# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AddApiPostName(models.TransientModel):
    _name = 'add.api.post.ref.wizard'
    _description = 'Add POST ref for POSTing'

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
        
    ###########################################################################
    # Fields
    ###########################################################################
    odoo_field = fields.Many2one(string='Field', comodel_name='ir.model.fields', readonly=True)
    new_post_label = fields.Char(string='New POST Name')

    ###########################################################################
    # Model methods
    ###########################################################################
    def button_add_post_name(self):

        self.env.cr.execute(
            """
            UPDATE ir_model_fields
            SET post_ref = '%s'
            WHERE id = %d""" % (self.new_post_label, self.odoo_field.id)
        )
