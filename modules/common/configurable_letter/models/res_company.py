# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class Company(models.Model):
    _inherit = 'res.company'

    configurable_letter_footer_text = fields.Text(string='Footer text for configurable letters')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    configurable_letter_footer_text = fields.Text(string='Footer text for configurable letters')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        configurable_letter_footer_text = self.env.company.configurable_letter_footer_text

        if configurable_letter_footer_text:
            res['configurable_letter_footer_text'] = configurable_letter_footer_text

        return res

    def set_values(self):
        self.env.company.write({'configurable_letter_footer_text': self.configurable_letter_footer_text})
        return super(ResConfigSettings, self).set_values()
