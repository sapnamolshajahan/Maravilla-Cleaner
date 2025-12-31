# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ParterDocumentEmail(models.Model):
    """
    Emails to send documents to.
    """
    _name = "partner.document.email"
    _description = 'Partner Document Email'

    ###########################################################################
    # Fields
    ###########################################################################
    partner = fields.Many2one("res.partner", "Partner", required=True, ondelete="cascade")
    email_doc_type = fields.Many2one("email.doc.type", "Document Type", required=True, ondelete="cascade")
    email = fields.Char("Email", help="Use this email instead of the one on the Partner")
    disabled = fields.Boolean("Stop", help="Disable notifications for this operation")

    @api.onchange("disabled")
    def onchange_disabled(self):
        """
        Blank out email if disabled.
        """
        for r in self:
            if r.disabled:
                r.email = None
