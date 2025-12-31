# -*- coding: utf-8 -*-
import logging

from odoo.api import Environment
from odoo.exceptions import UserError
from odoo.modules.registry import Registry
from .controllers.viaduct_service import T_IMAGE

_logger = logging.getLogger(__name__)


class ViaductHelper(object):
    """
        JasperReports Helpers that can be invoked from within JasperReports.
        Reports are expected to subclass and implement helper methods.

        @param env: std Odoo env
        @param ids: list of int values.
        @param parameters: parameters handed to the viaduct report.
    """

    def __init__(self, env, session, report, ids, parameters):
        self.session = session
        self.env = env
        self.report = report
        self.ids = ids
        self.parameters = parameters

    def example_method(self, int_value):
        """
            Helper methods that can be invoked from Jasper Reports will
            have the following parameters:

            @param int_value: (int)
                (int) generic value, usually an id-value
            @param optional-args: additional optional arguments.

            @return:
                Dictionary of values.
        """
        return {}

    def _2localtime(self, v):
        """
        Convert a datetime value to local time for serialization.

        Not really required from Odoo17 onwards.
        """
        _logger.debug("ViaductHelper:_2localtime() is deprecated")
        if not v:
            return None
        return v

    def _format_timestamp(self, dt, date_only=False):
        """ Formats a time stamp to the correct format for the language.

            Args:
                dt: a datetime object
                date_only: If True, use a date format only
                    (exclude the time component).
        """
        lang = self.env.context.get("lang", "en_US")
        res_lang_model = self.env["res.lang"]
        res_lang = res_lang_model.search([("code", "=", lang)])
        if not res_lang.ids:
            raise UserError("Unable to get Language to convert datetimes")

        if date_only:
            format_string = "{date_format}"
        else:
            format_string = "{date_format} {time_format}"
        return dt.strftime(format_string.format(
            date_format=res_lang.date_format,
            time_format=res_lang.time_format))

    @staticmethod
    def append_non_null(result, key, str2, sep="\n"):
        """
        Standard helper to append strings.
        """
        if not str2:
            return
        if key in result and result[key].strip():
            result[key] += sep + str2
        else:
            result[key] = str2

    def image_path(self, record, field):
        """
        Return a "cooked" type+value for the image.

        :param record:
        :param field:
        """
        with Registry.new(self.env.cr.dbname).cursor() as cr:
            env = Environment(cr, self.env.uid, self.env.context)
            session_image = env["viaduct.session.image"].construct(self.session, record, field)
            return {
                "type": T_IMAGE,
                "value": session_image.id,
            }
