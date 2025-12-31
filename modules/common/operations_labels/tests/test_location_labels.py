from odoo.tests.common import tagged, TransactionCase
from odoo.exceptions import UserError
from unittest.mock import patch


@tagged('common', 'operations_labels')
class TestLocationLabels(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create test printer and label template
        self.printer = self.env['label.printer'].create({
            'label': 'Test Printer',
            'queue': 'test_queue'
        })
        self.label_template = self.env['label.printer.template'].create({
            'name': 'Test Label Template',
            'model': 'stock.location',
            'state': 'a-active',
        })

        # Create test stock locations with and without barcodes
        self.location_with_barcode = self.env['stock.location'].create({
            'name': 'Location With Barcode',
            'barcode': 'LOC123',
        })
        self.location_without_barcode = self.env['stock.location'].create({
            'name': 'Location Without Barcode',
            'barcode': False,
        })

    def test_location_labels_wizard(self):
        """Test the Location Labels wizard functionality"""
        # Create wizard instance with locations
        wizard = self.env['operations.labels.location.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'lines': [(0, 0, {'location': self.location_with_barcode.id}),
                      (0, 0, {'location': self.location_without_barcode.id})],
        })

        action_result = wizard.action_print()

        # Test action_print with check_barcode=False in context
        wizard_with_barcode_check = self.env['operations.labels.location.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'lines': [(0, 0, {'location': self.location_with_barcode.id}),
                      (0, 0, {'location': self.location_without_barcode.id})],
        })

        with patch('odoo.addons.label_printer.models.template.Label.print_to_queue') as mock_print_to_queue:
            wizard_with_barcode_check.with_context(check_barcode=False).action_print()
            mock_print_to_queue.assert_called_once_with(self.location_with_barcode, 'test_queue')

    def test_show_confirm(self):
        """Test that show_confirm is called when some locations lack barcodes"""
        wizard = self.env['operations.labels.location.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'lines': [(0, 0, {'location': self.location_with_barcode.id}),
                      (0, 0, {'location': self.location_without_barcode.id})],
        })

        wizard.action_print()  # This should trigger the show_confirm method

    def test_action_print_without_barcode_check(self):
        """Test that labels are printed only if barcodes are present (with check_barcode=False)"""
        wizard = self.env['operations.labels.location.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'lines': [(0, 0, {'location': self.location_with_barcode.id}),
                      (0, 0, {'location': self.location_without_barcode.id})],
        })

        with patch('odoo.addons.label_printer.models.template.Label.print_to_queue') as mock_print_to_queue:
            wizard.with_context(check_barcode=False).action_print()  # Skip barcode check
            mock_print_to_queue.assert_called_once_with(self.location_with_barcode, 'test_queue')

    def test_location_labels_confirm(self):
        """Test the Location Labels Confirmation wizard"""
        # Create Location Labels Wizard Confirm instance
        wizard = self.env['operations.labels.location.wizard.confirm'].create({
            'wizard_id': self.env['operations.labels.location.wizard'].create({
                'printer_id': self.printer.id,
                'label': self.label_template.id,
                'lines': [(0, 0, {'location': self.location_with_barcode.id}),
                          (0, 0, {'location': self.location_without_barcode.id})],
            }).id
        })

        wizard.action_print()

    def test_invalid_location_without_barcode(self):
        """Test validation when locations without barcode are handled"""
        wizard = self.env['operations.labels.location.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'lines': [(0, 0, {'location': self.location_without_barcode.id})],
        })
        wizard.action_print()

    def test_create_wizard(self):
        """Test creating a wizard with a set of locations"""
        locations = [self.location_with_barcode, self.location_without_barcode]
        wizard = self.env['operations.labels.location.wizard'].create_wizard(locations)

        self.assertEqual(len(wizard.lines), 2)
        self.assertTrue(all(line.location in locations for line in wizard.lines))
