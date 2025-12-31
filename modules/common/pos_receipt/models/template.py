from odoo import api, fields, models


class Label(models.Model):
    """
    Label Template
    """
    _inherit = "label.printer.template"

    flavour = fields.Selection(selection_add=[("escpos", "ESC PoS")], ondelete={'escpos': 'set zpl'})
