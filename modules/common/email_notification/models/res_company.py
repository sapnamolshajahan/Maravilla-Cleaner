# -*- coding: utf-8 -*-
from odoo import models, fields


class EmailNotificationCompany(models.Model):
    _inherit = "res.company"

    success_template_id = fields.Many2one(comodel_name="mail.template", string="Success Notification Template")
    error_template_id = fields.Many2one(comodel_name="mail.template", string="Error Notification Template")
    task_notification_email_from = fields.Char("Email From", size=32)
