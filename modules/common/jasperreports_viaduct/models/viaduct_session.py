# -*- coding: utf-8 -*-
import importlib
import logging

from odoo import api, fields, models
from odoo.api import Environment
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)


class ViaductSession(models.TransientModel):
    """
    Viaduct Sessions
    """
    _name = "viaduct.session"
    _description = __doc__

    ################################################################################
    # Fields
    ################################################################################
    create_uid = fields.Many2one("res.users", "Creator UID", required=True)
    report = fields.Many2one("ir.actions.report", required=True, ondelete="cascade")
    viaduct_report = fields.Many2one("viaduct.resource", required=True, ondelete="cascade")
    data = fields.Json("Session information")

    @api.model
    def construct(self, report, viaduct_report, ids, data):
        """

        """
        save_data = {
            "ids": ids,
            "data": data,
            "context": dict(self.env.context),
        }
        return self.create(
            [{
                "report": report.id,
                "viaduct_report": viaduct_report.id,
                "data": save_data,
            }])

    @api.model
    def create_session_helper(self, session_id):
        """
        Create a helper for the session, using saved data.

        New instances of the helper are created per request, because in a multi-worker system,
        the current worker-request may not be the originating request which started the report,
        nor even the same request from the last call; this means helpers can't be cached
        internally as a dictionary.
        """
        session = self.browse(session_id)

        ids = session.data["ids"]
        data = session.data["data"]
        context = session.data["context"]

        report = session.report
        if not report.viaduct_helper:
            raise Exception(f"missing viaduct_helper for report={report.name}")

        helper_env = Environment(self.env.cr, session.create_uid.id, context)
        class_components = report.viaduct_helper.strip().split(".")
        helper_module = importlib.import_module(".".join(class_components[:-1]))
        helper_class = getattr(helper_module, class_components[-1])
        helper = helper_class(helper_env, session, report, ids, data)
        _logger.debug(f"report={report.name}, viaduct-helper={type(helper).__name__}")

        return helper

    @api.model
    def cleanup(self, session_id):
        """
        Remove session manually.

        We require a new cursor, as the current db-session was created before the supplied
        viaduct.session was present, and is now out-of-sync.
        """
        with Registry.new(self.env.cr.dbname).cursor() as cr:
            env = Environment(cr, self.env.uid, {})
            env["viaduct.session"].browse(session_id).unlink()
