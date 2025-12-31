# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LetterToPractitionerReport(models.TransientModel):
    _name = 'letter.template.report.wizard'
    _description = 'Generic wizard to create letter template'

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    @api.onchange('template_ids')
    def onchange_template_ids(self):
        for wizard in self:
            if wizard.template_ids:
                wizard.title = wizard.template_ids[-1].name  # -1 as we want to keep name as the first one selected

    @api.depends('record_id', 'model_name')
    def _get_reference(self):
        self.ensure_one()
        if self.record_id and self.model_name:
            record = self.env[self.model_name].browse(self.record_id)

            ref = ''

            if hasattr(record, 'name'):
                ref += record.name

            self.reference = ref

    ###########################################################################
    # Fields
    ###########################################################################

    # Since record can be for different models, just specify ID and model name to browse if we need an object
    record_id = fields.Integer(string="Record ID")
    model_name = fields.Char(string="Model Name")
    reference = fields.Char(string='Reference', compute='_get_reference')

    # Email and report names needed for pointing out the wizard to the correct report/email template
    # Module name will have to find the expected template
    module_name = fields.Char(string="Module Name")
    email_template_name = fields.Char(string='Email template name')
    use_generic_email_template = fields.Boolean(string='Use generic email template')
    report_name = fields.Char(string="Report Name")

    # Partner could be practitioner or normal partner, depending on report. Always res.partner
    # third_party_name could be used when letter generated should have references to another person (char name)
    partner_id = fields.Many2one(comodel_name='res.partner', string="Partner")
    third_party_name = fields.Char(string='3rd party name')

    # Select one of multiple templates available
    template_ids = fields.Many2many(comodel_name='letter.template', string="Template")

    # Signature and from_email are prepopulated from the current user
    signature = fields.Html(string='Signature', default=lambda self: self.env.user.signature or '')
    signature_required = fields.Boolean(string='Signature required', default=True)
    from_email = fields.Char(string='From Email', default=lambda self: self.env.user.email)

    # Body to be constructed from templates selected + signature
    title = fields.Char(string='Title')
    body = fields.Html(string='Letter Body')

    # Specify other render type if needed (for example, docx if needed a Word document)
    render_type = fields.Selection(selection=[('pdf', 'PDF'), ('docx', 'Word')], string='Render type', default='pdf')

    ###########################################################################
    # Model methods
    ###########################################################################
    def generate_template(self):
        u"""
        Construct body from all templates specified + signature
        :return: same wizard with generated body field
        """
        if len(self) > 1:
            raise UserError(_('You can only process a single report at a time.'))

        record_text = ''

        for template in self.template_ids:
            record_text += template.text or ""
            record_text += '\n\n'

        if self.signature_required and self.signature:
            record_text += '\n\n'
            record_text += self.signature

        # Clean text a bit and save a body
        if record_text:
            self.body = self.clean_body(record_text + '\n')

        return {
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    def message_get_reply_to(self, ids, default=None):
        """
        Override to get the reply_to of the parent project.
        """
        wizards = self.browse(ids)
        return {wizard.id: self.env.user.email for wizard in wizards}

    def button_create_report(self):
        self.env.cr.commit()
        if len(self) > 1:
            raise UserError(_('You can only process a single report at a time.'))

        # Make sure font size is ok
        self.format_font_size()

        data = {
            'ids': self.ids,
            'id': self.id,
            'viaduct-parameters': {'body': self.body},
            'output-type': self.render_type,
        }

        return {
            'name': '{0}-{1}-{2}'.format(self._name, self.record_id, self.report_name),
            'type': 'ir.actions.report',
            'report_name': self.report_name,
            'report_type': 'qweb-pdf',
            'data': data
        }

    def button_send_by_email(self):
        self.env.cr.commit()

        # Make sure font size is ok
        self.format_font_size()

        ir_model_data = self.env['ir.model.data']
        try:
            if self.use_generic_email_template:
                template_id = ir_model_data.check_object_reference('configurable_letter', self.email_template_name)[1]
            else:
                template_id = ir_model_data.check_object_reference(self.module_name, self.email_template_name)[1]
        except (ValueError, IndexError) as e:
            _logger.error(e)
            template_id = False

        try:
            compose_form_id = ir_model_data.check_object_reference('mail', self.email_template_name)[1]
        except (ValueError, IndexError):
            compose_form_id = False

        ctx = dict(self.env.context or {})
        ctx.update({
            'original_model': self.model_name,
            'original_res_id': self.record_id,
            'default_model': self._name,
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'render_type': self.render_type,
            'output-type': self.render_type,
            'mail_notify_user_signature': False,
        })

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.model
    def clean_body(self, body_text):
        return body_text.replace('style="font-family: inherit;', '')

    def format_font_size(self):
        self.ensure_one()
        for n in range(25):

            if n == 10:
                continue
            if self.body:
                if 'font-size: {num}px'.format(num=n) in self.body:
                    self.body = self.body.replace('font-size: {num}px'.format(num=n), 'font-size: 9px')
