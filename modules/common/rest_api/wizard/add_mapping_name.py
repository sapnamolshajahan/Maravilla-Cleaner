# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AddApiMappingName(models.TransientModel):
    _name = 'add.api.mapping.name.wizard'
    _description = 'Add mapping name for a field'

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
        
    ###########################################################################
    # Fields
    ###########################################################################
    odoo_field = fields.Many2one(string='Field', comodel_name='ir.model.fields', readonly=True)
    odoo_field_name = fields.Char(string='Odoo Field Name', related='odoo_field.name')
    odoo_field_api_name = fields.Char(string='Existing API Name', related='odoo_field.api_name')
    api_name = fields.Char(string='API Name')

    ###########################################################################
    # Model methods
    ###########################################################################
    def button_add_mapping_name(self):

        self.env.cr.execute(
            """
            UPDATE ir_model_fields
            SET api_name = '%s'
            WHERE id = %d""" % (self.api_name, self.odoo_field.id)
        )
