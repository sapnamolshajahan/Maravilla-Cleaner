# -*- coding: utf-8 -*-
from odoo import models

from .purchase_order import CONTEXT_EMAIL_PRICED


class ActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def update_viaduct_data(self, res_ids, data):
        """
        Apply priced-parameter to report if present.
        """
        result = super(ActionsReport, self).update_viaduct_data(res_ids, data)

        if CONTEXT_EMAIL_PRICED in self.env.context:
            email_data = {
                "viaduct-parameters": {
                    "priced": self.env.context[CONTEXT_EMAIL_PRICED],
                }
            }
            if result:
                result.update(email_data)
            else:
                result = email_data

        return result
