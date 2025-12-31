# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ApiIrModelFields(models.Model):
    """Enable custom names for fields in the API"""
    _inherit = "ir.model.fields"

    api_name = fields.Char(string="API name",
                           help="Custom name for the field when returned in the REST API")

    post_ref = fields.Char(string="POST/PUT reference",
                           default='id',
                           help="On POST/PUT calls, if you need to pass a Many2one field not but its ID "
                                "(but, for example, its reference), "
                                "specify Odoo field label here")

    def button_add_mapping_name(self):
        wizard = self.env['add.api.mapping.name.wizard'].create({'odoo_field': self.id})

        return {
            'name': _('Add API Mapping Name'),
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.api.mapping.name.wizard',
            'res_id': wizard.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def button_add_post_ref(self):
        wizard = self.env['add.api.post.ref.wizard'].create({'odoo_field': self.id})

        return {
            'name': _('Add API POST Name'),
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.api.post.ref.wizard',
            'res_id': wizard.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
