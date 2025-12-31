# -*- coding: utf-8 -*-
import importlib
from odoo.tests.common import TransactionCase, tagged
from unittest.mock import patch
import odoo.addons.site_ribbon.models.ribbon_backend as site_ribbon_backend


@tagged('common', 'site_ribbon')
class TestSiteRibbon(TransactionCase):
    def setUp(self):
        super(TestSiteRibbon, self).setUp()
        self.ribbon_model = self.env["site.ribbon.backend"]

    @patch("odoo.tools.config.get_misc")
    def test_get_display_data_with_config(self, mock_get_misc):
        """
        Test get_display_data method when config values are set.
        """
        mock_get_misc.side_effect = lambda section, key, default=None: {
            "name": "Test Environment",
            "colour": "#FFFFFF",
            "background": "rgba(0,255,0,.6)",
        }.get(key, default)
        importlib.reload(site_ribbon_backend)
        expected_data = {
            "name": "Test Environment",
            "color": "#FFFFFF",
            "background_color": "rgba(0,255,0,.6)",
        }
        display_data = self.ribbon_model.get_display_data()
        self.assertEqual(display_data, expected_data)

    @patch("odoo.tools.config.get_misc")
    def test_get_display_data_without_config(self, mock_get_misc):
        """
        Test get_display_data method when no config values are set.
        """
        mock_get_misc.side_effect = lambda section, key, default=None: None if key == "name" else default
        importlib.reload(site_ribbon_backend)
        expected_data = {
            "name": None,
            "color": None,
            "background_color": None,
        }
        display_data = self.ribbon_model.get_display_data()
        self.assertEqual(display_data, expected_data)
