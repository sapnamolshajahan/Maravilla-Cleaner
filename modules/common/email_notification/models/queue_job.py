# -*- coding: utf-8 -*-
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class QueueJobNotifications(models.Model):
    _inherit = "queue.job"

    ###########################################################################
    # Default & compute methods
    ###########################################################################

    ###########################################################################
    # Fields
    ###########################################################################

    ###########################################################################
    # Functions
    ###########################################################################
    def write(self, values):
        res = super(QueueJobNotifications, self).write(values)
        if values.get("state") in ("done", "failed"):
            self._send_task_notifications()
        return res

    def _send_task_notifications(self):
        """ Send success or error notifications for the task"""
        for task in self:
            if task.state == 'failed' and task.company_id.error_template_id:
                template = self.env['mail.template'].browse(task.company_id.error_template_id.id)
                mail_id = template.send_mail(task.id)
                _logger.info('_send_task_notifications - sent error email - message id = {id}'.format(id=mail_id))

            if task.state == 'done' and task.company_id.success_template_id:
                template = self.env['mail.template'].browse(task.company_id.success_template_id.id)
                mail_id = template.send_mail(task.id)
                _logger.info('_send_task_notifications - sent success email - message id = {id}'.format(id=mail_id))
