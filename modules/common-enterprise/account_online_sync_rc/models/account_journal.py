# -*- coding: utf-8 -*-
import logging

from odoo import api, models
from odoo.addons.base_generic_changes.utils.config import configuration

CONFIG_SECTION = "account_online_sync_rc"
KEY_FETCH = "enable_fetch"
KEY_FETCH_WAIT = "enable_fetch_wait"

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def _cron_fetch_online_transactions(self):
        ENABLE_FETCH = configuration.get(CONFIG_SECTION, KEY_FETCH) or False
        if ENABLE_FETCH:
            super()._cron_fetch_online_transactions()
        else:
            _logger.info("cron_fetch_online_transactions() disabled")

    @api.model
    def _cron_fetch_waiting_online_transactions(self):
        ENABLE_FETCH_WAIT = configuration.get(CONFIG_SECTION, KEY_FETCH_WAIT) or False
        if ENABLE_FETCH_WAIT:
            super()._cron_fetch_waiting_online_transactions()
        else:
            _logger.info("cron_fetch_waiting_online_transactions() disabled")
