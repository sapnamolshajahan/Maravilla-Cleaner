# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MassMailContact(models.Model):
    _inherit = 'mailing.contact'

    ###########################################################################
    # Default & compute methods
    ###########################################################################

    ###########################################################################
    # Fields
    ###########################################################################
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')

    ###########################################################################
    # Methods
    ###########################################################################
    def _message_get_default_recipients(self):
        return dict((record.id, {
            'partner_ids': record.partner_id.ids,
            'email_to': record.email,
            'email_cc': False
        }) for record in self)
