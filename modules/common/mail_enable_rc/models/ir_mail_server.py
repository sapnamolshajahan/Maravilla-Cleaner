# -*- coding: utf-8 -*-
import logging

from odoo import models, api
from odoo.addons.base_generic_changes.utils.config import configuration
from .fetchmail_server import CONFIG_SECTION

KEY_SEND = "enable_send"

ENABLE_SEND = configuration.get(CONFIG_SECTION, KEY_SEND)


_logger = logging.getLogger(__name__)


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    @api.model
    def send_email(self, message, **kwargs):
        """
        Overrides send_email for controls
         the unwanted e-mail sending via conf
         """
        if not ENABLE_SEND:
            _logger.info("email Sending disabled via config")
            return False
        return super(IrMailServer, self).send_email(message, **kwargs)
