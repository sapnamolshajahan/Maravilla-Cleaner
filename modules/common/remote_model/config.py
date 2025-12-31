# -*- coding: utf-8 -*-
from cryptography.hazmat.primitives import serialization

from odoo.addons.base_generic_changes.utils.config import configuration

SECTION_NAME = "remote_model"
KEY_URL = "remote_url"
KEY_DBNAME = "remote_dbname"
CONFIG_ACCEPT_KEYS = "accept_public_keys"
CONFIG_PRIVATE_KEY = "private_key"

PRIVATE_KEY_PATH = configuration.get(SECTION_NAME, CONFIG_PRIVATE_KEY)
PUBLIC_KEY_PATHS = configuration.get(SECTION_NAME, CONFIG_ACCEPT_KEYS).split()

# Construct Private key, if any
PRIVATE_KEY = None
if PRIVATE_KEY_PATH:
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        PRIVATE_KEY = serialization.load_pem_private_key(key_file.read(), None)

# Construct Public keys, if any
PUBLIC_KEYS = []
for key_path in PUBLIC_KEY_PATHS:
    with open(key_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read(), None)
        PUBLIC_KEYS.append(
            {
                "path": key_path,
                "key": public_key,
            })
