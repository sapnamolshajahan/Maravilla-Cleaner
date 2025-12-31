from odoo import models, fields

class CustomerPriority(models.Model):
    _name = 'customer.priority'
    _description = 'Customer Priority'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)


class CustomerType(models.Model):
    _name = 'customer.type'
    _description = 'Customer Type'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
