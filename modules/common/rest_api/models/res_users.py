# -*- coding: utf-8 -*-
import uuid
import logging

from werkzeug.exceptions import Unauthorized

from odoo import models, fields, api
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)


class APIAuthTokenUser(models.Model):
    _inherit = "res.users"

    api_auth_token = fields.Char("API Auth Token", readonly=True)
    token_ids = fields.One2many(comodel_name="api.access_token", inverse_name="user", string="Access Tokens")

    def button_generate_api_auth_token(self):
        new_uuid = uuid.uuid4()

        if any(self.search([('api_auth_token', '=', new_uuid)])):
            return self.button_generate_api_auth_token()

        self.api_auth_token = new_uuid

    @api.model
    def get_user_by_auth_token(self, token, raise_on_failure=True):
        """
        :param token: uuid str() to look for users linked to it
        :param raise_on_failure: pass as False to avoid request abort with an error
        :returns res.users object if token is valid
        :raises Unauthorized if token is invalid (i.e. not found) and raise_on_failure is True
        """
        existing_user = self.sudo().search([('api_auth_token', '=', token)])

        if not existing_user:
            if raise_on_failure:
                _logger.error('Token {} is invalid'.format(token))
                raise Unauthorized(_('Token is invalid'))

            return False

        return existing_user
