# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CRMStage(models.Model):
    _inherit = "crm.stage"

    type = fields.Selection(selection=[
        ("cancel", "Cancelled"),
        ("lost", "Lost"),
        ("won", "Won"),
    ], string="Type")


class CrmPhonecallCategory(models.Model):
    _name = "crm.phonecall.category"
    _description = "CRM Phonecall Category"

    ###########################################################################
    # Fields
    ###########################################################################
    active = fields.Boolean(string="Active")
    # since there is no crm.phoncall.category in odoo10 let's put fields here
    name = fields.Char('Name', required=True, translate=True)
    team_id = fields.Many2one('crm.team', 'Sales Team')


class CrmLead(models.Model):
    _inherit = "crm.lead"

    ###########################################################################
    # Field computations and defaults
    ###########################################################################
    @api.depends("contact_ids")
    def _primary_contact(self):
        """
        Show the Primary Contact
        :return:
        """
        for lead in self:
            if lead.contact_ids:
                for partner in lead.contact_ids.sorted("lead_contact_sequence"):
                    lead.primary_contact = partner
                    break
            else:
                lead.primary_contact = None

    ###########################################################################
    # Fields
    ###########################################################################
    mail_activity_ids = fields.One2many("mail.activity", "res_id", domain=[("res_model", "=", "crm.lead")],
                                        string="Mail Activities")
    primary_contact = fields.Many2one("res.partner", "Primary Contact", compute="_primary_contact")
    contact_ids = fields.Many2many("res.partner", "crm_lead_contacts_rel", "crm_lead_id", "contact_id",
                                   domain=[("is_company", "=", False)],
                                   string="Contacts")
    fax = fields.Char("Fax")
    mobile = fields.Char('Mobile', compute='_compute_mobile', readonly=False, store=True)


    ###########################################################################
    # Model methods
    ###########################################################################
    def _phone_get_number_fields(self):
        """
        For phone-validation.
        """
        result = super(CrmLead, self)._phone_get_number_fields()
        result.append("mobile")
        return result

    @api.depends('partner_id')
    def _compute_mobile(self):
        """ compute the new values when partner_id has changed """
        for lead in self:
            if not lead.mobile or lead.partner_id.mobile:
                lead.mobile = lead.partner_id.mobile

    def action_mail_activity(self):
        self.ensure_one()
        view_id = self.env.ref("mail.mail_activity_view_form_popup").id
        return {
            "name": "Log Activity",
            "view_mode": "form",
            "res_model": "mail.activity",
            "act_window_id": "crm_generic_changes.mail_activity_action_form",
            "view_id": view_id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {
                "default_opportunity_id": self.id if self.type == "opportunity" else False,
                "default_res_id": self.id,
                "default_res_model_id": self.env.ref("crm.model_crm_lead").id,
                "default_name": self.name,
            },
        }

    def action_add_contact(self):
        """
        Add a new contact, making it primary
        """
        wizard = self.env["crm.lead.new.partner"].construct(self)
        return {
            "name": wizard._description,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "target": "new",
        }

    def get_rainbowman_message(self):
        """This function doesn't really work -
        just creates crm.lead record doesn't exist on switching between stages on kanban views.

        Better to turn it off
        """
        return False
