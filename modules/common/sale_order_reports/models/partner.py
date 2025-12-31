# -*- coding: utf-8 -*-
from odoo import fields, models


class Partner(models.Model):
    """
    Introduce "sales" type for optional sales address.
    """
    _inherit = "res.partner"

    ##################################################################################
    # Fields
    ##################################################################################
    type = fields.Selection(selection_add=[("sales", "Sales Display Address")])

    def sales_display_address(self):
        """
        Get the res.partner record for the sales address.

        Precedence for address is:
            - sales
            - invoice
            - self

        :return: address record
        """
        addr_type = ["sales", "invoice"]

        addresses = self.address_get(addr_type)
        for t in addr_type:
            if t in addresses and addresses[t] != self.id:
                return self.browse([addresses[t]])

        return self  # default
