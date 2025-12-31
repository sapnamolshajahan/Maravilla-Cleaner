# -*- coding: utf-8 -*-
from odoo import api, models

STATEMENT_SEQ = 50
STATEMENT_TYPE = "partner-statement"
STATEMENT_DESC = "Partner Statement"


class EmailDocType(models.Model):
    """
    Introduce partner-statement type. It's not used in
    any workflow related triggers though.
    """
    _inherit = "email.doc.type"

    @api.model
    def _name_selection_list(self):
        """
        Extend to include statement-type
        """
        vals = super(EmailDocType, self)._name_selection_list()
        vals.append((STATEMENT_SEQ, STATEMENT_TYPE, STATEMENT_DESC))
        return vals

    ###########################################################################
    # Fields
    ###########################################################################

    def get_description(self, name):
        if name == STATEMENT_TYPE:
            return STATEMENT_DESC
        return super(EmailDocType, self).get_description(name)
