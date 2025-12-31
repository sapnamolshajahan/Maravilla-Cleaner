# -*- coding: utf-8 -*-
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

EXPIRED_QUEUE_AFTER = 2  # days


class JobQueue(models.Model):
    """
    Printer Queues characteristics
    """
    _name = "remote.print.mqtt.job.queue"
    _description = __doc__
    _sql_constraints = [
        ('name_hostname_uniq', 'unique (name, hostname)', "Queue and Hostname combination must be unqiue"),
    ]

    ##################################################################################
    # Fields
    ##################################################################################
    name = fields.Char("Queue Name", required=True)
    hostname = fields.Char("Host Name", required=True)
    topic = fields.Char("Queue Topic", required=True)
    public_key = fields.Text("Public Key", required=True)
    write_date = fields.Datetime("Last Updated On", readonly=True)

    ##################################################################################
    # Fields
    ##################################################################################
    @api.model
    def valid_queues(self, name):
        """
        Return list of queues with given name.

        :param name:
        :return:
        """
        return self.search([("name", "=", name)])

    @api.model
    def update_queue(self, hostname, queue, topic, key):
        """
        Update or add an entry
        """
        q = self.search(
            [
                ("name", "=", queue),
                ("hostname", "=", hostname),
            ])
        if q:
            q.write(
                {
                    "topic": topic,
                    "public_key": key,
                })
        else:
            q = self.create(
                [{
                    "name": queue,
                    "hostname": hostname,
                    "topic": topic,
                    "public_key": key,
                }])

        # Clean out dead queues while we're here
        cutoff = fields.Datetime.now() - relativedelta(days=EXPIRED_QUEUE_AFTER)
        self.search([("write_date", "<", cutoff)]).unlink()

        return q
