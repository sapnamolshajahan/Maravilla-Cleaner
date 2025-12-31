# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, SUPERUSER_ID
from odoo.modules.registry import Registry
from ..publisher import PrintPublisher

_logger = logging.getLogger(__name__)


class Job(models.Model):
    """
    Print Job
    """
    _name = "remote.print.mqtt.job"
    _description = __doc__

    ##################################################################################
    # Fields
    ##################################################################################
    queue = fields.Char("Queue Name", required=True)
    copies = fields.Integer("Copies", required=True, default=1)
    data = fields.Binary("Content", attachment=False, required=True)

    @api.model
    def jobs_for_queue(self, queue):
        """
        :param queue: queue-name (str)
        """
        return self.search([("queue", "=", queue)], order="id")

    @api.model
    def submit_print(self, queue, data_list, copies=1):
        """
        Submit job and notify print-agents.

        :param queue: queue name
        :param data_list: list of bytes
        :param copies: number of copies
        """
        dbname = self.env.cr.dbname
        db_registry = Registry(dbname)

        # Localise the change with a separate cursor
        with db_registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            env[self._name].create(
                [{
                    "queue": queue,
                    "copies": copies,
                    "data": data,
                } for data in data_list])
            qtoken, job_queues = env["remote.print.mqtt.token.queue"].create_for_queue(queue)
            cr.commit()  # job must be present in the db before notification

            if qtoken:
                publisher = PrintPublisher()
                publisher.notify_for_queue(dbname, qtoken, job_queues)

        return True
