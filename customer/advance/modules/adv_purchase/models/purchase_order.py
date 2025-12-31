from odoo import models, fields


class PurhaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    supplier_dispatch = fields.Datetime('Supplier Dispatch')