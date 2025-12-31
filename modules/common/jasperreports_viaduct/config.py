# -*- coding: utf-8 -*-
import socket

from odoo.addons.base_generic_changes.utils.config import configuration
from odoo.tools import config

SECTION_NAME = "jasperreports_viaduct"
KEY_ODOO = "odoo"
KEY_VIADUCT = "viaduct"

#
# Sensible Defaults
#
DEFAULT_VIADUCT_URL = "http://localhost:8080"

#
# CONFIG_* is exportable
#
CONFIG_DB_HOST = config.get("db_host") or "localhost"
CONFIG_DB_PORT = int(config.get("db_port", "5432") or "5432")
CONFIG_DB_USER = config.get("db_user", "unspecified")
CONFIG_DB_PASSWORD = config.get("db_password", "")
CONFIG_VIADUCT_URL = DEFAULT_VIADUCT_URL
CONFIG_ODOO_URL = f"http://{socket.getfqdn()}:{config.get('http_port')}"

if SECTION_NAME in configuration:
    section = configuration[SECTION_NAME]

    CONFIG_VIADUCT_URL = section.get(KEY_VIADUCT, DEFAULT_VIADUCT_URL)
    if KEY_ODOO in section:
        CONFIG_ODOO_URL = section.get(KEY_ODOO)
