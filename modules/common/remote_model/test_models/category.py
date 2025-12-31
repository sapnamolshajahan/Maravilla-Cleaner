# -*- coding: utf-8 -*-
from odoo import fields
from .. import models

"""
The models in this file require a configuration section similar to the following:

[remote_model]
incoming_secret_key = 1702b75a-595e-11ec-adf8-1831bfb5097f
outgoing_remote_url = http://localhost:8069
outgoing_remote_dbname = waterforce
outgoing_secret_key = 1702b75a-595e-11ec-adf8-1831bfb5097f
"""


class ProductCategory(models.RemoteModel):
    """
    Local loopback test
    """
    _name = "localhost.product.category"
    _remote_name = "product.category"

    ###########################################################################
    # Fields
    ###########################################################################
    name = fields.Char("Name", index=True, required=True)
    complete_name = fields.Char("Complete Name")
    parent_id = fields.Many2one("localhost.product.category", "Parent Category")
    child_id = fields.One2many("localhost.product.category", "parent_id", "Child Categories")
