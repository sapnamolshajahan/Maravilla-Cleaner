# -*- coding: utf-8 -*-
import logging

import redis

import odoo.addons.session_redis.http as rd
from odoo import http
from odoo.addons.session_redis.session import RedisSessionStore
from odoo.addons.base_generic_changes.utils.config import configuration
from odoo.tools.config import config

SECTION_NAME = "session_redis_rcd"
ENTRY_HOST = "host"
ENTRY_PORT = "port"
ENTRY_PREFIX = "prefix"
ENTRY_PASSWORD = "password"
ENTRY_EXPIRE = "expiration"
ENTRY_EXPIRE_ANON = "anon_expiration"
ENTRY_SSL = "ssl"
ENTRY_SSL_CERT = "ssl_certfile"
ENTRY_SSL_KEY = "ssl_keyfile"
ENTRY_SSL_CA = "ssl_ca_certs"

_logger = logging.getLogger(__name__)

if SECTION_NAME in configuration:
    section = configuration[SECTION_NAME]

    rcd_host = section.get(ENTRY_HOST, "localhost")
    rcd_port = int(section.get(ENTRY_PORT, 6379))
    rcd_prefix = section.get(ENTRY_PREFIX)
    rcd_password = section.get(ENTRY_PASSWORD)
    rcd_expire = section.get(ENTRY_EXPIRE)
    rcd_expire_anon = section.get(ENTRY_EXPIRE_ANON)
    rcd_ssl = section.get(ENTRY_SSL, False)
    rcd_ssl_cert = section.get(ENTRY_SSL_CERT)
    rcd_ssl_key = section.get(ENTRY_SSL_KEY)
    rcd_ssl_ca = section.get(ENTRY_SSL_CA)

    redis_client = redis.Redis(host=rcd_host, port=rcd_port, password=rcd_password,
                               ssl=rcd_ssl,
                               ssl_certfile=rcd_ssl_cert, ssl_keyfile=rcd_ssl_key, ssl_ca_certs=rcd_ssl_ca,
                               socket_timeout=5, socket_connect_timeout=5)
    session_store = RedisSessionStore(
        redis=redis_client,
        prefix=rcd_prefix,
        expiration=rcd_expire,
        anon_expiration=rcd_expire_anon,
        session_class=http.Session)

    # Monkey patch the root session-store
    http.root.session_store = session_store

    rd.purge_fs_sessions(config.session_dir)  # clean the existing sessions on the file system

    _logger.debug(f"Sessions stored in redis[{rcd_host}:{rcd_port}], prefix={rcd_prefix or ''}")
