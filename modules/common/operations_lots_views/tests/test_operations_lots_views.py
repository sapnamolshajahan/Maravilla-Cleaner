# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "operations_lot_views")
class TestOperationsLotsView(common.TransactionCase):
    """Class to test Operations lots view workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.stock_picking = self.env.ref('stock.outgoing_shipment_main_warehouse')
        self.view = self.env.ref('operations_lots_views.stock_quant_picking_tree')

    def test_action_show_lot_quantities(self):
        """
        Check actions to show lot quantities in stock
        """
        stock_move = self.stock_picking.move_ids[0]
        result = stock_move.action_show_lot_quantities()
        self.assertEqual(self.view.id, result['view_id'])  # Check view_id
        self.assertEqual(stock_move.id, result['res_id'])
        self.assertEqual(result['name'], 'Lots Available')
        # Check product id is the same in stock move and stock quant
        product_id_list = list(filter(lambda x: x[0] == 'product_id', result['domain']))
        product_id = product_id_list[0][2]
        self.assertEqual(stock_move.product_id.id, product_id)
        # Check location id is the same in stock move and stock quant
        location_id_list = list(filter(lambda x: x[0] == 'location_id', result['domain']))
        location_id = location_id_list[0][2]
        self.assertEqual(stock_move.location_id.id, location_id)
