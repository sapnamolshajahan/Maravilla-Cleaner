from odoo import fields, models

class PlasticBomDieChange(models.TransientModel):
    _name = 'plastic.bom.die.change'

    plastic_bom_builder = fields.Many2one('plastic.bom.builder', string='BOM Builder')
    product = fields.Many2one('product.template', string='Cost Type')
    minutes = fields.Integer(string='Minutes')


class PlasticBomWorkcentre(models.TransientModel):
    _name = 'plastic.bom.workcentre'

    plastic_bom_builder = fields.Many2one('plastic.bom.builder', string='BOM Builder')
    workcentre = fields.Many2one('mrp.workcenter', string='Workcentre')
    cycle_time = fields.Float(string='Cycle Time')
    machine_efficiency = fields.Float(string='Machine Efficiency %')
    labour_loading = fields.Many2one('plastic.bom.labour.loading', string='Labour Loading')

class PlasticBomLabourLoading(models.TransientModel):
    _name = 'plastic.bom.labour.loading'

    name = fields.Char(string='Description')

class PlasticBuilder(models.TransientModel):
    _name = 'plastic.bom.builder'

    name = fields.Char(string='Product Name')
    categ = fields.Many2one('product.category', string='Product Category')
    quantity = fields.Integer(string='Production Quantity')
    sprue_weight = fields.Float(string='Sprue Weight')
    regrind_type = fields.Selection(string='Regrind Type', selection=[('online', 'On Line'), ('offline', 'Off Line')])
    regrind_pct = fields.Float(string='Regrind %')
    sets_per_shot = fields.Integer(string='Sets per Shot', default=1)
    shot_weight = fields.Float(string='Shot Weight')
    total_weight = fields.Float(string='Total Weight per Shot')
    unit_weight = fields.Float(string='Weight per Unit')
    die_change_costs = fields.One2many('plastic.bom.die.change', 'plastic_bom_builder',
                                       string='Die Change Costs')
    workcentres = fields.One2many('plastic.bom.workcentre', 'plastic_bom_builder',
                                       string='Workcentres')
    purge_kg = fields.Float('Purge Qty (Kg)')
    box_type = fields.Many2one('product.template', string='Pack Type')
    qty_per_box = fields.Integer(string='Qty per pack')

    plastic = fields.Many2one('product.template', string='Base Material')
    mats_efficiency = fields.Float(string='Base Material Efficiency %')
    notes=fields.Text(string='Notes')