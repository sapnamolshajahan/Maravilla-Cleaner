# -*- coding: utf-8 -*-
import logging

from odoo import models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def get_journal_from_account(self, xero_account_code):
        xero_config = self.env.company
        account_id = self.env['account.account'].search(
            [('code', '=', xero_account_code), ('company_ids', 'in', xero_config.id)])
        journal_id = self.search([('type', 'in', ['bank', 'cash']), ('default_account_id', '=', account_id.id),
                                  ('company_id', '=', xero_config.id)],
                                 limit=1)
        if not journal_id:
            raise ValidationError(_("Payment journal is not defined for XERO's Account : %s " % xero_account_code))
        return journal_id
