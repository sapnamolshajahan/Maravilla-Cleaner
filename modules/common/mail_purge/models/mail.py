# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

MAIL_PURGE_DAYS_KEY = "mail_purge.purge_days"


class MailMail(models.Model):
    _inherit = "mail.mail"

    @api.model
    def do_mail_purge(self):
        """Purge old emails"""

        purge_days = self.env["ir.config_parameter"].get_param(MAIL_PURGE_DAYS_KEY, default=0)
        try:
            purge_days = int(purge_days)
        except Exception as e:
            _logger.warning("do_mail_purge - purge days must be an integer. Error: {}".format(e))
            return

        if purge_days < 1:
            _logger.info("do_mail_purge purge_days zero or not set - terminating")
            return

        purge_date = fields.Datetime.from_string(fields.Date.today())
        purge_date = fields.Datetime.to_string(purge_date - timedelta(days=purge_days))
        purge_mails = self.search([("create_date", "<", purge_date)])
        count = len(purge_mails)

        if count:
            purge_mails.unlink()
            _logger.info("purged {} emails".format(count))
