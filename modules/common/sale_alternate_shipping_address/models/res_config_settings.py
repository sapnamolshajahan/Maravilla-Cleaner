# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_hide_alt_so_address = fields.Boolean(
        related="company_id.show_hide_alt_so_address",
        string="Show Alt Delivery Address by Default",
        help="Show Alt Delivery Address by Default",
        readonly=False,
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "show_hide_alt_so_address": self.show_hide_alt_so_address,
            }
        )

