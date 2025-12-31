# -*- coding: utf-8 -*-
import logging

from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from ..utils.serial_numbers import numeric_decompose

_logger = logging.getLogger(__name__)


class StockInventoryProduct(models.Model):
    _name = "stocktake.data.entry.line"

    def _compute_serialised(self):
        for r in self:
            r.serialised = r.product_id.tracking == "serial"

    @api.depends('stocktake_id')
    def get_control(self):
        for record in self:
            record.stocktake_data_entry_control = record.stocktake_id.stocktake_data_entry_control_id or False

    ###########################################################################
    # Fields
    ###########################################################################
    stocktake_id = fields.Many2one("stocktake.data.entry", string="Stocktake", ondelete="cascade")
    stocktake_data_entry_control = fields.Many2one('stocktake.data.entry.control', string='Control', compute='get_control', store=True)
    name = fields.Char(string="Name")
    product_id = fields.Many2one("product.product", string="Product", required=True,
                                 domain="[('type', '!=', 'service')]")
    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure")
    serialised = fields.Boolean("Serial item", compute="_compute_serialised")
    production_lot_id = fields.Many2one("stock.lot", string="Production Lot")
    end_production_lot = fields.Many2one("stock.lot", string="End Production Lot",
                                         help="Ending serial number for serial-batches")

    def validate_serial_range(self, start, finish, quantity):
        """
        Attempt to validate the quantity against the start and finish items.
        :param start: production-lot start, assumed non-null
        :param finish:
        :param quantity: can assume >= 1
        :return:
        """
        # edge-cases
        if quantity == 1:
            return not finish or start == finish
        if quantity > 1 and not finish:
            return False

        start_x = numeric_decompose(start.name)
        finish_x = numeric_decompose(finish.name)
        if len(start_x) != len(finish_x):
            _logger.warning("Serial number patterning failure: start={} ({}), end={} ({})".format(
                start.name, len(start_x),
                finish.name, len(finish_x)))
            return False

        if not start_x:
            _logger.warning("No numeric sections found in serial number {}".format(start.name))
            return False

        # use the last numeric section for serial number computation
        n = len(start_x) - 1
        computed = finish_x[n] - start_x[n] + 1
        if quantity != computed:
            _logger.debug("computed={}, quantity={}".format(computed, quantity))
            return False

        return True

    @api.constrains("product_id", "quantity", "production_lot_id", "end_production_lot")
    def validate_line(self):
        for r in self:
            if r.quantity < 0:
                raise ValidationError("Product '{}' quantity invalid".format(r.product_id.name))

            # Serialised product checks
            if r.product_id.tracking == "none":
                continue
            if r.production_lot_id and r.end_production_lot and \
                    (not self.validate_serial_range(r.production_lot_id, r.end_production_lot, r.quantity)):
                raise ValidationError(
                    "Product '{}' quantity and production-lot range do not match".format(r.product_id.name))

    @api.onchange("product_id")
    def onchange_product(self):
        self.serialised = self.product_id.tracking == "serial"

    @api.onchange("quantity", "production_lot_id", "end_production_lot")
    def onchange_serialise(self):

        if not self.product_id or not self.serialised:
            return {}

        if not self.quantity or self.quantity < 0:
            return {
                "warning": {
                    "title": "Quantity Reset",
                    "message": "Serialised product quantity has been set to minimum",
                },
                "value": {
                    "quantity": 1,
                }
            }
        if self.quantity and self.production_lot_id and self.end_production_lot:
            if not self.validate_serial_range(self.production_lot_id, self.end_production_lot, self.quantity):
                return {
                    "warning": {
                        "title": "Serial Number Range Mismatch",
                        "message": "The quantity and the production-lot range does not match",
                    },
                }
        return {}
