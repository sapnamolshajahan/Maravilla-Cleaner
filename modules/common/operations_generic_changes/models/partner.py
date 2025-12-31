# -*- coding: utf-8 -*-
from odoo import models


class Partner(models.Model):
    """
    Introduce invoice display address
    """
    _inherit = "res.partner"

    def delivery_display_address(self):
        """
        Get the res.partner record for the delivery address.

        Precedence for address is:
            - delivery
            - self

        :return: address record
        """
        addr_type = ["delivery"]

        addresses = self.address_get(addr_type)
        for t in addr_type:
            if t in addresses and addresses[t] != self.id:
                return self.browse([addresses[t]])

        return self  # default
