from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('hr_hazard_substance')
class TestHazardousProduct(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].search([], limit=1)
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': 'True',
            'type': "consu",
        })
        self.warehouse = self.env['stock.warehouse'].create({
            'name': "Sample Warehouse",
            'code': "SW",
            'company_id': self.company.id,
        })
        self.warehouse_bin = self.env['stock.warehouse.bin'].create({
            'name' :"sample warehouse",
            'product_id' :self.product.id,
            'warehouse_id' :self.warehouse.id,
        })
        self.product_template = self.env['product.template'].create({
            'name': 'Test Hazardous Product',
            'hazard_substance': True,
            'hazard_approval_nr': '12345',
            'hazard_classifications': 'Class A',
        })
        self.product_variant = self.env['product.product'].create({
            'name': 'Variant of Hazardous Product',
        })

    def test_compute_location_product_template(self):
        self.product_template._compute_location()
        self.assertEqual(self.product_template.hazard_location.id,False,
                         "Hazard location should be set to the None.")
        self.assertEqual(self.product_template.hazard_max_qty,0,
                         "Hazard max quantity should set to 0.")
        self.product_template.write({'bin_ids': [(6, 0, [self.warehouse_bin.id])]})
        self.product_template._compute_location()
        self.assertEqual(self.product_template.hazard_max_qty, self.warehouse_bin.max,
                         "Hazard max quantity should match the bin's max quantity.")


    def test_compute_location_product_product(self):
        """
        Test _compute_location for product.product.
        It should correctly set the hazard location and max quantity.
        """
        self.product_variant._compute_location()
        self.assertEqual(self.product_variant.hazard_location.id, False,
                         "Hazard location should be set to the None.")
        self.assertEqual(self.product_variant.hazard_max_qty, 0,
                         "Hazard max quantity should set to 0.")
        self.product_variant.write({'bin_ids': [(6, 0, [self.warehouse_bin.id])]})
        self.product_variant._compute_location()
        self.assertEqual(self.product_variant.hazard_max_qty, self.warehouse_bin.max,
                         "Hazard max quantity should match the bin's max quantity.")

    def test_hazardous_product_creation_constraint(self):
        """
        Test that hazardous product creation raises an error if variants exist.
        """
        self.product_template.hazard_substance = True
        with self.assertRaises(UserError, msg="Creating a variant for hazardous product should raise a UserError."):
            self.env['product.product'].create({
                'name': 'Another Variant',
                'product_tmpl_id': self.product_template.id,
            })
