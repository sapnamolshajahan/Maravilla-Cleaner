# -*- coding: utf-8 -*-
import time

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


FIELD_NAMES = [
    'partner_id',
    'partner',
    'practitioner_id',
    'practitioner',
]


class MassMailList(models.TransientModel):
    _name = 'mass.mail.list'

    ##################################################################################################
    # Default & compute methods
    ##################################################################################################
    @api.depends('mailing_model_id')
    def _compute_model(self):
        for record in self:
            record.mailing_model_real = (
                        ((record.mailing_model_name != 'mail.mass_mailing.list') and record.mailing_model_name)
                        or 'mailing.contact')

    ##################################################################################################
    # Fields
    ##################################################################################################
    name = fields.Many2one(comodel_name='mailing.list', string='Mailing List', required=True)
    mailing_model_id = fields.Many2one('ir.model', string='Recipients Model', required=True)

    mailing_model_name = fields.Char(related='mailing_model_id.model', string='Recipients Model Name',
                                     readonly=True, related_sudo=True)

    mailing_domain = fields.Char(string='Domain')

    mailing_model_real = fields.Char(compute='_compute_model', string='Recipients Real Model',
                                     default='mail.mass_mailing.contact', required=True)

    model_id = fields.Many2one('ir.model', string='Related Document Model',
                               domain=[('transient', '=', False)])

    model = fields.Char(related='model_id.model', readonly=True)

    filter_id = fields.Many2one("ir.filters", string='Filter', ondelete='restrict',
                                domain="[('model_id', '=', mailing_model_name)]")

    ##################################################################################################
    # Functions
    ##################################################################################################
    @api.onchange('filter_id')
    def onchange_filter_id(self):
        for record in self:
            record.mailing_domain = record.filter_id.domain

    def _get_eval_context(self):
        """ Prepare the context used when evaluating python code
            :returns: dict -- evaluation context given to safe_eval
        """
        return {
            'uid': self.env.uid,
            'user': self.env.user,
        }

    def build_list(self):

        domain = safe_eval(self.mailing_domain, self._get_eval_context())
        selected_records = self.env[self.mailing_model_name].search(domain)
        selected_contacts = []

        if self.mailing_model_name == 'res.partner':
            for record in selected_records:
                if record not in selected_contacts:
                    selected_contacts.append(record)

            # Exclude EDM out out records
            selected_contacts = [contact for contact in selected_contacts if not contact.edm_opt_out]

        else:
            possible_fields = self.env['ir.model.fields'].search([
                ('model', '=', self.mailing_model_name),
                ('relation', '=', 'res.partner'), ('ttype', '=', 'many2one')
            ])

            for poss in possible_fields:
                for field_name in FIELD_NAMES:
                    if poss.name == field_name:
                        for record in selected_records:
                            if not hasattr(record, field_name):
                                continue
                            if getattr(record, field_name) not in selected_contacts:
                                selected_contacts.append(getattr(record, field_name))
                        break

            if selected_records and not selected_contacts:
                raise UserError('The model filter you have selected does not have a mapped partner value'
                                ' as a field so cannot be used')

        for partner in selected_contacts:
            if partner.email:
                self.env['mailing.contact'].create({
                    'name': partner.name,
                    'partner_id': partner.id,
                    'email': partner.email,
                    'list_ids': self.name.ids
                })

        return
