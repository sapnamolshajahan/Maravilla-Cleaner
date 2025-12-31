# -*- coding: utf-8 -*-
from odoo.addons.base_generic_changes.utils.config import configuration

PROTOCOL_VERSION = "2"  # increment for every protocol change, pleae

SECTION_NAME = "remote_print_mqtt"
KEY_BROKER = "broker"
KEY_TOPIC_BASE = "topic_base"
KEY_PUBLIC_KEYS = "remote_public_keys"
KEY_LP_CMD = "lp_command"

DEFAULT_LP_CMD = "lp -d {queue} -n {copies} {path}"

BROKER = configuration.get(SECTION_NAME, KEY_BROKER, fallback="")
TOPIC_BASE = configuration.get(SECTION_NAME, KEY_TOPIC_BASE, fallback="")
REMOTE_PUBLIC_KEYS = configuration.get(SECTION_NAME, KEY_PUBLIC_KEYS, fallback="").split()
LP_CMD = configuration.get(SECTION_NAME, KEY_LP_CMD, fallback=DEFAULT_LP_CMD)
