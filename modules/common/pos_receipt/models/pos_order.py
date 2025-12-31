# -*- coding: utf-8 -*-
import logging

from odoo import models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = ["pos.order", "remote.print.mixin"]

    @api.model
    def get_pos_receipt_report(self):
        """
        Override as required for custom reports
        :return: ir.actions.report record
        """
        return self.env.ref("pos_receipt.pos_receipt_report")

    def button_print_to_queue(self):
        """
        Print the POS Receipt to configured queue
        :return:
        """
        self.ensure_one()

        if not self.config_id.pos_receipt_queue:
            raise UserError(f"No POS Receipt Queue configured for {self.config_id.name}")

        self.print_pos_receipt()
        return True

    def print_pos_receipt(self):
        """
        Print the Till-docket for the POS Order.
        :return:
        """
        for pos_order in self:
            queue = pos_order.config_id.pos_receipt_queue
            if not queue:
                _logger.info(f"ignored pos={pos_order.name}, no receipt queue config={pos_order.config_id.name}")
                continue

            report = pos_order.get_pos_receipt_report()
            result, _format = report._render(report, [pos_order.id])
            if type(result) == str:
                result = result.encode()
            if not self.lp_command(queue.name, result):
                _logger.warning(f"failed print: receipt={pos_order.name}, report={report.name}, queue={queue}")
