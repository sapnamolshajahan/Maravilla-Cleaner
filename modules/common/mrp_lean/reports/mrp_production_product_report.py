# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class MRPProductionProductReport(models.Model):
    _name = "mrp.production.product.report"
    _description = "MO to Product Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    @api.model
    def _get_done_states(self):
        return ['sale', 'done']

    name = fields.Char('Order Name', readonly=True)
    date = fields.Datetime('Order Date', readonly=True)
    production_product_id = fields.Many2one('product.product', 'Product', readonly=True)
    production_product_qty = fields.Float('Production Qty', readonly=True)
    raw_material_product_id = fields.Many2one('product.product', 'Raw material Product', readonly=True)
    raw_material_product_qty = fields.Float('Production Qty', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    production_state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State')

    def _select_production(self):
        select_sql = \
            f"""
            MIN(p.id) AS id,
            p.name AS name,
            p.date_start AS date,
            p.product_id AS production_product_id,
            MAX(p.product_qty) AS production_product_qty,
            pp.id AS raw_material_product_id,
            MAX(sm.product_qty) AS raw_material_product_qty,
            p.company_id AS company_id,
            p.state AS production_state
            """
        return select_sql


    def _from_production(self):
        return """
            mrp_production p
            LEFT JOIN mrp_bom_line b on p.bom_id = b.bom_id
            LEFT JOIN stock_move sm on sm.raw_material_production_id = p.id
            LEFT JOIN product_product pp on b.product_id = pp.id
            LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id 
            """

    def _where_production(self):
        return """
            p.state in ('confirmed','progress') 
            and pt.track_lean = True
            """

    def _group_by_production(self):
        return """
            p.name,
            p.date_start,
            pp.id,
            p.product_id,
            p.company_id,
            p.state
            """

    def _query(self):
        query =  f"""
            SELECT {self._select_production()}
            FROM {self._from_production()}
            WHERE {self._where_production()}
            GROUP BY {self._group_by_production()}
        """
        return query

    @property
    def _table_query(self):
        return self._query()
