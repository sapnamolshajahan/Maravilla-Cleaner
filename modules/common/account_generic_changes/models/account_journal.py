# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountJournalExtension(models.Model):
    _inherit = "account.journal"

    ################################################################################
    # Fields
    ################################################################################
    short_description = fields.Char(string="Short Description", help="Please enter a short description.")
    use_for_statement_bank_account = fields.Boolean(string="Use this Bank Account for printing on Statements",
                                                    help=("If set, the bank account attached to this "
                                                          "is used as the remittance account on a "
                                                          "statement for the currency matching the "
                                                          "journal currency")
                                                    )

    bank_account_for_invoice = fields.Char(string='Bank Account for printing on Invoice',
                                           help='If not set will use the company bank account from this journal')

    entry_posted = fields.Boolean(string='Autopost Created Moves',
                                  help='Check this box to automatically post entries of this journal.'
                                       ' Note that legally, some entries may be automatically posted '
                                       'when the source document is validated (Invoices),'
                                       ' whatever the status of this field.')
    sequence_id = fields.Many2one("ir.sequence", string="Document Sequence", check_company=True, copy=False)
    refund_sequence_id = fields.Many2one("ir.sequence", string="Credit Note Entry Sequence", copy=False,
                                         help="Journal Sequence Generator for Credit Notes")
