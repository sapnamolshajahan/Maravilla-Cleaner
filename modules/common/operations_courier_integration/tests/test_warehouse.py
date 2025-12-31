from odoo.tests import TransactionCase
from odoo.odoo.tests import tagged


@tagged("operations_courier_integration")
class TestWarehouse(TransactionCase):
    def setUp(self):
        super().setUp()
        self.warehouse = self.env["stock.warehouse"].create({
            "name": "Test Warehouse",
            "code": "TWH",
        })
        self.printer1 = self.env["carrier.label.printer"].create({
            "name": "Printer 1",
            "warehouse_id": self.warehouse.id,
            "default": False,
        })
        self.printer2 = self.env["carrier.label.printer"].create({
            "name": "Printer 2",
            "warehouse_id": self.warehouse.id,
            "default": True,
        })
        self.box = self.env["stock.warehouse.box"].create({
            "name": "Box A",
            "width": 10.0,
            "height": 15.0,
            "length": 20.0,
            "default_kgs": 2.0,
            "type": "Carton",
            "hire_type_account": "12345",
            "hire_company": "C",
            "hire_type": "R",
            "equipment_type": "P",
            "is_pallet": False,
        })

    def test_default_printer_with_default(self):
        """Test that the method returns the default printer if one is set."""
        printer = self.warehouse.default_printer()
        self.assertEqual(printer, self.printer2, "The default printer should be Printer 2")

    def test_default_printer_without_default(self):
        """Test that the method returns the first printer if no default printer is set."""
        self.printer2.default = False
        printer = self.warehouse.default_printer()
        self.assertEqual(printer, self.printer1,
                         "The first printer in the list should be returned when no default is set")

    def test_default_printer_no_printers(self):
        """Test that the method returns None if no printers are available."""
        self.warehouse.carrier_label_printer_ids.unlink()
        printer = self.warehouse.default_printer()
        self.assertIsNone(printer, "Method should return None if no printers exist")

    def test_compute_display_name(self):
        """Test that display name is correctly computed."""
        self.box._compute_display_name()
        expected_display_name = "Box A(15.0x10.0x20.0)"
        self.assertEqual(self.box.display_name, expected_display_name, "Display name should be in the correct format")

    def test_compute_display_name_empty_fields(self):
        """Test that display name is empty if required fields are missing."""
        self.box.name = ""
        self.box._compute_display_name()
        self.assertEqual(self.box.display_name, "", "Display name should be empty when required fields are missing")

