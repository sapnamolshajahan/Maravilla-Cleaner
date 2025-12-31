# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DangerousGoods(models.Model):
    _name = "picking.dangerous.goods"
    _description = "PickingDangerous Goods Items"

    ########################################################################################
    # Default and compute methods
    ########################################################################################

    ########################################################################################
    # Fields
    ########################################################################################
    dangerous_goods_preset_item = fields.Many2one(
        string='DG Preset', comodel_name='gss.dangerous.goods.preset')

    picking_id = fields.Many2one(string='Picking', comodel_name='stock.picking', ondelete='cascade')
    un_or_id = fields.Char(string='UN or ID No')
    shipping_name = fields.Char(string='Proper Shipping Name')
    shipping_class = fields.Char(string='Class')
    packing_group = fields.Char(string='Packing Group')
    subsidiary_risk = fields.Char(string='Subsidiary Risk')
    packing_qty_type = fields.Char(string='Qty and Type of Packing')
    packing_instructions = fields.Char(string='Packing Inst')
    authorization = fields.Char(string='Authorization', default='Storeperson')
    ########################################################################################
    # Model methods
    ########################################################################################
