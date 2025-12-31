# -*- coding: utf-8 -*-
import datetime
import logging

from odoo import SUPERUSER_ID
from odoo.api import Environment
from odoo.http import Controller, route
from odoo.http import request
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

SERVICE_URL = "/jasperreports-viaduct/"
EPOCH = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, datetime.UTC)

T_UNKNOWN = "unknown"
T_INT = "int"
T_FLOAT = "float"
T_STRING = "string"
T_DATE = "date"
T_DATETIME = "datetime"
T_IMAGE = "image"


class IncomingHelperRequest(Controller):

    @route(SERVICE_URL + "<dbname>", type="json", auth="none", csrf=False)
    def handler(self, dbname, session, method, identifier, arguments):
        """
        These are requests coming in from the Java webapp.

        The session, method, identifier and arguments are unpacked from
        the POST against the URL.
        """
        env = request.env
        if env.cr.dbname == dbname:
            return self._handle_it(env, session, method, identifier, arguments)

        with Registry.new(dbname).cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            return self._handle_it(env, session, method, identifier, arguments)

    def _handle_it(self, env, session, method, identifier, arguments):

        result = {}
        tzname = "UTC"
        helper = env["viaduct.session"].sudo().create_session_helper(session)
        if helper:
            if hasattr(helper, method):
                fn = getattr(helper, method)
                if arguments:
                    result = fn(identifier, *arguments)
                else:
                    result = fn(identifier)
            else:
                _logger.warning("no helper-method={0}".format(method))
            if "tz" in helper.env.context:
                tzname = helper.env.context["tz"]

        return self.cook(result, tzname)

    @staticmethod
    def cook(values, tzname):
        """
        Cook the raw results into type+value.
        """
        cooked = {}
        for k, v in values.items():

            # Pre-converted?
            if isinstance(v, dict):
                cooked[k] = v
                continue

            # Inspection required
            vtype = T_UNKNOWN
            if isinstance(v, int):
                vtype = T_INT
            elif isinstance(v, float):
                vtype = T_FLOAT
            elif isinstance(v, str):
                vtype = T_STRING
            elif isinstance(v, datetime.datetime):
                vtype = T_DATETIME
                secs = int((v.astimezone(datetime.UTC) - EPOCH).total_seconds())
                v = f"{secs}:{tzname}"
            elif isinstance(v, datetime.date):
                vtype = T_DATE
                v = str(v)

            cooked[k] = {
                "type": vtype,
                "value": v,
            }
        return cooked
