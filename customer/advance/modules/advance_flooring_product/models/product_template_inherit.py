from odoo import models, fields, api
from odoo.osv import expression


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    colour_id = fields.Many2one(
        'product.colour',
        string='Colour'
    )
    product_group_id = fields.Many2one(
        'product.group',
        string='Product Group'
    )
    size_id = fields.Many2one(
        'product.size',
        string='Size'
    )
    category_id = fields.Many2one(
        'product.category',
        string='Category'
    )
    quotation_description = fields.Text(
        string="Quotation Description",
        translate=True,
        compute="_compute_quotation_description",
        inverse="_inverse_quotation_description",
        store=True,
        help="A description of the product to communicate to customers. "
             "It will be copied to Sales Orders, Delivery Orders, and Invoices."
    )

    @api.depends('description_sale')
    def _compute_quotation_description(self):
        for rec in self:
            rec.quotation_description = rec.description_sale

    def _inverse_quotation_description(self):
        for rec in self:
            rec.description_sale = rec.quotation_description

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        domain = domain or []
        results = super().name_search(name, domain, operator, limit)

        if not results and name:
            search_domain = expression.OR([
                domain,
                [('description_sale', operator, name)]
            ])
            products = self.search(search_domain, limit=limit)
            if products:
                return [(p.id, p.display_name) for p in products]
        return results

