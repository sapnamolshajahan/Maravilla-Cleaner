# -*- coding: utf-8 -*-
from odoo import api, models


class StockPicking(models.Model):
    """
    Stock picking extension for picking list report.
    """
    _inherit = "stock.picking"

    @api.model
    def get_delivery_report(self):
        """
        Sub-modules should override as required.

        :return: ir.actions.report
        """
        # this version will print priced or unpriced depending on the partner's packing_slip_pricing field
        return self.env.ref("operations_packing_slip_reports.standard_packing_viaduct")

    def do_print_delivery(self):
        """
        Print packing slip, invoked from "Print" menu dropdown.
        """
        report = self.get_delivery_report()
        # Re-Force active_ids
        context = dict(self.env.context)
        context["active_ids"] = self.ids

        return {
            "type": "ir.actions.report",
            "report_name": report.report_name,
            "report_type": report.report_type,
            "report_file": report.report_file,
            "name": report.name,
            "context": context,
        }
