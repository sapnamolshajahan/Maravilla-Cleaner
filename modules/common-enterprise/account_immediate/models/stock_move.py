from odoo import api, fields, models
import pytz


class StockMove(models.Model):
    _inherit = 'stock.move'

    immediate_reconciled_date = fields.Date()
    move_date = fields.Date(string='Move Date', compute='_set_move_date', store=True)

    @api.depends('date')
    def _set_move_date(self):
        """ Convert the date in datetime to a date.
        """
        tz = self.env.company.operations_timezone
        local_tz = pytz.timezone(tz)
        for record in self:
            if not record.date:
                record.move_date = False
            local_datetime = record.date.astimezone(local_tz)
            record.move_date = local_datetime.date()


