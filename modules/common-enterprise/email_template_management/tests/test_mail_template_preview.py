# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestMailTemplatePreview(TransactionCase):

    def setUp(self):
        super().setUp()
        self.template_model = self.env['mail.template']
        self.design_model = self.env['mail.template.design']
        self.preview_model = self.env['mail.template.preview']

    def test_preview_triggers_merge(self):
        design = self.design_model.create({
            'name': 'Design A',
            'body': '<html><body><h1>Header</h1>{text_content}</body></html>',
        })

        mail_template = self.template_model.create({
            'name': 'Test Email',
            'subject': 'Subject',
            'body_text': '<p>Hello {object.name}</p>',
            'design_template': design.id,
            'model_id': self.env['ir.model']._get_id('res.users'),
        })

        self.preview_model.with_context(template_id=mail_template.id).create({
            'mail_template_id': mail_template.id,
        })

        self.assertIn('<h1>Header</h1>', mail_template.body_html)
        self.assertIn('<p>Hello {object.name}</p>', mail_template.body_html)
