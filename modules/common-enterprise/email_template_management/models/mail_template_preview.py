# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MailTemplatePreviewExtension(models.TransientModel):
    _inherit = 'mail.template.preview'

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    @api.model
    def default_get(self, fields):
        result = super(MailTemplatePreviewExtension, self).default_get(fields)

        default_template = self.env.context.get('template_id') or self.env.context.get('default_mail_template_id')

        if default_template:
            template = self.env['mail.template'].browse(default_template)

            if template:
                template.merge_content_and_design()

        return result
