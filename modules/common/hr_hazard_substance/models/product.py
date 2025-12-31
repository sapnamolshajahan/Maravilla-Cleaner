# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

SUBSTANCE_STATES = [
    ("solid", "Solid"),
    ("liquid", "Liquid"),
    ("gas", "Gas")]


class StockWarehouseBin(models.Model):
    _name = 'stock.warehouse.bin'
    """
    Used in operations_multibin - added here to avoid dependency issues. At some point, this module
    will be incremented to use standard Odoo bin locations
    """

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

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _compute_location(self):
        for prod in self:
            if hasattr(prod, 'bin_ids'):
                if prod.product_variant_ids and prod.product_variant_ids[0].bin_ids:
                    prod.hazard_location = prod.product_variant_ids[0].bin_ids[0]
                    prod.hazard_max_qty = prod.product_variant_ids[0].hazard_location.max or 0
                    continue
            prod.hazard_location = None
            prod.hazard_max_qty = 0

    hazard_substance = fields.Boolean("Hazardous Substance")
    hazard_approval_nr = fields.Text("Approval number and group standard name")
    hazard_classifications = fields.Text("Hazard classifications")
    hazard_sds_issuing_date = fields.Date("SDS issuing date")
    hazard_storage_reqs = fields.Text("Specific storage and segregation requirements")
    hazard_material_state = fields.Selection(SUBSTANCE_STATES, "Substance state")
    hazard_ppe_notes = fields.Text("PPE & Notes")
    hazard_location = fields.Many2one("stock.warehouse.bin", "Location", compute="_compute_location")
    hazard_max_qty = fields.Float("Max likely qty", compute="_compute_location")
    hazard_document_1 = fields.Binary("Document 1", attachment=False)
    hazard_document_1_filename = fields.Char("Document 1 Filename")
    hazard_document_2 = fields.Binary("Document 2", attachment=False)
    hazard_document_2_filename = fields.Char("Document 2 Filename")
    hazard_document_3 = fields.Binary("Document 3", attachment=False)
    hazard_document_3_filename = fields.Char("Document 3 Filename")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_location(self):
        for prod in self:
            if hasattr(prod, 'bin_ids'):
                if prod.product_variant_ids and prod.product_variant_ids[0].bin_ids:
                    prod.hazard_location = prod.product_variant_ids[0].bin_ids[0]
                    prod.hazard_max_qty = prod.product_variant_ids[0].hazard_location.max or 0
                    continue
            prod.hazard_location = None
            prod.hazard_max_qty = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('product_tmpl_id', None):
                product_template = self.env['product.template'].browse(vals['product_tmpl_id'])
                if product_template.hazard_substance and product_template.product_variant_ids:
                    raise UserError('Do not use variants for hazardous items - create a new product for each')

        return super(ProductProduct, self).create(vals_list)


class Product(models.Model):
    """
        Product with bin locations.
    """
    _inherit = "product.product"
    bin_ids = fields.One2many(comodel_name="stock.warehouse.bin", inverse_name="product_id", string="Bins")


class ProductTemplates(models.Model):
    """
        Product with bin locations.
    """
    _inherit = "product.template"
    bin_ids = fields.One2many(comodel_name="stock.warehouse.bin", inverse_name="product_template_id", string="Bins")
