from odoo.tests.common import TransactionCase, tagged
from odoo import fields


@tagged('product_bom')
class TestProductBOMPrice(TransactionCase):

    def setUp(self):
        super(TestProductBOMPrice, self).setUp()
        self.product_a = self.env.ref('mrp.product_product_wood_panel')
        self.bom = self.env.ref('mrp.mrp_bom_wood_panel')
        self.bom_line_ply = self.env.ref('mrp.mrp_bom_line_wood_panel_ply')
        self.bom_line_wear = self.env.ref('mrp.mrp_bom_line_wood_panel_wear')

    def test_cron_product_bom_price_and_update_cost(self):
        self.bom.write({'write_date': fields.Datetime.now()})

        # Get the product's UoM (Unit of Measure)
        product_uom = self.product_a.uom_id

        # Simulate a manufacturing order with a 'done' state
        self.env['mrp.production'].create({
            'product_id': self.product_a.id,
            'bom_id': self.bom.id,
            'state': 'done',
            'create_date': fields.Datetime.now(),
            'product_uom_id': product_uom.id,
            'product_qty': 1.0,
        })
        self.product_a._cron_product_bom_price()

        # Calculate expected cost
        expected_cost = (
                                (self.bom_line_ply.product_id.standard_price * self.bom_line_ply.product_qty) +
                                (self.bom_line_wear.product_id.standard_price * self.bom_line_wear.product_qty)
                        ) / self.bom.product_qty

        # Verify the product's standard price has been updated
        self.assertAlmostEqual(
            self.product_a.standard_price,
            expected_cost,
            places=2,
            msg=f"Product cost for {self.product_a.name} was not updated correctly by the cron job."
        )
