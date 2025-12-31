# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('common', 'queue_job_notifications')
class TestQueueJobNotifications(TransactionCase):

    def setUp(self):
        super(TestQueueJobNotifications, self).setUp()
        self.queue_job_model = self.env["queue.job"].sudo()

        self.job_partner = self.env["res.partner"].with_delay().create({
            "name": "Test"
        })
        self.job = self.queue_job_model.search([], order="id desc", limit=1)

    def test_set_suppress_notifications(self):
        """Test setting suppress notifications via set_suppress_notifications"""
        self.job.set_suppress_notifications(self.job.uuid, False, False)

        self.assertFalse(self.job.suppress_error_notification, "Error notification should be False")
        self.assertFalse(self.job.suppress_success_notification, "Success notification should be False")

    def test_write_triggers_notifications(self):
        """Test that state change triggers notification"""
        self.job.write({'state': 'done'})
        self.assertEqual(self.job.state, 'done', "Job state should be updated to 'done'")

        self.job.write({'state': 'failed'})
        self.assertEqual(self.job.state, 'failed', "Job state should be updated to 'failed'")

    def test_queue_job_notifications(self):
        """Test the notification system based on job state"""
        mail_template_done = self.env.ref("queue_job_notifications.job_queue_update_done")
        mail_template_failed = self.env.ref("queue_job_notifications.job_queue_update_failed")

        self.job.suppress_success_notification = False
        self.job.suppress_error_notification = False

        self.job.write({'state': 'done'})
        self.assertEqual(self.job.state, 'done', "Job should be marked as done")
        mail_done = mail_template_done.send_mail(self.job.id, force_send=False, raise_exception=False)
        self.assertTrue(mail_done, "Mail should be sent for 'done' state")

        self.job.write({'state': 'failed'})
        self.assertEqual(self.job.state, 'failed', "Job should be marked as failed")
        mail_failed = mail_template_failed.send_mail(self.job.id, force_send=False, raise_exception=False)
        self.assertTrue(mail_failed, "Mail should be sent for 'failed' state")

    def test_no_notification_if_suppressed(self):
        """Test no notification is sent if suppress flags are True"""
        self.job.suppress_success_notification = True
        self.job.suppress_error_notification = True

        self.job.write({'state': 'done'})
        mail_template_done = self.env.ref("queue_job_notifications.job_queue_update_done")
        mail_sent_done = mail_template_done.send_mail(self.job.id, force_send=False, raise_exception=False)
        self.assertFalse(mail_sent_done, "No mail should be sent for 'done' state when suppressed")

    def test_no_notification_if_not_suppressed(self):
        """Test no notification is sent if suppress flags are False"""
        self.job.suppress_success_notification = False
        self.job.suppress_error_notification = False

        self.job.write({'state': 'failed'})
        mail_template_failed = self.env.ref("queue_job_notifications.job_queue_update_failed")
        mail_sent_failed = mail_template_failed.send_mail(self.job.id, force_send=False, raise_exception=False)
        self.assertFalse(mail_sent_failed, "No mail should be sent for 'failed' state when suppressed")
