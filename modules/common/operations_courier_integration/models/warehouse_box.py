# -*- coding: utf-8 -*-
from odoo import fields, models, api


class StockWarehouseBox(models.Model):

    _name = "stock.warehouse.box"
    _description = "Parcel Box/Packaging"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    ###########################################################################
    # Fields
    ###########################################################################

    name = fields.Char("Name/Code", required=True)
    width = fields.Float("Width(cm)", required=True, digits=(3, 2))
    height = fields.Float("Height(cm)", required=True, digits=(3, 2))
    length = fields.Float("Length(cm)", required=True, digits=(3, 2))
    default_kgs = fields.Float(string="Default Weight (kgs)", required=True, default=1.0, digits=(5, 2))
    active = fields.Boolean("Active", default=True)
    type = fields.Char("Type", help="Box, Carton, Satchel, Bag, Pallet, etc")
    hire_type_account = fields.Char("Hire Type Account Number")
    hire_company = fields.Selection([("C", "CHEP"), ("L", "Loscam")], "Hire Company")
    hire_type = fields.Selection([("R", "Retrieval"), ("T", "Transfer")], "Hire Type")
    equipment_type = fields.Selection([("P", "Pallet"), ("NOTRANSFER", "No Transfer")], "Equipment Type")
    is_pallet = fields.Boolean("Is Pallet?")

    ###########################################################################
    # Model's methods
    ###########################################################################

    @api.depends('name', 'height', 'width', 'length')
    def _compute_display_name(self):
        for record in self:
            if record.name and record.height and record.width and record.length:
                dimensions = f"{record.height}x{record.width}x{record.length}"
                record.display_name = f"{record.name}({dimensions})"
            else:
                record.display_name = ""
