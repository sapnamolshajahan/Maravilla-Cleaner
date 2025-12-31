from odoo import models, fields, api
from odoo.tools import SQL


class ResPartner(models.Model):
    _inherit = 'res.company'

    @api.model
    def _operations_timezones(self):
        zones = []
        for tz in pytz.all_timezones:
            zones.append((tz, tz))
        return zones

    operations_timezone = fields.Selection("_operations_timezones", string="Operations Timezone",
                                           default="Pacific/Auckland", required=True,
                                           help="Company's Standard Timezone")


    max_writeoff = fields.Integer(string='Maximum Write-Off')
    write_off_journal = fields.Many2one(comodel_name='account.journal', string='Write Off Journal')



    @api.model
    def install_reconcile_history(self):
        """
        since this module introduces new as at fields to manage the timing around reconciliation
        we need to try and clear all the historical data.
        But the inventory account is missing links back to stock moves
        so this uses the quantity received or dispatched by day.
        Will use queue job (OCA Module) to create the entries so avoids memory issues
        """
        categories = self.env['product.category'].search([])
        accounts = list(set([x.property_stock_valuation_account_id.id for x in categories]))
        for account in accounts:
            query = SQL(
                """
                SELECT id from account_move_line where account_id = %(account_id)s 
                and parent_state = 'posted'  
                """,
                account_id=account,
            )
            self.env.cr.execute(query)
            account_move_lines = [r[0] for r in self.env.cr.fetchall()]
            record_count = len(account_move_lines)
            cycle_count = int(record_count / 5000) + 1
            for i in range(0, cycle_count):
                start = i*5000
                stop = (i+1)*5000
                aml = account_move_lines[start:stop]

                self.with_delay(
                    channel=self.light_job_channel(),
                    description="Process Historical Reconciliation"
                ).process_aml_lines(
                    aml=aml,
                    account=account
                )

        return True

    def process_aml_lines(self, aml, account):

        lines = self.env['account.move.line'].browse(aml)
        current_date = False
        for line in lines:
            if line.immediate_reconciled_date:
                continue
            if line.date == current_date:
                continue
            lines_for_day = self.env['account.move.line'].search([
                ('account_id', '=', account),
                ('date', '=', line.date),
                ('parent_state', '=', 'posted')
            ])
            aml_qty = sum([x.quantity for x in lines_for_day])
            stock_moves = self.env['stock.move'].search([('move_date', '=', line.date),
                                                         ('state', '=', 'done')])
            move_qty = 0.0
            for move in stock_moves:
                if move.location_dest_id.usage == 'internal' and move.location_id.usage != 'internal':
                    move_qty += move.product_uom_qty
                elif move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
                    move_qty -= move.product_uom_qty

            if abs(aml_qty - move_qty) < abs(aml_qty * .05):
                lines_for_day.write({'immediate_reconciled_date': line.date})
                stock_moves.write({'immediate_reconciled_date': line.date})

            current_date = line.date



