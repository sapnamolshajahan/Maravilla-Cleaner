# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SaleLineViewCompany(models.Model):
    _inherit = "res.company"

    sale_line_low_price_warning = fields.Boolean("Show low price warnings")
    sale_line_low_stock_warning = fields.Boolean("Show low stock warnings")
    sale_line_exclude_in_avail_stock = fields.Boolean("Avail Stock all except excluded")
    sale_set_counts_zero = fields.Boolean(string='Override Counts on Partner Form')
    sale_company_only = fields.Boolean(string='Set Company Domain on Sale Orders')
    advance_invoice_rule = fields.Boolean(string='Advance Invoice Ordered Quantity', default=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_line_low_price_warning = fields.Boolean("Show low price warnings", default=lambda self: self.env.company.sale_line_low_price_warning)
    sale_line_low_stock_warning = fields.Boolean("Show low stock warnings", default=lambda self: self.env.company.sale_line_low_stock_warning)
    sale_line_exclude_in_avail_stock = fields.Boolean("Calculate available stock on sale order lines",
                                                      default=lambda self: self.env.company.sale_line_exclude_in_avail_stock)
    sale_set_counts_zero = fields.Boolean(string='Override Counts on Partner Form', default=lambda self: self.env.company.sale_set_counts_zero)
    sale_company_only = fields.Boolean(string='Set Company Domain on Sale Orders', default=lambda self: self.env.company.sale_company_only)
    advance_invoice_rule = fields.Boolean(string='Advance Invoice Ordered Quantity',
                                          default=lambda self: self.env.company.advance_invoice_rule)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "sale_line_low_price_warning": self.sale_line_low_price_warning,
                "sale_line_low_stock_warning": self.sale_line_low_stock_warning,
                "sale_line_exclude_in_avail_stock": self.sale_line_exclude_in_avail_stock,
                "sale_set_counts_zero": self.sale_set_counts_zero,
                "sale_company_only": self.sale_company_only,
                "advance_invoice_rule": self.advance_invoice_rule,

            }
        )
