from odoo import models, fields


class ITMControLDocument(models.Model):
    _name = "itm.control.document"

    filename = fields.Char(help='Control document file name')
    associated_invoice = fields.Many2one("account.move")
    content = fields.Char(help='Contents of control document')
