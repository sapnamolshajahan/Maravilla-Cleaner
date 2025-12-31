# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockWarehouseBin(models.Model):
    """
        Bins in a warehouse containing Stock.
    """
    _name = "stock.warehouse.bin"
    _description = "Warehouse bins"

    ###########################################################################
    # Fields
    ###########################################################################

    name = fields.Char(string="Name", size=128, required=True,
                       help='Used as sequence indicator if many bins for same product')
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    product_template_id = fields.Many2one(comodel_name="product.template", string="Product",
                                          related="product_id.product_tmpl_id")
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Warehouse", required=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company",
                                 default=lambda obj: obj.env.user.company_id.id)
    min = fields.Float(string="Min", digits="Accounting")
    max = fields.Float(string="Max", digits="Accounting")

    _order = "warehouse_id, product_id, name"
    _unique_bin = models.Constraint("unique (product_id,warehouse_id,name)", "The warehouse product bin name must be unique")

    @api.model_create_multi
    def create(self, value_list):
        product_model = self.env['product.product']
        for v in value_list:
            if "product_id" not in v and "product_template_id" in v:
                product = product_model.search([("product_tmpl_id", "=", v["product_template_id"])], limit=1)
                v["product_id"] = product.id
        return super(StockWarehouseBin, self).create(value_list)
