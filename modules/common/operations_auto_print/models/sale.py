# -*- coding: utf-8 -*-
import logging

from odoo import models

CONTEXT_DISABLE = "operations_auto_print.disable"

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        """
        Confirm order and trigger picking auto-print
        """
        existing_pickings = set(self.picking_ids.ids)
        res = super(SaleOrder, self).action_confirm()
        if not self.env.context.get(CONTEXT_DISABLE, False):  # inherited modules may choose to disable
            picks_to_print = self.picking_ids.filtered(lambda r: r.id not in existing_pickings)
            picks_to_print.queue_picking_report()
        return res
