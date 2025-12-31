# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    include_invoiced = fields.Boolean("Include Invoiced")
    include_confirmed_orders = fields.Boolean("Include Confirmed Orders")
    include_quote_orders = fields.Boolean("Include Quoted Orders")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    include_invoiced = fields.Boolean(
        "Include Invoiced",
        default=lambda self: self.env.company.include_invoiced,
        help="Target actuals includes invoiced values.",
    )

    include_confirmed_orders = fields.Boolean(
        "Include Confirmed Orders",
        default=lambda self: self.env.company.include_confirmed_orders,
        help="Target actuals includes confirmed sale orders.",
    )

    include_quote_orders = fields.Boolean(
        "Include Quoted Orders",
        default=lambda self: self.env.company.include_quote_orders,
        help="Target actuals includes quoted sale orders.",
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "include_invoiced": self.include_invoiced,
                "include_confirmed_orders": self.include_confirmed_orders,
                "include_quote_orders": self.include_quote_orders,
            }
        )
