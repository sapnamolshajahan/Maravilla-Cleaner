# -*- coding: utf-8 -*-
from odoo import models, fields


class Partner(models.Model):
    """
    Introduce invoice display address
    """
    _inherit = "res.partner"



    def invoice_display_address(self):
        """
        Get the res.partner record for the invoice address.

        Precedence for address is:
            - invoice
            - self

        :return: address record
        """
        addr_type = ["invoice"]

        addresses = self.address_get(addr_type)
        for t in addr_type:
            if t in addresses and addresses[t] != self.id:
                return self.browse([addresses[t]])

        return self  # default
