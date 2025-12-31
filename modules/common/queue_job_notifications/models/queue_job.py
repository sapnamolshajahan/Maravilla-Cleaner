# -*- coding: utf-8 -*-
from odoo import models, fields


class QueueJobNotifications(models.Model):
    _inherit = "queue.job"

    suppress_success_notification = fields.Boolean(default=True)
    suppress_error_notification = fields.Boolean(default=True)

    def set_suppress_notifications(self, uuid, sen, ssn):
        """
        set ssn/sen False to send email notification
        """
        rec = self.search([('uuid', '=', uuid)], limit=1)
        rec.write({'suppress_error_notification': sen, 'suppress_success_notification': ssn})

    def write(self, values):
        res = super(QueueJobNotifications, self).write(values)
        if values.get("state") in ("done", "failed"):
            self._queue_job_notifications()
        return res

    def _queue_job_notifications(self):
        for task in self:
            sen = task.suppress_error_notification
            ssn = task.suppress_success_notification
            if task.state == 'failed' and not sen:
                mail_tmpl = self.env.ref('queue_job_notifications.job_queue_update_failed')
                mail_tmpl.sudo().send_mail(task.id, force_send=False, raise_exception=True)

            if task.state == 'done' and not ssn:
                mail_tmpl = self.env.ref('queue_job_notifications.job_queue_update_done')
                mail_tmpl.sudo().send_mail(task.id, force_send=False, raise_exception=True)
