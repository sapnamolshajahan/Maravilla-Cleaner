# -*- coding: utf-8 -*-
import json
import logging
from unittest.mock import patch, MagicMock
import requests
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import config

_logger = logging.getLogger(__name__)



@tagged('common', 'deployment_info_agent')
class TestDeploymentInfo(TransactionCase):
    def setUp(self):
        super(TestDeploymentInfo, self).setUp()
        self.deployment_info = self.env["deployment.info.agent"]

        # Mock config parameters
        self.endpoint = "http://test-endpoint.com"
        self.key = "test-key"
        self.tag = "test-tag"

        config.misc.setdefault("deployment-info-agent", {})
        config.misc["deployment-info-agent"]["endpoint"] = self.endpoint
        config.misc["deployment-info-agent"]["key"] = self.key
        config.misc["deployment-info-agent"]["tag"] = self.tag

    def test_get_release(self):
        """
        Test that get_release returns a valid string.
        """
        release = self.deployment_info.get_release()
        self.assertIsInstance(release, str)
        _logger.info(f"Test get_release: {release}")

    def test_get_installed_modules(self):
        """
        Test that get_installed_modules returns a list.
        """
        modules = self.deployment_info.get_installed_modules()
        self.assertIsInstance(modules, list)
        if modules:
            self.assertIn("name", modules[0])
            self.assertIn("author", modules[0])
        _logger.info(f"Test get_installed_modules: {modules}")

    def test_get_db_expiry(self):
        """
        Test that get_db_expiry correctly retrieves the expiration date.
        """
        self.env["ir.config_parameter"].set_param("database.expiration_date", "2025-12-31")
        expiry_date = self.deployment_info.get_db_expiry()
        self.assertEqual(expiry_date, "2025-12-31")

    @patch("odoo.addons.deployment_info_agent.models.deployment_info.requests.post")
    def test_send_info(self, mock_post):
        """
        Test send_info sends correct data.
        """
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "Success"
        mock_post.return_value = mock_response

        self.deployment_info.send_info()

        # Ensure requests.post was called with expected arguments
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        sent_data = json.loads(kwargs["data"])

        self.assertEqual(sent_data["key"], self.key)
        self.assertEqual(sent_data["tag"], self.tag)
        self.assertEqual(sent_data["source"], "odoo")
        self.assertIn("version", sent_data)
        self.assertIn("release", sent_data)
        self.assertIn("installed_modules", sent_data)
        self.assertIn("database-name", sent_data)
        self.assertIn("database-expiry", sent_data)

        _logger.info(f"Test send_info data: {sent_data}")

    @patch("odoo.addons.deployment_info_agent.models.deployment_info.requests.post")
    def test_send_info_connection_error(self, mock_post):
        """
        Test send_info handles connection errors gracefully.
        """
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        self.deployment_info.send_info()
        _logger.info("Test send_info connection error handled successfully.")
