# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError



class TestMailTemplateManagementExtension(TransactionCase):

    def setUp(self):
        super().setUp()
        self.mail_template_model = self.env['mail.template']
        self.design_template_model = self.env['mail.template.design']

    def test_unique_id_generation(self):
        template = self.mail_template_model.create({
            'name': 'Welcome Email',
            'subject': 'Welcome',
            'body_text': '<p>Hello {object.name}, welcome!</p>',
        })
        self.assertTrue(template.unique_id)
        self.assertTrue(template.unique_id.startswith('welcome_email_'))


    def test_merge_content_and_design(self):
        # Create design template
        design = self.design_template_model.create({
            'name': 'Default Design',
            'body': '<html><body><div>{text_content}</div></body></html>',
        })

        # Create mail template with design
        template = self.mail_template_model.create({
            'name': 'Onboarding Email',
            'subject': 'Start here',
            'body_text': '<p>Welcome to our platform</p>',
            'design_template': design.id
        })

        # Run merge
        template.merge_content_and_design()

        self.assertIn('<div><p>Welcome to our platform</p></div>', template.body_html)
