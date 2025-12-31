# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    exclude_internal = fields.Boolean(string='Exclude Internal Followers')
    exclude_external = fields.Boolean(string='Exclude External Followers')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    exclude_internal = fields.Boolean(string='Exclude Internal Followers')
    exclude_external = fields.Boolean(string='Exclude External Followers')


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        exclude_internal = self.env.company.exclude_internal
        exclude_external = self.env.company.exclude_external

        if exclude_internal:
            res['exclude_internal'] = exclude_internal

        if exclude_external:
            res['exclude_external'] = exclude_external


        return res

    def set_values(self):
        self.env.company.write({
            'exclude_internal': self.exclude_internal,
            'exclude_external': self.exclude_external,
        })
        return super(ResConfigSettings, self).set_values()
