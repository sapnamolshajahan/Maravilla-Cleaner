# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ################################################################################
    # Fields
    ################################################################################
    unconfirmed_edi_notify_email = fields.Char("Email address to receive notifications of unconfirmed EDI documents")
    unconfirmed_edi_period = fields.Integer("Number of hours before unconfirmed notification email is sent", default=8)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ################################################################################
    # Fields
    ################################################################################
    unconfirmed_edi_notify_email = fields.Char("Email address to receive notifications of unconfirmed EDI documents",
                                               default=lambda self: self.env.company.unconfirmed_edi_notify_email)
    unconfirmed_edi_period = fields.Integer("Number of hours before unconfirmed notification email is sent",
                                            default=lambda self: self.env.company.unconfirmed_edi_period)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "unconfirmed_edi_notify_email": self.unconfirmed_edi_notify_email,
                "unconfirmed_edi_period": self.unconfirmed_edi_period,
            })

    @api.onchange("group_product_variant")
    def _onchange_group_product_variant(self):
        """
        Override sale/.../res_config_settings:

        The product Configurator requires the product variants activated.
        If the user disables the product variants -> Don't disable the product configurator
        """
        if self.module_sale_product_matrix and not self.group_product_variant:
            self.module_sale_product_matrix = True
