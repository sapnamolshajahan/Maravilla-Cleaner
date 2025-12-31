# -*- coding: utf-8 -*-
import time
from odoo import models, api, fields


class MailMail(models.Model):
    _inherit = "mail.mail"

    def send(self, auto_commit=False, raise_exception=False, post_send_callback=None):
        sleep_time = self.env.company.sleep_time

        result = super(MailMail, self).send(auto_commit, raise_exception, post_send_callback)
        # Apply micro-sleep if configured
        if sleep_time > 0:
            time.sleep(sleep_time)
        return result
