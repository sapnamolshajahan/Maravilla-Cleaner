# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools import float_utils

import logging

_log = logging.getLogger(__name__)

CONTEXT_SALE_LINE_PRICE_ROUNDING = "operations_courier_integration.courier_line_price_rounding"


class SaleOrder(models.Model):
    _inherit = "sale.order"
    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    ################################################################################
    # Fields
    ################################################################################

    ################################################################################
    # Methods
    ################################################################################

    def _create_delivery_line(self, carrier, price_unit):
        """
        If Invoice policy on delivery method is real, Odoo keeps the sol price at 0 and add the price in the description
        This overrides this behaviour.
        :param carrier: As per super method
        :param price_unit: As per super method
        :return: new Sale Order Line
        """
        if carrier and not float_utils.float_is_zero(carrier.price_unit_rounding_digits, precision_digits=4):
            price_unit = float_utils.float_round(price_unit, precision_rounding=carrier.price_unit_rounding_digits)
            _log.info(f"_create_delivery_line - price unit for carrier: {carrier.name} rounded to: {price_unit}")

        sol = super(SaleOrder, self)._create_delivery_line(carrier, price_unit)
        if sol and price_unit != 0 and "Estimate" in sol.name and sol.price_unit == 0:
            sol.price_unit = price_unit
            start = sol.name.find(" (Estimated")
            sol.name = sol.name[:start]
        return sol


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    ################################################################################
    # Fields
    ################################################################################

    ################################################################################
    # Methods
    ################################################################################

    def write(self, values):
        # Do the price rounding for delivery lines.
        if self.env.context.get(CONTEXT_SALE_LINE_PRICE_ROUNDING) and "price_unit" in values:
            values["price_unit"] = float_utils.float_round(
                values["price_unit"], precision_rounding=self.env.context[CONTEXT_SALE_LINE_PRICE_ROUNDING]
            )

        return super(SaleOrderLine, self).write(values)
