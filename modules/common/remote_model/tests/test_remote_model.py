# -*- coding: utf-8 -*-

from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, tagged
from ..client import RemoteProxyClient


@tagged('common', 'remote_model')
class TestRemoteProxyClient(TransactionCase):

    def setUp(self):
        super().setUp()
        self.client = RemoteProxyClient()

        # Create some dummy records to test .read()
        DummyModel = self.env['dummy.model']
        self.records = DummyModel.create([
            {'name': 'Alpha'},
            {'name': 'Beta'},
        ])

        # Patch config.get_misc
        self.get_misc_patch = patch("odoo.tools.config.get_misc", side_effect=self.mock_get_misc)
        self.get_misc_patch.start()

        # Patch PRIVATE_KEY for signature generation
        fake_key = self._fake_private_key()
        self.private_key_patch = patch("odoo.addons.remote_model.client.PRIVATE_KEY", new=fake_key)
        self.private_key_patch.start()

    def tearDown(self):
        self.get_misc_patch.stop()
        self.private_key_patch.stop()

    def mock_get_misc(self, section, key, default=None):
        return {
            "remote_url": "http://testserver",
            "remote_dbname": "test_db",
            "private_key": "mocked_path",
            "accept_public_keys": "mocked_path",
        }.get(key, default)

    def _fake_private_key(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        return rsa.generate_private_key(public_exponent=65537, key_size=2048)


    @patch("odoo.addons.remote_model.client.requests.post")
    def test_read_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {
            "result": {
                self.records[0].id: {"name": self.records[0].name},
                self.records[1].id: {"name": self.records[1].name},
            }
        })
