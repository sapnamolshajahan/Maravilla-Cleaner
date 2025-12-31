# -*- coding: utf-8 -*-
from odoo import fields, models
from .company import PURCHASE_PRINT_OPTIONS


class Partner(models.Model):
    """
    Introduce "purchase" type for optional purchase address.
    Precedence for address is:
        - purchase
        - invoice
        - company
    """
    _inherit = "res.partner"

    ##################################################################################
    # Field Computations
    ##################################################################################
    def _default_price_option(self):
        return self.env.company.purchase_report_pricing

    ##################################################################################
    # Fields
    ##################################################################################
    type = fields.Selection(selection_add=[("purchase", "Purchase Display Address")])
    purchase_report_pricing = fields.Selection(PURCHASE_PRINT_OPTIONS, string="Purchase Report Price Display",
                                               default=_default_price_option)

    ##################################################################################
    # Business Methods
    ##################################################################################
    def purchase_display_address(self):
        """
        Get the res.partner record for the Purchase Address.

        Precedence for address is:
            - sales
            - invoice
            - self

        :return: address record
        """
        addr_type = ["purchase", "invoice"]

        addresses = self.address_get(addr_type)
        for t in addr_type:
            if t in addresses and addresses[t] != self.id:
                return self.browse([addresses[t]])

        return self  # default
