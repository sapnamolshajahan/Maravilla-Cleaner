Remote Model
============

Support data-querying between Odoo instances by using ORM-like
methods. For sanity's sake, only read-operations are supported;
no 'push' operations, only 'pull' operations are implemented.

Property fields (ie: company_dependent=True) are **NOT** supported.

Inter-instance communcation uses asymetric-encryption to determine access.

Configuration
-------------

A simple 2-way connection can be implemented by adding the following
into the configuration file::

    [options]
    ...
    # modules offering multi-db support
    server_wide_modules = base,web,remote_model

    [remote_model]
    remote_url = http://localhost:18069
    remote_dbname = dbname

    # private key used to sign outgoing queries
    private_key = /path/to/private/key

    # list of public keys allowed to query this instance
    accept_public_keys = /path/to/key1 /path/to/key2

In code,::

    from odoo.addons.remote_model import models
    ...
    class RemoteProduct(models.RemoteProxy):
        _name = "remote.product.template"
        _remote_name = "product.template"
        ...
        # Only mirror fields of interest from the remote schema
        default_code = fields.Char("Internal Reference")
        product_tmpl_id = fields.Many2one("remote.product.template", "Product Template")

Advanced Configuration
----------------------

The module also supports querying multiple remote instances. The
outgoing configuration entries is prefixed with $name_; eg::

    [options]
    ...
    # modules offering multi-db support
    server_wide_modules = base,web,remote_model

    [remote_model]
    remote1_remote_url = http://remote1:18069
    remote1_remote_dbname = remote1-db
    ...
    remote2_remote_url = http://remote2:18069
    remote2_remote_dbname = remote2-db

    # private key used to sign outgoing queries
    private_key = /path/to/private/key

In code, *_remote_name* needs to be prefixed with the appropriate $name, eg::

    class Remote1Product(models.RemoteProxy):
        _name = "remote1.product.template"
        _remote_name = "remote1:product.template"
        ...
        # Only mirror fields of interest from the remote schema
        default_code = fields.Char("Internal Reference")
        product_tmpl_id = fields.Many2one("remote.product.template", "Product Template")
        ...
    class Remote2Product(models.RemoteProxy):
        _name = "remote2.product.template"
        _remote_name = "remote2:product.template"
        ...

