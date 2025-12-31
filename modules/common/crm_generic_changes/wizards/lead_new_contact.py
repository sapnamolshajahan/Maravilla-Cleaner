# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LeadNewContact(models.TransientModel):
    """
    Add New Contact to Lead
    """

    _name = "crm.lead.new.partner"
    _description = __doc__

    ################################################################################
    # Fields
    ################################################################################
    lead = fields.Many2one("crm.lead", required=True, ondelete="cascade")
    name = fields.Char("Name")
    position = fields.Char("Job Position")
    email = fields.Char("Email")
    mobile = fields.Char("Mobile")
    phone = fields.Char("Phone")

    ################################################################################
    # Methods
    ################################################################################
    @api.model
    def construct(self, lead):
        return self.create(
            [{
                "lead": lead.id,
            }])

    def action_save_close(self):
        self.create_partner()
        return {"type": "ir.actions.act_window_close"}

    def action_save_another(self):
        self.create_partner()
        self.write(
            {
                "name": False,
                "position": False,
                "email": False,
                "mobile": False,
                "phone": False,
            })
        return {
            "name": self._description,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": self._name,
            "res_id": self.id,
            "target": "new",
        }

    def create_partner(self):
        """
        Create a new person, possibly linked to the company; as the primary contact

        :return: res.partner
        """

        values = {
            "name": self.name,
            "function": self.position,
            "email": self.email,
            "mobile": self.mobile,
            "phone": self.phone,
        }
        if self.lead.partner_id.is_company:
            values["parent_id"] = self.lead.partner_id.id

        if self.lead.contact_ids:
            lowest_sequence = min([c.lead_contact_sequence for c in self.lead.contact_ids])
            if lowest_sequence:
                values["lead_contact_sequence"] = lowest_sequence
                for contact in self.lead.contact_ids:
                    contact.write({"lead_contact_sequence": contact.lead_contact_sequence + 1})
        else:
            values["lead_contact_sequence"] = 1

        partner = self.env["res.partner"].create([values])
        self.lead.write(
            {
                "contact_ids": [(4, partner.id, 0)]
            })
        return partner
