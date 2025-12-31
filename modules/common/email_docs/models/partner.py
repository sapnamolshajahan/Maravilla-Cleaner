# -*- coding: utf-8 -*-
from odoo import models, fields


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_invoice_email_address(self):
        for record in self:
            docs = record.email_documents
            if docs.filtered(lambda x: x.email_doc_type in ['invoice', 'credit-note'] and not x.disabled):
                record.invoice_email_address = ','.join(
                    [x.email for x in docs.filtered(
                        lambda x: x.email_doc_type in ['invoice', 'credit-note'] and not x.disabled)])
            else:
                record.invoice_email_address = record.email

    ###########################################################################
    # Fields
    ###########################################################################
    email_documents = fields.One2many("partner.document.email", "partner", string="Document Recipients")
    invoice_email_address = fields.Char(string='Invoice Email Address', compute='_get_invoice_email_address')

    def has_doctype(self, doc_type):
        """
        Does the partner have an email (possibly default) configured for the doc-type?
        """
        for d in self.email_documents:
            if d.email_doc_type.name != doc_type:
                continue
            if not d.email_doc_type.enabled:
                return False
            if d.disabled:
                return False
            if d.email:
                return True
        return True if self.email else False

    def action_bulk_customer_invoice_wizard(self):
        """
        Bring up wizard for bulk customer invoice mailouts
        :return:
        """
        wizard = self.env["bulk.customer.invoice.dispatch"].build_wizard(self)
        return {
            "name": wizard._description,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "target": "new",
        }
