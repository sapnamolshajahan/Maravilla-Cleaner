from odoo import models, fields, api

class EveEvent(models.Model):
    _name = 'eve.event'
    _description = 'Momentus Event'

    momentus_id = fields.Integer(string="Momentus ID", required=True)
    name = fields.Char(string="Description", required=True)
    qty_uplift = fields.Float(
        string="Qty Uplift",
        default=lambda self: self.env.company.qty_uplift,
        help="Percentage increase to apply to quantities for this event. Defaults to the company setting."
    )
