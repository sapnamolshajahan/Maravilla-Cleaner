from odoo import api, fields, models


class GSSDangerousGoodsPresets(models.Model):
    _name = 'gss.dangerous.goods.preset'
    _description = 'Presets for Dangerous Goods Items'
    _rec_name = 'shipping_name'

    ########################################################################################
    # Default & Compute methods
    ########################################################################################

    ########################################################################################
    # Fields
    ########################################################################################
    shipping_name = fields.Char(string='Proper Shipping Name')
    un_or_id = fields.Char(string='UN or ID No')
    shipping_class = fields.Char(string='Class')
    packing_group = fields.Char(string='Packing Group')
    subsidiary_risk = fields.Char(string='Subsidiary Risk')
    packing_qty_type = fields.Char(string='Quantity and Type of Packing')
    packing_instructions = fields.Char(string='Packing Inst')
    authorization = fields.Char(string='Authorization', default='Storeperson')

    ########################################################################################
    # Methods
    ########################################################################################
