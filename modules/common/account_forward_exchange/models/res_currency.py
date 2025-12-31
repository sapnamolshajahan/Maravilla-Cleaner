from odoo import models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def _get_rates(self, company, date):
        rate_info = self.env.context.get('account_forward_exchange__force_rate', {})
        res = super(ResCurrency, self)._get_rates(company, date)
        if rate_info:
            currency_id = rate_info.get('currency_id')
            rate = rate_info.get('rate')
            if currency_id in res:
                res[currency_id] = rate

        return res
