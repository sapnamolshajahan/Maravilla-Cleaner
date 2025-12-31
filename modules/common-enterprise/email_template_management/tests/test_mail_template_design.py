# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestMailTemplateDesign(TransactionCase):

    def setUp(self):
        super().setUp()
        self.design_model = self.env['mail.template.design']
        self.template_model = self.env['mail.template']

    def test_render_templates(self):
        # Step 1: Create design template
        design = self.design_model.create({
            'name': 'Simple Design',
            'body': '<html><body><h1>Header</h1><div>{text_content}</div></body></html>',
        })

        # Step 2: Create mail template that uses this design
        template = self.template_model.create({
            'name': 'Welcome Email',
            'subject': 'Welcome!',
            'body_text': '<p>Hello {object.name}</p>',
            'design_template': design.id,
        })

        # Step 3: Render the template using render_templates
        design.render_templates()

        # Step 4: Check result
        self.assertIn('<div><p>Hello {object.name}</p></div>', template.body_html)
        self.assertIn('<h1>Header</h1>', template.body_html)
