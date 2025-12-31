# -*- coding: utf-8 -*-
from odoo import api, models

PO_SEQ = 60
PO_TYPE = "purchase"
PO_DESC = "Purchase Order"


class EmailDocType(models.Model):
    """
    Introduce purchase order print type.
    """
    _inherit = "email.doc.type"

    @api.model
    def _name_selection_list(self):
        """
        Extend to include statement-type
        """
        vals = super(EmailDocType, self)._name_selection_list()
        vals.append((PO_SEQ, PO_TYPE, PO_DESC))
        return vals

    ###########################################################################
    # Fields
    ###########################################################################

    def get_description(self, name):
        if name == PO_TYPE:
            return PO_DESC
        return super(EmailDocType, self).get_description(name)
