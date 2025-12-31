# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_hide_alt_po_address = fields.Boolean(string='Show Alt Delivery Address by Default on PO',
                                              default=lambda self: self.env.company.show_hide_alt_po_address,
                                              readonly=False
                                              )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "show_hide_alt_po_address": self.show_hide_alt_po_address,

            }
        )
