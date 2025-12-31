from odoo.tests.common import TransactionCase, tagged
import base64


@tagged('common', 'account_generic_changes')
class TestAccountJournalExport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.move = self.env['account.move'].create({
            'name': 'Original Move',
            'move_type': 'out_invoice',
            'partner_id': self.partner.id
        })
        self.journal_export = self.env['account.journal.export'].create({'move_id': self.move.id})

    def test_button_process(self):
        """Test the journal export process."""
        self.journal_export.button_process()
        self.assertTrue(self.journal_export.data, "Exported data should be available.")


@tagged('common', 'account_generic_changes')
class TestMoveReversal(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.move = self.env['account.move'].create({
            'name': 'Original Move',
            'move_type': 'out_invoice',
            'partner_id': self.partner.id
        })
        self.main_company_id = self.env.ref('base.main_company').id
        self.journal_id = self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', self.main_company_id)], limit=1).id

        self.reversal_wizard = self.env['account.move.reversal'].create({
            'move_ids': [(6, 0, [self.move.id])],
            'journal_id': self.journal_id
        })

    def test_prepare_default_reversal(self):
        """Test the move reversal logic ensures unique references."""
        reversal_vals = self.reversal_wizard._prepare_default_reversal(self.move)
        self.assertIn('invoice_origin', reversal_vals, "Reversal should contain invoice_origin.")

