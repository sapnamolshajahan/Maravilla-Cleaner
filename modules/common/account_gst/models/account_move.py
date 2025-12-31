# -*- coding: utf-8 -*-

import logging
from decimal import Decimal

from odoo import models, api, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def round_dp(self, value_to_round, number_of_decimals):
        if number_of_decimals and value_to_round:
            TWO_PLACES = Decimal(10) ** -number_of_decimals
            return float(Decimal(str(value_to_round)).quantize(TWO_PLACES))
        return False

    def action_post(self):
        for record in self:
            zero_rated = []
            if record.move_type in ['in_invoice', 'in_refund', 'out_invoice', 'out_refund']:
                tax_amount = 0.0
                for line in record.line_ids:
                    discount_amount = line.price_unit * (line.discount / 100) * line.quantity
                    line_value = line.quantity * line.price_unit - discount_amount
                    if line.tax_ids:
                        tax_rate = self.env['account.tax'].browse(line.tax_ids[0].id).amount / 100
                        if not tax_rate:
                            zero_rated.append(line.tax_ids[0])
                        if tax_rate > 100:  # handles case where line is tax only - such as duty charges on imports
                            tax_amount += line_value
                        elif line.tax_ids[0].price_include:
                            tax_amount += line_value * (tax_rate / (1 + tax_rate))
                        else:
                            tax_amount += line_value * tax_rate
                if record.amount_tax and  abs(record.amount_tax - tax_amount) > 0.10:
                    raise UserError("The calculated tax for this invoice is {tax_amount}. "
                                    "Please check the total tax".format(tax_amount=tax_amount))

        return super(AccountMove, self).action_post()

