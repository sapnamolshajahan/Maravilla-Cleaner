# -*- coding: utf-8 -*-
import os
import hashlib
import logging

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

expires_in = "rest_api.access_token_expires_in"


def get_random_token(length=40, prefix="access_token"):
    random_bytes = os.urandom(length)
    return "{prefix}_{random_bytes}".format(prefix=prefix, random_bytes=str(hashlib.sha1(random_bytes).hexdigest()))


class APIAccessToken(models.Model):
    _name = "api.access_token"
    _order = "expires desc"

    ######################################################
    # Default and compute methods
    ######################################################
    @api.depends('expires')
    def _get_expired(self):
        for token in self:
            expiry_dt = fields.Datetime.context_timestamp(token, fields.Datetime.from_string(token.expires))
            now_dt = fields.Datetime.context_timestamp(token, datetime.now())
            token.is_expired = expiry_dt < now_dt

    ######################################################
    # Fields
    ######################################################
    token = fields.Char("Access Token", required=True, readonly=True)
    user = fields.Many2one("res.users", string="User", required=True, readonly=True)
    company = fields.Many2one("res.company", string="Company")
    expires = fields.Datetime("Expires", required=True)
    is_expired = fields.Boolean(string='Expired', compute='_get_expired')

    ######################################################
    # Methods
    ######################################################
    def find_one_or_create_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        found_tokens = self.env["api.access_token"].sudo().search([
            ("user", "=", user_id)
        ], order="id desc")

        if found_tokens:
            valid_tokens = [t.token for t in found_tokens if (not t.is_expired and t.is_valid())]

            if valid_tokens:
                return valid_tokens, None

        if create:
            expires = datetime.now() + timedelta(seconds=int(self.env.ref(expires_in).sudo().value))
            user = self.env['res.users'].sudo().browse(user_id)

            new_access_token = self.env["api.access_token"].sudo().create({
                "user": user_id,
                "company": self.env.company.id,
                "expires": expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": get_random_token(),
            })

            return [new_access_token.token], new_access_token.company.id

        return [], None

    def is_valid(self):
        """
        Checks if the access token is valid.
        """
        self.ensure_one()
        return not self.is_expired

    def button_revoke_access_token(self):
        self.expires = fields.Datetime.now()
