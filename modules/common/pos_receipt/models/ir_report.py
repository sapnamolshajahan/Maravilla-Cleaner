# -*- coding: utf-8 -*-
import logging

from odoo import api, models
from odoo.addons.escpos_reports.escpos_report import ESCPOS_PROFILE

_logger = logging.getLogger(__name__)


class ReportActions(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def _render_qweb_text(self, report_ref, docids, data=None):
        """
        Inject ESCPOS profile into context if warranted
        """
        if self.is_escpos_report() and self.model == "pos.order" and ESCPOS_PROFILE not in self.env.context:

            # Pick the first non-empty escpos_profile to use, if any
            for pos_order in self.env["pos.order"].browse(docids):
                queue = pos_order.config_id.pos_receipt_queue
                if not queue:
                    _logger.warning(f"No receipt printer configured for {pos_order.config_id.name}")
                    continue

                escpos_context = dict(self.env.context)
                escpos_context[ESCPOS_PROFILE] = queue.escpos_profile
                return super(ReportActions, self.with_context(escpos_context))._render_qweb_text(report_ref, docids,
                                                                                                 data)

        return super(ReportActions, self)._render_qweb_text(report_ref, docids, data)
