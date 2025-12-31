# -*- coding: utf-8 -*-
from odoo import models, fields


class CRMProspect(models.TransientModel):
    """ Update CRM partner binding to allow creating a prospect. """

    _inherit = "crm.lead2opportunity.partner"

    prospect = fields.Boolean(string="Create as Prospect Only")



    def _convert_handle_partner(self, lead, action, partner_id):
        """
        Extend parent behaviour to set partner type to prospect if required.

        Returns:
            The result of the super call.
        """
        super(CRMProspect, self)._convert_handle_partner(lead, action, partner_id)

        if self.prospect and self.lead_id and self.lead_id.partner_id:
            self.lead_id.partner_id.write(
                {
                    "prospect": True,
                })
