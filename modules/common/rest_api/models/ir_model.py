# -*- coding: utf-8 -*-
from odoo import fields, models


class ApiIrModel(models.Model):
    """Enable all models to be available for API request."""
    _inherit = "ir.model"

    allow_rest_api = fields.Boolean(string="REST API",
                                    help="Allow this model to be fetched through REST API")

    api_fields = fields.Many2many(
        'ir.model.fields', 'ir_model_ir_model_fields_rel', 'ir_model_id', 'ir_model_fields_id',
        string='Fields available in API',
        help='Select fields you want to be available in the API')

    delete_domain = fields.Char(string='Delete Domain',
                                help='Specify domain if required for cases when a record CAN be deleted in the API\n'
                                     'For example, sale orders can be deleted only in the draft state: '
                                     '[("state", "=", "draft")]')

    include_computed_fields = fields.Char(string='Include Computed Fields',
                                          help='Computed fields required for GET response must be listed here.'
                                               'Use comma "," to separate different fields')

    include_fields_in_post_response = fields.Char(string='Include IDs in POST response',
                                                  help='Fields whose IDs required for POST response must be listed here'
                                                       'Use comma "," to separate different fields')
