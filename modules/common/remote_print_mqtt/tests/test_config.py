# -*- coding: utf-8 -*-
from odoo.tests.common import tagged, TransactionCase
from ..config import KEY_BROKER, KEY_TOPIC_BASE, KEY_PUBLIC_KEYS, BROKER, TOPIC_BASE, REMOTE_PUBLIC_KEYS


@tagged("common", "remote_print_mqtt")
class ConfigTest(TransactionCase):

    def test_configured(self):
        self.assertTrue(BROKER, f"Expected non-empty {KEY_BROKER}")
        self.assertTrue(TOPIC_BASE, f"Expected non-empty {KEY_TOPIC_BASE}")
        self.assertTrue(REMOTE_PUBLIC_KEYS, f"Expected non-empty {KEY_PUBLIC_KEYS}")
