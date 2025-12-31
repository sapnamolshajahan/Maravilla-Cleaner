# -*- coding: utf-8 -*-
from odoo.addons.base_generic_changes.utils.config import configuration

SECTION_NAME = "label_printer"
KEY_COMMAND = "print"

#
# CONFIG_* is exportable
#
CONFIG_PRINT = configuration.get(SECTION_NAME, KEY_COMMAND, fallback="lp")
