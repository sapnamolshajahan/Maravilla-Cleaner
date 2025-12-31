# -*- coding: utf-8 -*-
from odoo import fields, models,api


class ResCompany(models.Model):
    _inherit = "res.company"

    auto_background_sale_threshold = fields.Integer(string="Sale Auto Background Processing Threshold",default=0)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_background_sale_threshold = fields.Integer(
        string="Sale Auto Background Processing Threshold",
        default=0,
        help="Number of sale lines before a sale order is automatically processed in the background.")


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        auto_background_sale_threshold = self.env.company.auto_background_sale_threshold
        if auto_background_sale_threshold:
            res['auto_background_sale_threshold'] = auto_background_sale_threshold
        return res

    def set_values(self):
        self.env.company.write({
            'auto_background_sale_threshold': self.auto_background_sale_threshold,
        })
        return super(ResConfigSettings, self).set_values()
