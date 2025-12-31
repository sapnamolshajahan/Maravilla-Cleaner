# -*- coding: utf-8 -*-
import base64
import logging
from datetime import datetime
from decimal import Decimal
from io import BytesIO as cStringIO
from odoo import api, models, fields, SUPERUSER_ID

logger = logging.getLogger(__name__)


def chunk_list(big_list, chunk_size):
    """ Yield successive chunks from a list. """
    for i in range(0, len(big_list), chunk_size):
        yield big_list[i:i + chunk_size]


class ResPartnerStatement(models.TransientModel):
    _name = 'account.gst.report'
    _description = 'GST Report'

    ###########################################################################
    # Fields
    ###########################################################################
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')

    line_ids = fields.One2many(comodel_name="account.gst.report.lines",
                               inverse_name="account_gst_report_id",
                               string="Lines")

    account_ids = fields.Many2many(comodel_name="account.account",
                                   relation="account_gst_account_rel",
                                   string="Accounts", required=True,
                                   help="Select GST Accounts to be included.")

    output_type = fields.Selection(selection=[("xls", "Excel")],
                                   string="Output format", default="xls")

    detail = fields.Selection(selection=[("summary", "Summary"), ("detailed", "Detailed")],
                              string="Level of Detail",
                              help="Summary gives one line per invoice per GST type, detailed is at invoice line level",
                              default="summary")

    report_name = fields.Char(size=64,
                              string="Report Name",
                              readonly=True,
                              default="GST Report.xlsx")

    data = fields.Binary(string="Download File", readonly=True)

    ###########################################################################
    # Methods
    ###########################################################################
    @api.model
    def round_dp(self, value_to_round, number_of_decimals):
        if number_of_decimals and value_to_round:
            TWO_PLACES = Decimal(10) ** -number_of_decimals
            return float(Decimal(str(value_to_round)).quantize(TWO_PLACES))
        return False

    def create_report_line(self, date, invoice_number, reference, gst_type, account_tax_id, value_excl, gst,
                           value_incl, account_id, move_id, move_id_technical=None, partner_id=None):

        self.env['account.gst.report.lines'].create({
            'account_gst_report_id': self.id,
            'date': date,
            'invoice_number': invoice_number,
            'ref': reference,
            'gst_type': gst_type,
            'account_tax_id': account_tax_id,
            'value_excl': value_excl,
            'gst': gst,
            'value_incl': value_incl,
            'account_id': account_id,
            'move_id': move_id,
            'move_id_technical': move_id or move_id_technical,
            'partner_id': partner_id,
        })

    def process_zero_invoice(self, move, big_aml_done_list):
        invoice_line_ids = move.line_ids

        for line in invoice_line_ids:
            if line.id in big_aml_done_list:
                continue
            if line.display_type != 'product':
                continue
            if not (line.debit or line.credit):
                continue
            if line.tax_ids:
                account_tax_id = line.tax_ids[0].id
                gst_type = line.tax_ids[0].name
            else:
                account_tax_id = False
                gst_type = 'No Tax Code on Line'

            subtotal = line.debit - line.credit

            big_aml_done_list.append(line.id)

            self.create_report_line(
                date=move.invoice_date,
                invoice_number=move.name,
                reference=line.name,
                gst_type=gst_type,
                account_tax_id=account_tax_id,
                value_excl=subtotal,
                gst=0,
                value_incl=subtotal,
                account_id=False,
                move_id=False,
                move_id_technical=move.id,
                partner_id=move.partner_id and move.partner_id.id
            )
        return big_aml_done_list

    def process_invoice(self, aml, move_id, accounting_decimal_precision, big_aml_done_list):
        # the idea here is we do all the tax types that exist on this invoice in one function
        # aml are the GST account posted aml
        gst_to_process = sum([x.debit - x.credit for x in move_id.line_ids if x.account_id.id in
                                    [a.id for a in self.account_ids]])
        unique_tax_ids1 = list(set([x.tax_line_id for x in move_id.line_ids if x.tax_line_id]))
        unique_tax_ids2 = list(set([x.tax_ids[0] for x in move_id.line_ids if x.tax_ids]))
        unique_tax_ids = list(set(unique_tax_ids2 + unique_tax_ids1))
        # odoo does not store that tax for a line anywhere so we get the total tax for the move for this tax_id
        # and will then pro-rata across lines
        for tax_id in unique_tax_ids:
            account_ids = [x.account_id for x in tax_id.invoice_repartition_line_ids.filtered(lambda x: x.account_id)]
            gst_amount = sum([x.debit - x.credit for x in move_id.line_ids if x.account_id.id in [x.id for x in account_ids]
                              and x.tax_line_id.id == tax_id.id])
            gst_to_process -= gst_amount
            invoice_line_ids = move_id.line_ids.filtered(lambda x: x.tax_ids and x.tax_ids[0].id == tax_id.id)

            invoice_lines_amount = self.round_dp(
                sum([(x.debit - x.credit) for x in invoice_line_ids]),
                accounting_decimal_precision)

            number_of_lines = len(invoice_line_ids)
            lines_processed = tax_allocated = 0.0

            for line in invoice_line_ids:
                lines_processed += 1
                line_amount = (line.debit - line.credit)
                big_aml_done_list.append(line.id)

                if lines_processed == number_of_lines:  # if last line
                    tax_share = gst_amount - tax_allocated
                else:
                    if gst_amount and invoice_lines_amount:
                        logger.info('Move = {move} '.format(move=move_id))
                        tax_share = self.round_dp((line_amount / invoice_lines_amount * gst_amount), accounting_decimal_precision)
                    else:
                        tax_share = 0.0

                    tax_allocated += tax_share

                self.create_report_line(
                    date=move_id.invoice_date,
                    invoice_number=move_id.name,
                    reference=line.name,
                    gst_type=tax_id.name,
                    account_tax_id=tax_id.id,
                    value_excl=line_amount,
                    gst=tax_share,
                    value_incl=line_amount + tax_share,
                    account_id=line.account_id.id,
                    move_id=line.move_id.id,
                    partner_id=move_id.partner_id and move_id.partner_id.id
                )

        # this caters for an invoice being used to process a GST refund (go figure)
        # where the line is coded direct to the GST account and no tax code used
        invoice_line_ids = aml.move_id.line_ids.filtered(lambda x: x.account_id.id == aml.account_id.id and x.display_type == 'product'
                                                         and not x.tax_line_id)

        for line in invoice_line_ids:
            amount = (line.debit - line.credit)
            gst_to_process -= amount
            big_aml_done_list.append(line.id)
            self.create_report_line(
                date=move_id.invoice_date,
                invoice_number=move_id.name,
                reference=line.name,
                gst_type="Other Transactions",
                account_tax_id=False,
                value_excl=0,
                gst=amount,
                value_incl=amount,
                account_id=line.account_id.id,
                move_id=line.move_id.id,
                partner_id=move_id.partner_id and move_id.partner_id.id
            )
        if gst_to_process:
            self.create_report_line(
                date=move_id.invoice_date,
                invoice_number=move_id.name,
                reference=move_id.ref,
                gst_type="Other Transactions",
                account_tax_id=False,
                value_excl=0,
                gst=gst_to_process,
                value_incl=0.0,
                account_id=self.account_ids[0].id,
                move_id=line.move_id.id,
                partner_id=move_id.partner_id and move_id.partner_id.id
            )

        return big_aml_done_list

    def process_no_invoice(self, move, big_aml_done_list):
        move_id = self.env['account.move'].browse(move)
        aml_lines = move_id.line_ids

        # if all lines are GST lines this is just a transfer between GST accounts so can ignore
        not_gst_line = aml_lines.filtered(lambda x: x.account_id.id not in [x.id for x in self.account_ids])
        if not not_gst_line:
            return big_aml_done_list

        gst_dict = {}

        tax_base_amount = sum([x.tax_base_amount for x in aml_lines])
        if not tax_base_amount:
            # bank statement entries do not have tax_base_amount so need to work out here. Will assume only 1 GST line as no way of splitting
            logger.info('Move = {move} '.format(move=move_id))
            gst = sum([x.debit - x.credit for x in aml_lines if x.account_id.id in [z.id for z in self.account_ids]])
            first_gst_line = aml_lines.filtered(lambda x: x.account_id.id in [x.id for x in self.account_ids])
            value_excl = sum([x.debit - x.credit for x in aml_lines if x.account_id.id not in [z.id for z in self.account_ids]
                               and x.account_id.id != x.journal_id.default_account_id.id])
            value_incl = value_excl + gst
            for line in aml_lines:
                big_aml_done_list.append(line.id)
            self.create_report_line(
                date=move_id.date,
                invoice_number=move_id.name,
                reference=first_gst_line[0].name,
                gst_type=first_gst_line[0].tax_line_id.name,
                account_tax_id=first_gst_line[0].tax_line_id.id,
                value_excl=value_excl,
                gst=gst,
                value_incl=value_incl,
                account_id=first_gst_line[0].account_id.id,
                move_id=move_id.id,
                partner_id=move_id.partner_id and move_id.partner_id.id
            )

        else:
            for line in aml_lines:
                big_aml_done_list.append(line.id)
                if line.account_id in self.account_ids:
                    key_val = str(line.account_id.id) + '-' + str(line.tax_line_id.id if line.tax_line_id else 'No Tax')
                    if gst_dict.get(key_val, None):
                        gst_dict[key_val] += line
                    else:
                        gst_dict[key_val] = line

            for k, v in gst_dict.items():
                value_excl = value_incl = tax_base_amount = gst = 0.0
                for i in range(0, len(v)):
                    gst += v[i].debit - v[i].credit
                    if gst < 0:
                        value_excl += 0 - v[i].tax_base_amount
                        value_incl += 0 - v[i].tax_base_amount + v[i].debit - v[i].credit
                        tax_base_amount += 0 - v[i].tax_base_amount
                    else:
                        value_excl += v[i].tax_base_amount
                        value_incl += v[i].tax_base_amount + v[i].debit - v[i].credit
                        tax_base_amount += v[i].tax_base_amount

                    if v[i].tax_line_id:
                        tax_name = v[i].tax_line_id.name
                    else:
                        tax_name = 'Other Transactions'


                if v[0].ref:
                    ref = v[0].ref
                else:
                    ref = v[0].name

                self.create_report_line(
                    date=v[0].date,
                    invoice_number=v[0].name,
                    reference=ref,
                    gst_type=tax_name,
                    account_tax_id=v[0].tax_line_id.id if v[0].tax_line_id else False,
                    value_excl=value_excl,
                    gst=gst,
                    value_incl=value_incl,
                    account_id=v[0].account_id.id,
                    move_id=v[0].move_id.id,
                    partner_id=move_id.partner_id and move_id.partner_id.id
                )

        return big_aml_done_list

    def process_accounts(self):
        accounting_decimal_precision = self.env['decimal.precision'].precision_get('Accounting')
        processed_moves = []
        big_aml_done_list = []
        all_moves_to_process = []

        for account in self.account_ids:

            sql_string = """select move_id from account_move_line where account_id = {account}
                                    and date <= '{to_date}' and date >= '{from_date}' and parent_state = 'posted' 
                                    and company_id = '{company}'"""
            self.env.cr.execute(sql_string.format(
                account=account.id,
                to_date=self.to_date,
                from_date=self.from_date,
                company=self.env.company.id
            ))
            moves_to_process = self.env.cr.fetchall()

            moves_to_process = list(set([x[0] for x in moves_to_process]))
            all_moves_to_process.extend(moves_to_process)

            tot_recs = len(moves_to_process)
            up_to = 0
            aml_model = self.env['account.move.line']
            am_model = self.env['account.move']
            for chunk_ids in chunk_list(moves_to_process, 500):
                up_to += len(chunk_ids)
                logger.info('Records Moves Processed = {up_to} of {tot_recs}'.format(up_to=up_to, tot_recs=tot_recs))
                for move in am_model.browse(chunk_ids):

                    # initially look at the lines for this move to see if it relates to an invoice
                    # and process based on the invoice

                    move_lines = [x for x in move.line_ids if x.account_id.id == account.id]
                    # these move lines could have multiple tax rates posted to the same GST account

                    if move_lines and move.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']:
                        big_aml_done_list = self.process_invoice(move_lines[0], move, accounting_decimal_precision, big_aml_done_list)
                        processed_moves.append(move.id)

                aml_model._invalidate_cache()

        # now handle transactions not linked to an invoice
        # we pass the move and handle all the lines in the move as a set
        moves_without_invoice_id = set(all_moves_to_process) - set(processed_moves)

        # first handle transactions from bank statement processing

        for move in moves_without_invoice_id:
            big_aml_done_list = self.process_no_invoice(move, big_aml_done_list)
            processed_moves.append(move)

        # cater for any invoices with no GST as these will not have any entry in the GST accounts and therefore not
        # be selected

        zero_gst_invoices = self.env['account.move'].search([
            ('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
            ('id', 'not in', processed_moves),
            ('state', '=', 'posted')
        ])

        for move in zero_gst_invoices:
            big_aml_done_list = self.process_zero_invoice(move, big_aml_done_list)

        # now handle any mixed invoices - ie some lines have GST but some lines do not

        exempt_zero_codes = self.env['account.tax'].search([('amount','=', 0.0)])
        all_possible_moves = self.env['account.move'].search([('date', '>=', self.from_date),
            ('date', '<=', self.to_date),('state', '=', 'posted'),('company_id','=',self.env.company.id)])
        for move in all_possible_moves:
            lines_to_include = []
            for line in move.line_ids:
                if line.id in big_aml_done_list:
                    continue
                if line.tax_ids:
                    for tax in line.tax_ids:
                        if tax in exempt_zero_codes:
                            lines_to_include.extend(line)
            if lines_to_include:
                for line in lines_to_include:
                    if line.id in big_aml_done_list:
                        continue
                    big_aml_done_list.append(line.id)

                    self.env['account.gst.report.lines'].create({
                        'account_gst_report_id': self.id,
                        'date': line.move_id.date,
                        'invoice_number': line.move_id.name,
                        'ref': line.move_id.ref,
                        'gst_type': line.tax_ids[0].name,
                        'account_tax_id': line.tax_ids[0].id,
                        'value_excl': line.debit - line.credit,
                        'gst': 0,
                        'value_incl': line.debit - line.credit,
                        'account_id': line.tax_ids[0].invoice_repartition_line_ids[0].account_id.id,
                        'move_id': line.move_id.id
                    })

        # now a sanity check in case any lines without a GST code or zero gst lines with no GL entry posted to GST account

        all_possible_aml = self.env['account.move.line'].search([
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
            ('parent_state', '=', 'posted'),
            ('id', 'not in', big_aml_done_list),
            ('display_type', '=', 'product')
        ])
        for aml in all_possible_aml:
            self.env['account.gst.report.lines'].create({
                'account_gst_report_id': self.id,
                'date': aml.move_id.date,
                'invoice_number': aml.move_id.name,
                'ref': aml.move_id.ref,
                'gst_type': aml.tax_ids[0].name if aml.tax_ids else 'Other Transactions',
                'account_tax_id': aml.tax_ids[0].id if aml.tax_ids else False,
                'value_excl': aml.debit - aml.credit,
                'gst': 0,
                'value_incl': aml.debit - aml.credit,
                'account_id': aml.tax_ids[0].invoice_repartition_line_ids[0].account_id.id if aml.tax_ids else False ,
                'move_id': aml.move_id.id
            })

        # reverse all the signage here as simpler to do once
        for line in self.line_ids:
            line.write({
                'value_excl': line.value_excl * -1,
                'gst': line.gst * -1,
                'value_incl': line.value_incl * -1.

            })

    def _do_report(self, report_type):
        """
       Creates the underlying report data into the transient model below
       and then calls the required report
        """
        start_time = datetime.now()
        self.process_accounts()

        result = self.env[report_type].run_report(self)
        logger.debug("check_report completed - elapsed = {elapsed} seconds".format(
            elapsed=(datetime.now() - start_time).seconds)
        )
        return result

    def run_report(self, wizard):
        self.env.cr.commit()  # forced commit to allow Viaduct to view records
        res, rpt_format = self.render_report(wizard.ids, self.report_name, {})
        return self.report_name, "{0}.{1}".format(self.report_name, rpt_format), "GST Report", cStringIO.StringIO(res)

    def run_in_foreground(self, report_type):
        result = None

        for rec in self:
            result = rec._do_report(report_type)
        if not result:
            return {"type": "ir.actions.act_window_close"}

        _, file_name, _, data = result
        data.seek(0)
        output = base64.encodebytes(data.read())

        self.write({
            "data": output,
            "report_name": file_name,
        })

        view = self.env.ref("account_gst.account_gst_report_download_view")
        view = view.with_user(SUPERUSER_ID)  # To prevent security errors for accountant users only

        return {
            "name": view.name,
            "type": "ir.actions.act_window",
            "res_model": "account.gst.report",
            "view_mode": "form",
            "view_id": view.id,
            "res_id": self.id,
            "target": "new",
        }

    def print_report(self):

        report_type = "account.gst.xls.report"
        return self.run_in_foreground(report_type)


class AccountGSTReportLine(models.TransientModel):
    _name = 'account.gst.report.lines'
    _description = 'GST report Lines'

    ###########################################################################
    # Fields
    ###########################################################################

    account_gst_report_id = fields.Many2one(comodel_name="account.gst.report", string="GST Report")
    date = fields.Date(string="Date")
    invoice_number = fields.Char(string="Invoice Number", size=64)
    ref = fields.Char(string="Ref", size=64)
    gst_type = fields.Char(string="GST Type", size=50)
    account_tax_id = fields.Many2one("account.tax", string="Tax ID")
    value_excl = fields.Float(string="Excl GST", digits=("Account"))
    gst = fields.Float(string="GST", digits=("Account"))
    value_incl = fields.Float(string="Incl GST", digits=("Account"))
    account_id = fields.Many2one(comodel_name='account.account', string='Account')
    move_id = fields.Many2one(comodel_name='account.move', string='Move')
    move_id_technical = fields.Integer(string='Move ID (Technical)')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
