# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import fields, api, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def _get_partner(self):
        """
        if a linked record then try and get the partner
        """
        for r in self:
            partner = None
            if r.res_model_id and r.res_id:
                model_name = r.res_model_id.model
                related_record = self.env[model_name].search([("id", "=", r.res_id)])
                if related_record:
                    for f in ("partner_id", "partner"):
                        if hasattr(related_record, f):
                            partner = related_record[f]
                            break
            r.partner_id = partner

    ###########################################################################
    # Fields
    ###########################################################################
    date = fields.Date("Create date", default=lambda self: fields.Date.context_today(self), required=True)
    date_done = fields.Date("Date Completed", store=False, compute=None)
    priority = fields.Selection([
        ("0", "Low"),
        ("1", "Normal"),
        ("2", "High"),
    ], string="Priority", default="0")
    status = fields.Selection([
        ("open", "Open"),
        ("cancel", "Cancelled"),
        ("closed", "Done")], "Status", default="open")
    partner_id = fields.Many2one("res.partner", compute="_get_partner", string="Partner", store=True)
    category_id = fields.Many2one("crm.phonecall.category", string="Category")
    opportunity_id = fields.Many2one("crm.lead", string="Lead/Opportunity")
    
    ###########################################################################
    # Model methods
    ###########################################################################
    def write(self, vals):
        if "date" not in vals:
            vals["date"] = datetime.now()
        return super(MailActivity, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(MailActivity, self).create(vals)
        res["date"] = datetime.now()
        return res

    def action_done(self):
        """
        Override of standard Odoo. Standard odoo deletes the record after creating a message.
        We want to keep the activity record as the log of activity
        """
        for rec in self:
            rec.write(
                {
                    "status": "closed",
                    "date_done": datetime.now()
                })
        return {"type": "ir.actions.act_window_close"}


class MailMixin(models.AbstractModel):
    """
    Extend to respect status field on mail.activity
    """
    _inherit = "mail.activity.mixin"

    # Ignore activities that have been marked as completed
    activity_ids = fields.One2many(domain=[("status", "not in", ("cancel", "closed"))])
