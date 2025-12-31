# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class ResCompany(models.Model):
    _inherit = "res.company"

    sleep_time = fields.Float(string='Sleep Time')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sleep_time = fields.Float(string='Sleep Time', default=lambda self: self.env.company.sleep_time)

    def set_values(self):

        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "sleep_time": self.sleep_time,
            }
        )
