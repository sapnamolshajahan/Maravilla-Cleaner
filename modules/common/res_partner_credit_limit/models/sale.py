# -*- coding:utf-8 -*-
from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        for sale in self:
            sale.check_credit_limit()
        return super(SaleOrder, self).action_confirm()

    def check_credit_limit(self):
        if self.env.context.get("skip_credit_check"):
            return
        if self.partner_id.over_credit:
            return

        if self.partner_id.warning_type and self.partner_id.warning_type != "none":
            if self.partner_id.warning_type == "blocked":
                raise UserError(_("Can not confirm the order because this customer is credit blocked."))

            if self.partner_id.warning_type in ("value", "all"):
                available_credit = self.partner_id.calculate_remaining_credit()
                if self.amount_total > available_credit:
                    raise UserError(
                        f"Cannot confirm order because customer '{self.partner_id.name}' does not have enough credit.\n"
                        f"Available credit is {available_credit:0.2f}")
