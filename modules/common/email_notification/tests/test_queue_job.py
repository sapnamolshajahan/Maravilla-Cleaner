# -*- coding: utf-8 -*-
import logging
from unittest.mock import patch

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "email_notification")
class TestQueueJob(common.TransactionCase):
    """Class to test queue.job workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.success_template = self.env["mail.template"].create({
            "name": "Success Template",
            "subject": "Task Completed Successfully",
            "email_from": "test@example.com",
            "body_html": "<p>Task Completed Successfully.</p>",
            "model_id": self.env.ref("queue_job.model_queue_job").id,
        })
        self.error_template = self.env["mail.template"].create({
            "name": "Error Template",
            "subject": "Task Failed",
            "email_from": "test@example.com",
            "body_html": "<p>Task Failed.</p>",
            "model_id": self.env.ref("queue_job.model_queue_job").id,
        })
        self.env.company.write({
            "error_template_id": self.error_template.id,
            "success_template_id": self.success_template.id,
        })
        self.task = self.env["queue.job"].with_context(
                _job_edit_sentinel=self.env["queue.job"].EDIT_SENTINEL,
            ).create({
            "name": "Test Task",
            "state": "pending",
            "company_id": self.env.company.id,
            'uuid': '424242'
        })

    @patch("odoo.addons.email_notification.models.queue_job._logger.info")
    @patch("odoo.addons.mail.models.mail_template.MailTemplate.send_mail")
    def test_send_task_notifications(self, mock_send_mail, mock_logger_info):
        """
        Test that _send_task_notifications sends emails based on task state.
        """
        # Simulate task completion
        self.task.write({"state": "done"})
        mock_send_mail.assert_called_once_with(self.task.id)
        mock_logger_info.assert_called_with(
            "_send_task_notifications - sent success email - message id = {id}".format(id=mock_send_mail.return_value))
        # Simulate task failure
        self.task.write({"state": "failed"})
        self.assertEqual(mock_send_mail.call_count, 2,
                         "Two emails should be sent: one for success and one for failure.")
