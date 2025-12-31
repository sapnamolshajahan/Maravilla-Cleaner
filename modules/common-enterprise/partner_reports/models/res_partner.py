# -*- coding: utf-8 -*-
from odoo import fields, models
from ..models.email_doctype import STATEMENT_TYPE


class ResPartnerDocs(models.Model):
    _inherit = 'res.partner'

    ###########################################################################
    # Default & Compute methods
    ###########################################################################
    def _get_partner_statement_email(self):
        for partner in self:
            docs = partner.email_documents
            statements_docs = docs.filtered(lambda x: x.email_doc_type.name == STATEMENT_TYPE and not x.disabled)

            if statements_docs:
                partner.partner_statement_email = ','.join([x.email for x in statements_docs])
            else:
                partner.partner_statement_email = ''

    ###########################################################################
    # Fields
    ###########################################################################
    partner_statement_email = fields.Char(string="Email", compute="_get_partner_statement_email")
