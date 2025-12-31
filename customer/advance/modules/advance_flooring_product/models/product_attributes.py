from odoo import models, fields


class ProductColour(models.Model):
    _name = 'product.colour'
    _description = 'Product Colour'

    name = fields.Char(required=True)


class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'Product Group'

    name = fields.Char(required=True)


class ProductSize(models.Model):
    _name = 'product.size'
    _description = 'Product Size'

    name = fields.Char(required=True)


class ProductCategoryCustom(models.Model):
    _name = 'product.category.custom'
    _description = 'Custom Product Category'

    name = fields.Char(required=True)
