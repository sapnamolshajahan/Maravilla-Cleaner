# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.tools.config import config

EMAIL_NOTIFICATION_ADDRESS = 'task_notification_from_address'
EMAIL_NOTIFICATION_PREFIX = 'task_notification_system_prefix'


class EmailNotification(models.TransientModel):
    _name = 'email.notification'
    _description = 'Email Notification'

    def _get_notification_fields(self):
        """ Get the fields for notification from the configuration file.

        """
        self.notification_email_prefix = config.get('tcs', EMAIL_NOTIFICATION_PREFIX)
        self.notification_from_address = config.get('tcs', EMAIL_NOTIFICATION_ADDRESS)

    ###########################################################################
    # Fields
    ###########################################################################

    file_path = fields.Char(string="File Path", size=256)
    user_id = fields.Many2one(comodel_name="res.users", string="User", required=True)
    report_name = fields.Char(string="Report Name", size=256)

    notification_email_prefix = fields.Char(compute=_get_notification_fields, readonly=True,
                                            string="Email Notification System Prefix")

    notification_from_address = fields.Char(compute=_get_notification_fields, readonly=True,
                                            string="Email Notification From Address")
