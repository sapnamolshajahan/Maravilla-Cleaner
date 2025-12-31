from odoo import fields, models



class Delivery(models.Model):
    _inherit = "delivery.carrier"

    gln = fields.Text(string="GLN Code")