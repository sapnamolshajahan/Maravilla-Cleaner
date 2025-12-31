# -*- coding: utf-8 -*-
import logging

from odoo import models, api
from odoo.addons.base_generic_changes.utils.config import configuration

CONFIG_SECTION = "mail_enable_rc"
KEY_FETCH = "enable_fetch"

ENABLE_FETCH = configuration.get(CONFIG_SECTION, KEY_FETCH)

_logger = logging.getLogger(__name__)


class FetchMailServer(models.Model):
    _inherit = "fetchmail.server"

    @api.model
    def _fetch_mails(self):
        """
        Method called by cron to fetch mails from servers
        """
        if not ENABLE_FETCH:
            _logger.info("disabled fetching emails from servers")
            return False
        return super()._fetch_mails()
