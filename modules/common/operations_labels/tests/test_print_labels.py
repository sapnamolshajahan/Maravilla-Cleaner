from odoo.tests.common import tagged, TransactionCase
from odoo.exceptions import UserError
from unittest.mock import patch


@tagged('common', 'operations_labels')
class TestProductLabels(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create a test printer and label template
        self.printer = self.env['label.printer'].create({
            'label': 'Test Printer',
            'queue': 'test_queue'
        })
        self.label_template = self.env['label.printer.template'].create({
            'name': 'Test Label Template',
            'model': 'product.product',
        })

        # Create a test product with and without barcode
        self.product_template = self.env['product.template'].create({
            'name': 'Test Product Template',
        })
        self.product_with_barcode = self.env['product.product'].create({
            'name': 'Test Product With Barcode',
            'barcode': '1234567890',
            'product_tmpl_id': self.product_template.id,
        })
        self.product_without_barcode = self.env['product.product'].create({
            'name': 'Test Product Without Barcode',
            'barcode': False,
            'product_tmpl_id': self.product_template.id,
        })

    def test_product_labels_wizard(self):
        """Test the Product Labels wizard functionality"""
        # Create wizard instance
        wizard = self.env['operations.labels.product.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'product_ids': [(6, 0, [self.product_with_barcode.id, self.product_without_barcode.id])],
        })

        action_result = wizard.action_print()

        # Test action_print with check_barcode=False in context
        wizard_with_barcode_check = self.env['operations.labels.product.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'product_ids': [(6, 0, [self.product_with_barcode.id, self.product_without_barcode.id])],
        })

        with patch('odoo.addons.label_printer.models.template.Label.print_to_queue') as mock_print_to_queue:
            wizard_with_barcode_check.with_context(check_barcode=False).action_print()
            mock_print_to_queue.assert_called_once_with(self.product_with_barcode, 'test_queue')

    def test_show_confirm(self):
        """Test show_confirm method behavior when there are products without barcodes"""
        wizard = self.env['operations.labels.product.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'product_ids': [(6, 0, [self.product_with_barcode.id, self.product_without_barcode.id])],
        })

        wizard.action_print()

    def test_action_print_without_barcode_check(self):
        """Test that labels are printed only if barcodes are present"""
        wizard = self.env['operations.labels.product.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'product_ids': [(6, 0, [self.product_with_barcode.id, self.product_without_barcode.id])],
        })

        with patch('odoo.addons.label_printer.models.template.Label.print_to_queue') as mock_print_to_queue:
            wizard.with_context(check_barcode=False).action_print()  # Skip barcode check
            mock_print_to_queue.assert_called_once_with(self.product_with_barcode, 'test_queue')


    def test_invalid_product_without_barcode(self):
        """Test validation when products without barcode are handled"""
        wizard = self.env['operations.labels.product.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'product_ids': [(6, 0, [self.product_without_barcode.id])],
        })

        with self.assertRaises(UserError):
            wizard.action_print()

    def test_compute_active_model(self):
        """Test the compute method for active_model"""
        wizard = self.env['operations.labels.product.wizard'].create({
            'printer_id': self.printer.id,
            'label': self.label_template.id,
            'product_ids': [(6, 0, [self.product_with_barcode.id])],
        })
        self.assertEqual(wizard.active_model, 'product.product')

        wizard.product_tmpl_ids = [(6, 0, [self.product_template.id])]
        wizard._compute_active_model()
        self.assertEqual(wizard.active_model, 'product.template')
