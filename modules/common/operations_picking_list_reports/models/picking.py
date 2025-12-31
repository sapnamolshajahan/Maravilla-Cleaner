# -*- coding: utf-8 -*-
from odoo import models


class StockPicking(models.Model):
    """
    Stock picking extension for picking list report.
    """
    _inherit = "stock.picking"

    ##################################################################################
    # Methods
    ##################################################################################
    def get_picking_report(self):
        """
        Sub-modules should override as required.
        :return: ir.actions.report record, picking report to use.
        """
        return self.env.ref("operations_picking_list_reports.standard_picking_viaduct")

    def _get_picking_list_extra_report_data(self):
        return {}

    def action_print_picking(self):
        """
        Print picking list, invoked from "Print" menu dropdown.
        """
        report = self.get_picking_report()
        data = self._get_picking_list_extra_report_data()
        return report.report_action(self.ids, data=data)
