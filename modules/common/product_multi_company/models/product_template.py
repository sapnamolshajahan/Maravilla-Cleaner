# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'By Quantity')],
        string="Tracking", required=True, default='none',
        compute='_compute_tracking', store=True, readonly=False, precompute=True,
        help="Ensure the traceability of a storable product in your warehouse.", company_dependent=True)

    list_price = fields.Float(
        'Sales Price', default=1.0, company_dependent=True,
        digits='Product Price', tracking=True,
        help="Price at which the product is sold to customers.")

    @api.depends('is_storable')
    def _compute_tracking(self):
        super()._compute_tracking()

    @api.depends('list_price')
    def _compute_currency_id(self):
        """
        Override to use have the default as the current company rather than the main/first company.
        """
        company_id = self.env.context.get("force_company") or self.env.company.id
        company = self.env["res.company"].browse(company_id)
        for template in self:
            template.currency_id = template.company_id.sudo().currency_id or company.currency_id

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # price_extra: catalog extra value only, sum of variant extra attributes
    price_extra = fields.Float(
        'Variant Price Extra', compute='_compute_product_price_extra', company_dependent=True,
        digits='Product Price',
        help="This is the sum of the extra price of all attributes")

    @api.depends('list_price', 'price_extra')
    @api.depends_context('uom', 'company')
    def _compute_product_lst_price(self):
        super()._compute_product_lst_price()


class ProductCategory(models.Model):
    _inherit = 'product.category'

    company_id = fields.Many2one('res.company', 'Company', index=1)



