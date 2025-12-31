from odoo import fields, models, api
import pytz


class ProductValue(models.Model):
    _inherit = 'product.value'

    immediate_reconciled_date = fields.Date('Immediate Reconciled Date')
    accounting_date = fields.Date('Accounting Date')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductValue, self).create(vals_list)
        user_tz = self.env.tz
        if not user_tz:
            user_tz = timezone(self.company_id.resource_calendar_id.tz or 'UTC')

        for record in res:
            accounting_time = pytz.utc.localize(record.date).astimezone(user_tz)
            record.write({'accounting_date': accounting_time.date()})

        return res

