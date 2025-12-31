# -*- encoding: utf-8 -*-
from odoo import fields, models

class Company(models.Model):
    _inherit = "res.company"

    purchase_incoterm = fields.Many2one("account.incoterms", string="Default Purchase Incoterms")
    hide_drop_ship_fields = fields.Boolean(string="Hide Drop Ship on Purchase Order")
    hide_alt_address_fields = fields.Boolean(string="Hide Alt. Shipment Addr. on Purchase Order")
    hide_delivery_notes_fields = fields.Boolean(string="Hide Delivery Notes on Purchase Order")
    purchase_set_counts_zero = fields.Boolean(string='Override Purchase Counts on Partner Form')
    purchase_company_only = fields.Boolean(string='Set Company Domain on Purchase Orders')


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    purchase_incoterm = fields.Many2one("account.incoterms", string="Default Purchase Incoterms",
                                        default=lambda self: self.env.company.purchase_incoterm)
    hide_drop_ship_fields = fields.Boolean(string="Hide Drop Ship on Purchase Order", default=lambda self: self.env.company.hide_drop_ship_fields)
    hide_alt_address_fields = fields.Boolean(string="Hide Alt. Shipment Addr. on Purchase Order",
                                             default=lambda self: self.env.company.hide_alt_address_fields)
    hide_delivery_notes_fields = fields.Boolean(string="Hide Delivery Notes on Purchase Order",
                                                default=lambda self: self.env.company.hide_delivery_notes_fields)
    purchase_set_counts_zero = fields.Boolean(string='Override Purchase Counts on Partner Form',
                                              default=lambda self: self.env.company.purchase_set_counts_zero)
    purchase_company_only = fields.Boolean(string='Set Company Domain on Purchase Orders',
                                           default=lambda self: self.env.company.purchase_company_only)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "purchase_incoterm": self.purchase_incoterm.id,
                "hide_drop_ship_fields": self.hide_drop_ship_fields,
                "hide_alt_address_fields": self.hide_alt_address_fields,
                "hide_delivery_notes_fields": self.hide_delivery_notes_fields,
                "purchase_set_counts_zero": self.purchase_set_counts_zero,
            }
        )



