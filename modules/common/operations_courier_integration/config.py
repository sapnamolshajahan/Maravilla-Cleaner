# -*- coding: utf-8 -*-
from odoo.addons.base_generic_changes.utils.config import configuration

SECTION_NAME = "operations_courier_integration"
KEY_LABEL_WIDTH = "label_width"

LABEL_WIDTH = int(configuration.get(SECTION_NAME, KEY_LABEL_WIDTH, fallback="0"))
