# -*- coding: utf-8 -*-
from odoo import fields, models,api


class ResCompanyReportExtension(models.Model):

    _inherit = "res.company"

    cbs_message = fields.Char(string="Message For Credit Balance Statement")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cbs_message = fields.Char(string="Message For Credit Balance Statement")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        cbs_message = self.env.company.cbs_message
        if cbs_message:
            res['cbs_message'] = cbs_message
        return res

    def set_values(self):
        super().set_values()
        self.env.company.write(
            {
                "cbs_message": self.cbs_message,
            }
        )
