Configured Sessions with Redis
==============================

Leverage camptocamp's `session_redis <https://github.com/camptocamp/odoo-cloud-platform>`_ to
use configuration file entries instead of environment variables.

Configuration
-------------

To enable, simply include a ``session_redis_rcd`` section in the Configuration File::

    [session_redis_rcd]
    # default - localhost
    host =
    # default - 6379
    port =
    password =
    # use "prefix" when using a shared redis instance
    prefix =
    # time in seconds before expiration of sessions (default is 7 days)
    expiration =
    # time in seconds before expiration of anonymous sessions (default is 3 hours)
    anon_expiration =
    # enable SSL True/False (default is False)
    ssl =
    # SSL Certificate file (default is None)
    ssl_certfile =
    # SSL Key file (default is None)
    ssl_keyfile =
    # SSL Certificate Authorities (default is None)
    ssl_ca_certs =

