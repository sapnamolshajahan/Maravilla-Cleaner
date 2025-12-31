# -*- coding: utf-8 -*-
import logging

from odoo import models
from .sale import CONTEXT_DISABLE

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "remote.print.mixin"]

    def _action_done(self):
        """
        Intercept workflow to put reports onto the task-queue
        :return:
        """
        res = super(StockPicking, self)._action_done()
        if not self.env.context.get(CONTEXT_DISABLE, False):  # inherited modules may choose to disable
            self.queue_packing_report()
        return res

    def queue_packing_report(self):

        for picking in self:

            if not picking.allow_packing_print():
                continue

            if picking.partner_id.disable_auto_packing_slip:
                _logger.debug(f"Packing print skipped: disabled for partner={picking.partner_id.display_name}")
                continue

            parent =  picking.partner_id.parent_id
            if parent:
                if picking.partner_id.parent_id.disable_auto_packing_slip:
                    _logger.debug(f"Packing skipped: Disabled for parent partner {parent.display_name}")
                    continue

            packing_printer = picking.picking_type_id.warehouse_id.packing_printer
            if not packing_printer:
                _logger.debug(f"ignored: no packing printer for warehouse={picking.picking_type_id.warehouse_id.name}")
                continue

            picking.with_delay(
                channel=self.light_job_channel(),
                description=f"Packing Slip Auto-Print {picking.name}",
            ).print_report_job(picking.get_delivery_report().id, packing_printer)

    def queue_picking_report(self):
        for picking in self:

            if not picking.allow_picking_print():
                continue

            picking_printer = picking.picking_type_id.warehouse_id.picking_printer
            if not picking_printer:
                _logger.debug(f"ignored: no picking printer for warehouse={picking.picking_type_id.warehouse_id.name}")
                continue

            picking.with_delay(
                channel=self.light_job_channel(),
                description=f"Picking List Auto-Print {picking.name}",
            ).print_report_job(picking.get_picking_report().id, picking_printer)

    def print_report_job(self, report_id, printer):
        """
        Print the stock.picking report to specified printer.
        Expected to be invoked as a queue_job.
        """
        report_model = self.env["ir.actions.report"]
        report = report_model.browse(report_id)
        result, _format = report_model._render_qweb_pdf(report, self.ids)
        if self.lp_command(printer, result):
            _logger.debug(f"printed picking={self.name}, report={report.name}, printer={printer}")

    def allow_picking_print(self):
        """
        Allow inherited modules to override
        """
        return self.state not in ("cancel", "done")

    def allow_packing_print(self):
        """
        Allow inherited modules to override
        """
        return self.picking_type_id.code != "incoming" and self.state == "done"
