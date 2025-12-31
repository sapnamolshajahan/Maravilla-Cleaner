# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class SaleMoveReport(models.Model):
    """
    View-based for sales moves.
    """
    _name = "sale.move.report"
    _description = "Sale Moves Report"
    _auto = False

    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    date = fields.Datetime(string="Date Done", readonly=True)
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", readonly=True)
    quantity = fields.Float(string="Quantity", readonly=True)

    @classmethod
    def _get_move_query(cls):
        """
        Query to retrieve moves for the report
        """
        print('_get_move_query')
        return """
        select
            max (stock_move.id) as id,  
            stock_move.company_id as company_id,  
            date as date,  
            stock_move.product_id as product_id,    
            stock_move.warehouse_id as warehouse_id, 
            sum (
                case
                when stock_location.usage='internal' then stock_move.product_qty
                when stock_location.usage='customer' then - stock_move.product_qty  
                end
            ) as quantity  
        from stock_move
        join stock_location on stock_move.location_id = stock_location.id
        join stock_location stock_destination on stock_move.location_dest_id = stock_destination.id
        where stock_location.usage in ('internal', 'customer')
        and stock_destination.usage in ('internal', 'customer')  
        and state = 'done'  
        group by stock_move.id
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'sale_move_report')
        self.env.cr.execute("CREATE or REPLACE VIEW sale_move_report AS ({m})".format(m=self._get_move_query()))
