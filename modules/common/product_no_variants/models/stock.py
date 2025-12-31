# -*- coding: utf-8 -*-
from odoo import models, fields


class StockMove (models.Model):
    _inherit = "stock.move"
    
    picking_state = fields.Selection(related='picking_id.state', string='Status', type='selection', readonly=True,
                                     selection=[('draft', 'Draft'),
                                                ('cancel', 'Cancelled'),
                                                ('waiting', 'Waiting Another Operation'),
                                                ('confirmed', 'Waiting Availability'),
                                                ('assigned', 'Ready to Transfer'),
                                                ('done', 'Transferred')])
