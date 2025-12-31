# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, api


_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def cron_handle_negative_quants(self):
        # We only interested in internal locations
        internal_location_ids = self.env["stock.location"].search([("usage", "=", "internal")]).ids

        quants_to_process = self.search([
            ("lot_id", "=", False),  # Ignore negative quants with lots
            ("location_id", "in", internal_location_ids),
            ("quantity", "<", 0),
        ])
        _logger.info(f"Number of quants with negative quantity to process: {len(quants_to_process)}")

        for negative_quant in quants_to_process:
            positive_quants = self.search([
                ("location_id", "=", negative_quant.location_id.id),
                ("quantity", ">", 0),
                ("product_id", "=", negative_quant.product_id.id),
                ("lot_id", "=", False)
            ], order="write_date")

            if not positive_quants:
                continue

            remaining_qty = abs(negative_quant.quantity)
            _logger.info(f"Qty to eliminate for {negative_quant} is {negative_quant.quantity} from {positive_quants}")

            for positive_quant in positive_quants:
                if not remaining_qty:
                    break

                qty_in_this_round = abs(positive_quant.quantity)
                _logger.info(f"Quantity to process for {negative_quant} is {qty_in_this_round} from {positive_quant}")

                if qty_in_this_round > remaining_qty:
                    positive_quant.quantity -= remaining_qty
                    remaining_qty = 0

                else:
                    positive_quant.quantity = 0
                    remaining_qty -= qty_in_this_round

            negative_quant.quantity = -remaining_qty
            _logger.info(f"Remaining qty after cleanup for {negative_quant} is {negative_quant.quantity}")
