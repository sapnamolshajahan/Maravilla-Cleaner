from odoo.tests.common import TransactionCase
from unittest.mock import patch
import logging


class TestAccountJournalCron(TransactionCase):

    def setUp(self):
        super().setUp()
        self.journal = self.env['account.journal']

    @patch('odoo.addons.account_online_sync_rc.models.account_journal.ENABLE_FETCH', True)
    @patch('odoo.addons.account_online_sync_rc.models.account_journal.super')
    def test_cron_fetch_online_transactions_enabled(self, mock_super):
        self.journal._cron_fetch_online_transactions()
        mock_super()._cron_fetch_online_transactions.assert_called_once()


    @patch('odoo.addons.account_online_sync_rc.models.account_journal.ENABLE_FETCH_WAIT', True)
    @patch('odoo.addons.account_online_sync_rc.models.account_journal.super')
    def test_cron_fetch_waiting_online_transactions_enabled(self, mock_super):
        self.journal._cron_fetch_waiting_online_transactions()
        mock_super()._cron_fetch_waiting_online_transactions.assert_called_once()

    @patch('odoo.addons.account_online_sync_rc.models.account_journal.ENABLE_FETCH', False)
    @patch('odoo.addons.account_online_sync_rc.models.account_journal._logger')
    def test_cron_fetch_online_transactions_disabled(self, mock_logger):
        self.journal._cron_fetch_online_transactions()
        mock_logger.info.assert_called_once_with("cron_fetch_online_transactions() disabled")

    @patch('odoo.addons.account_online_sync_rc.models.account_journal.ENABLE_FETCH_WAIT', False)
    @patch('odoo.addons.account_online_sync_rc.models.account_journal._logger')
    def test_cron_fetch_waiting_online_transactions_disabled(self, mock_logger):
        self.journal._cron_fetch_waiting_online_transactions()
        mock_logger.info.assert_called_once_with("cron_fetch_waiting_online_transactions() disabled")
