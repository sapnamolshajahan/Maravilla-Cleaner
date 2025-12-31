# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from .client import RemoteProxyClient
from .exceptions import IllegalOperation, WhatTheHeck

_logger = logging.getLogger(__name__)


class RemoteModel(models.AbstractModel):
    """
    Remote Proxy Models should inherit from this class and define odoo.fields that are in use.
    """
    _name = "remote.model"  # placeholder name; must be defined in sub-classes
    _remote_name = None  # name of model on the remote end, may be prefixed with classes, eg: remote2:product.product

    # The 4 essential attributes defining the class
    _auto = False
    _register = False
    _abstract = True
    _transient = False

    # implicit required field
    id = fields.Id()

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """
        Delegate to remote proxy
        """
        proxy = RemoteProxyClient()
        result = proxy.search(self, args, offset, limit, order)
        return len(result) if count else result

    def _read(self, fields):
        """
        In the odoo/models.py, this method populates the cache with data from the database;
        override this to delegate to the remote proxy.

        When updating code between versions, this method _must_ be reviewed against odoo/models.py:read()
        """

        def cook_raw(raw):
            """
            Remassage the json results from remote-proxy/read
            """
            cooked = {}
            for k, v in raw.items():
                cooked[int(k)] = v
            return cooked

        #
        # Copy prelim code from models.py _read()
        #
        if not self:
            return
        self.check_access_rights("read")

        field_names = []
        inherited_field_names = []
        for name in fields:
            field = self._fields.get(name)
            if field:
                if field.store:
                    field_names.append(name)
                elif field.base_field.store:
                    inherited_field_names.append(name)
            else:
                _logger.warning("%s.read() with unknown field '%s'", self._name, name)

        # determine the fields that are stored as columns in tables; ignore 'id'
        fields_pre = [
            field
            for field in (self._fields[name] for name in field_names + inherited_field_names)
            if field.name != "id"
            if field.base_field.store and field.base_field.column_type
            if not (field.inherited and callable(field.base_field.translate))
        ]

        proxy = RemoteProxyClient()
        results = cook_raw(proxy.read(self, fields))
        if results:
            ids = [k for k in results.keys()]
            fetched = self.browse(ids)
            for field in fields_pre:
                values = tuple([results[r_id][field.name] for r_id in ids])
                # store values in cache
                self.env.cache.update(fetched, field, values)

            # determine the fields that must be processed now;
            # for the sake of simplicity, we ignore inherited fields
            for name in field_names:
                field = self._fields[name]
                if not field.column_type:
                    self._field_read(field, fetched, results)
        else:
            fetched = self.browse()

        # possibly raise exception for the records that could not be read
        missing = self - fetched
        if missing:
            raise WhatTheHeck("remote missing records")

    def _field_read(self, field, records, values):
        """
        Populate One2many, Many2many
        """
        if field.type in ("one2many", "many2many"):
            cache = records.env.cache
            for record in records:
                field_value = values[record.id][field.name]
                cache.set(record, field, tuple(field_value))
        else:
            raise WhatTheHeck("unsupported field type={}".format(field.type))

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals_list):
        """
        No.
        """
        raise IllegalOperation("create() is not permitted")

    def unlink(self):
        """
        No.
        """
        raise IllegalOperation("unlink() is not permitted")

    def write(self, vals):
        """
        No.
        """
        raise IllegalOperation("write() is not permitted")
