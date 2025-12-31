# -*- coding: utf-8 -*-
import logging

from odoo.http import root, FilesystemSessionStore

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _logout_users(self):
        if isinstance(root.session_store, FilesystemSessionStore):
            _logger.info("Logging everyone out")
            root.session_store.vacuum(0)
