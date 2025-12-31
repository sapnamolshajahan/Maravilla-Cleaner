# -*- coding: utf-8 -*-
import string
import random
from odoo import api, fields, models


class MailTemplateManagementExtension(models.Model):
    _inherit = 'mail.template'

    _sql_constraints = [
        ('unique_id', 'UNIQUE (unique_id)', 'Must be unique')]

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    ###########################################################################
    # Fields
    ###########################################################################
    unique_id = fields.Char(
        string='Unique ID', readonly=True,
        help='Unique text identifier generated from template name, cannot be changed, '
             'used for referencing template from the code'
    )
    body_text = fields.Html(
        string='Body text',
        help='Text part of email template, without any design applied;'
             ' although basic HTML tags (bullet points, bold font) are ok, as well as {object} like template variables'
    )

    design_template = fields.Many2one(
        comodel_name='mail.template.design',
        string='Design Template',
        help='This is a design-rich HTML template that could be re-used '
    )

    ###########################################################################
    # Model methods
    ###########################################################################
    @api.model
    def create(self, values):
        if isinstance(values, list):
            for val in values:
                self.populate_unique_id(val)
        else:
            self.populate_unique_id(values)
        return super(MailTemplateManagementExtension, self).create(values)

    @api.model
    def populate_unique_id(self, values):
        """
        Unique ID gets generated upon creation only, cannot be changed later
        :param values: dict() with values for creating a new object
        """
        if not values.get('name'):
            return

        values['unique_id'] = values['name'].replace(' ', '_').lower() + '_' + self.id_generator()

    @api.model
    def id_generator(self, size=10):
        chars = string.ascii_lowercase + string.digits
        unique_id = ''.join(random.choice(chars) for _ in range(size))

        # Avoid duplicated unique IDs
        if self.search([('unique_id', '=', unique_id)]):
            return self.id_generator()
        else:
            return unique_id

    def merge_content_and_design(self):
        for template in self:

            if not template.design_template:
                continue

            html = template.design_template.body or ""
            body_text = template.body_text or ""

            # Ensure both are strings
            html_with_content = html.replace("{text_content}", body_text)
            template.write({"body_html": html_with_content})
