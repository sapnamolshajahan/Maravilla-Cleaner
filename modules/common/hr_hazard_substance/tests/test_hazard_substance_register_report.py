from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.hr_hazard_substance.report.hazard_substance_register_report_helper import HazardSubstanceRegisterReportHelper


@tagged('hr_hazard_substance')
class TestHazardSubstanceRegisterReportHelper(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].search([], limit=1)
        self.hazard_location = self.env["stock.location"].create({
            "name": "Bin A",
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'default_code': 'TEST',
        })
        self.warehouse = self.env['stock.warehouse'].create({
            'name': "Sample Warehouse",
            'code': "SW",
            'company_id': self.company.id,
        })
        self.warehouse_bin = self.env['stock.warehouse.bin'].create({
            'name': "sample warehouse",
            'product_id': self.product.id,
            'warehouse_id': self.warehouse.id,
        })
        self.product_template = self.env["product.template"].create({
            "name": "Test Hazard Product",
            "hazard_approval_nr": "HAZ12345",
            "hazard_classifications": "Class A",
            "hazard_sds_issuing_date": "2025-01-01",
            "hazard_storage_reqs": "Store in cool, dry place",
            "hazard_max_qty": 100.0,
            "hazard_ppe_notes": "Wear gloves and goggles",
            "hazard_location": self.warehouse_bin.id,
        })
        self.product = self.product_template.product_variant_ids[0]
        self.product.write({
            "company_id": self.env.company.id,
            "free_qty": 50.0,
            "hazard_location": self.warehouse_bin.id,  # Assign the location properly
        })


    def test_product_method(self):
        """Test the `product` method in the HazardSubstanceRegisterReportHelper."""
        self.product.hazard_location =  self.warehouse_bin.id
        helper = HazardSubstanceRegisterReportHelper
        result = helper.product(self,self.product_template.id)
        self.assertEqual(result["company"], self.env.company.name, "Company name mismatch")
        self.assertEqual(result["product-name"], self.product.display_name, "Product name mismatch")
        self.assertEqual(result["hazard-approval-nr"], "HAZ12345", "Hazard approval number mismatch")
        self.assertEqual(result["hazard-classification"], "Class A", "Hazard classification mismatch")
        self.assertEqual(result["hazard-storage-reqs"], "Store in cool, dry place", "Hazard storage requirements mismatch")
        self.assertEqual(result["hazard-bin-location"], "sample warehouse", "Hazard bin location mismatch")
        self.assertEqual(result["available-qty"], 50.0, "Available quantity mismatch")
        self.assertEqual(result["hazard-ppe-notes"], "Wear gloves and goggles", "Hazard PPE notes mismatch")
