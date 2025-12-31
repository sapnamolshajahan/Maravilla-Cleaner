# -*- coding: utf-8 -*-
import logging
import uuid
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class QueueToken(models.TransientModel):
    """
    Queue Operation Token
    """
    _name = "remote.print.mqtt.token.queue"
    _description = __doc__

    ##################################################################################
    # Fields
    ##################################################################################
    queue = fields.Char("Queue Name", required=True)
    token = fields.Char("Token", required=True)
    expires = fields.Datetime("Expires", required=True)

    @api.model
    def create_for_queue(self, queue):
        """
        :param queue: queue name
        :return: (remote.print.mqtt.token.queue, remote.print.mqtt.job.queue)
        """
        job_queues = self.env["remote.print.mqtt.job.queue"].valid_queues(queue)  # possibly >= 1
        if not job_queues:
            _logger.warning(f"no job.queues found for queue={queue}")
            return None, None

        expires = fields.Datetime.now() + timedelta(minutes=10)
        qtoken = self.create(
            {
                "queue": queue,
                "token": str(uuid.uuid4()),
                "expires": expires,
            })
        return qtoken, job_queues

    @api.model
    def purge_tokens(self):
        """
        Remove expired tokens
        """
        self.search([("expires", "<", fields.Datetime.now())]).unlink()

    @api.model
    def validate_token(self, token):
        return self.search(
            [
                ("token", "=", token),
                ("expires", ">", fields.Datetime.now()),
            ])
