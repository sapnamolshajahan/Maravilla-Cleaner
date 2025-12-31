# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('common', 'label_printer')
class TestLabelPrinter(TransactionCase):
    def setUp(self):
        super(TestLabelPrinter, self).setUp()
        self.label_template = self.env["label.printer.template"].create({
            "name": "Test Label",
            "description": "Test Label Description",
            "flavour": "zpl",
            "model": "res.partner",
            "content": "Sample label template content",
            "state": "a-active",
        })

        self.partner = self.env.ref('base.res_partner_2')

        self.wizard = self.env["label.printer.wizard"].create({
            "template": self.label_template.id,
            "queue": "print_queue",
            "record": self.partner.id
        })

    def test_label_creation(self):
        """Test label template creation"""
        self.assertEqual(self.label_template.name, "Test Label")
        self.assertEqual(self.label_template.flavour, "zpl")
        self.assertEqual(self.label_template.state, "a-active")

    def test_flavour_notes_computation(self):
        """Test computed field 'flavour_notes' updates correctly"""
        self.label_template.flavour = "dpl"
        self.label_template._flavour_notes()
        self.assertIn("Newlines are auto-converted", self.label_template.flavour_notes)

    def test_current_label_search(self):
        """Test fetching the latest active template by name"""
        found_template = self.env["label.printer.template"].current("Test Label")
        self.assertEqual(found_template, self.label_template)

    def test_print_to_queue_invalid_model(self):
        """Test that print_to_queue raises an exception when given an incorrect model"""
        bank = self.env.ref('base.res_bank_1')
        with self.assertRaises(Exception):
            self.label_template.print_to_queue(bank, "print_queue")

    def test_action_print_label(self):
        """Test action to open the print label wizard"""
        action = self.label_template.action_print_label()
        self.assertEqual(action["res_model"], "label.printer.wizard")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["target"], "new")

    def test_button_print_success(self):
        """Test successful execution of button_print"""
        action = self.wizard.button_print()
        self.assertEqual(action, {'type': 'ir.actions.act_window_close'})

    def test_button_print_no_queue(self):
        """Test button_print raises UserError when queue is missing"""
        self.wizard.queue = False
        with self.assertRaises(UserError, msg="Queue needs to be specified"):
            self.wizard.button_print()

    def test_button_print_no_record(self):
        """Test button_print raises UserError when record is missing"""
        self.wizard.record = False
        with self.assertRaises(UserError, msg="Record to Print required"):
            self.wizard.button_print()
