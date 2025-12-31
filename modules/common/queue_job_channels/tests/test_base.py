# -*- coding: utf-8 -*-
import logging
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('common', 'queue_job_channels')
class TestQueueJobChannels(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create mock queue job channels
        self.light_channel = self.env["queue.job.channel"].create({
            "name": "light",
            "parent_id": self.env.ref("queue_job.channel_root").id,
            "removal_interval": 30,
        })

        self.heavy_channel = self.env["queue.job.channel"].create({
            "name": "heavy",
            "parent_id": self.env.ref("queue_job.channel_root").id,
            "removal_interval": 30,
        })

    def test_light_job_channel(self):
        """Test if light job channel is retrieved correctly"""
        channel_name = self.env["base"]._named_job_channel("queue_job_channels.light_job_channel")
        self.assertEqual(channel_name, "root.light", "Light job channel name mismatch!")

    def test_heavy_job_channel(self):
        """Test if heavy job channel is retrieved correctly"""
        channel_name = self.env["base"]._named_job_channel("queue_job_channels.heavy_job_channel")
        self.assertEqual(channel_name, "root.heavy", "Heavy job channel name mismatch!")
