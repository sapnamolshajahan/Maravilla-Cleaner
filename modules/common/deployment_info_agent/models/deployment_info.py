# -*- coding: utf-8 -*-
import json
import logging
import os

import requests
from requests.exceptions import ConnectionError

import odoo.release
from odoo import api, fields, models
from odoo.addons.base_generic_changes.utils.config import configuration

CONFIG_SECTION = "deployment-info-agent"
ENTRY_ENDPOINT = "endpoint"
ENTRY_KEY = "key"
ENTRY_TAG = "tag"

_logger = logging.getLogger(__name__)


class DeploymentInfo(models.AbstractModel):
    """
    Deployment Info Agent
    """
    _name = "deployment.info.agent"
    _description = __doc__.strip()

    @api.model
    def send_info(self):
        """
        Send deployment information to collector.
        """
        if CONFIG_SECTION not in configuration:
            _logger.debug(f"[{CONFIG_SECTION}] section not present in rc file")
            return

        section = configuration[CONFIG_SECTION]
        for k in (ENTRY_ENDPOINT, ENTRY_KEY, ENTRY_TAG):
            if k not in section:
                _logger.warning(f"[{CONFIG_SECTION}] section requires '{k}' entry")
                return

        endpoint = section.get(ENTRY_ENDPOINT)
        key = section.get(ENTRY_KEY)
        tag = section.get(ENTRY_TAG)

        data = {
            "key": key,
            "tag": tag,
            "source": "odoo",
            "version": odoo.release.version,
            "release": self.get_release(),
            "installed_modules": self.get_installed_modules(),
            "database-name": self.env.cr.dbname,
            "database-expiry": self.get_db_expiry(),
        }

        try:
            _logger.debug(f"post={data}")
            response = requests.post(
                endpoint, data=json.dumps(data),
                headers={"Content-Type": "application/json"})
            _logger.info(f"endpoint={endpoint}, response={response.text}")

        except ConnectionError as e:
            _logger.warning(f"failure on endpoint={endpoint}, exception={e}")

    def get_release(self):

        paths = os.getcwd().split("/")
        return paths[-1]

    def get_installed_modules(self):
        modules = self.env["ir.module.module"].search([("state", "=", "installed")])
        return [{
            "name": m.name,
            "author": m.author,
        } for m in modules]

    def get_db_expiry(self):

        date_string = self.env["ir.config_parameter"].get_param("database.expiration_date")
        if not date_string:
            return ""
        return date_string

    @api.model
    def schedule_send_info(self):
        """
        Make sure send_info is invoked on server startup
        :return:
        """
        cron = self.env.ref("deployment_info_agent.deployment_info_agent_cron")
        cron.nextcall = fields.Datetime.now()
