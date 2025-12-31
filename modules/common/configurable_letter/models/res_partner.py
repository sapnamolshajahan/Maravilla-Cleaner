# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def button_letter_to_contact(self):
        self.ensure_one()

        wizard = self.env['letter.template.report.wizard'].create({
            'record_id': self.id,
            'partner_id': self.id,
            'model_name': self._name,
            'use_generic_email_template': True,
            'report_name': 'configurable_letter.letter_to_contact_generic_report_viaduct',
            'email_template_name': 'registry_generic_letter_to_contact_email',
        })

        return {
            "name": "Create Letter",
            "res_model": "letter.template.report.wizard",
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
            "context": {"model_name": self._name, "title": "Letter"}
        }

    def prepare_address_string_for_letters(self, addr_str):
        # Some clean up for bad address cases
        # With more than 2 missing address lines
        while '\n \n' in addr_str:
            addr_str = addr_str.replace('\n \n', '\n')

        # Replace empty lines when two lines in a row missing data
        while '\n\n' in addr_str:
            addr_str = addr_str.replace('\n\n', '\n')

        # Use html like line break
        address = addr_str.replace('\n', '<br>')

        # Requirement: show country only if it's not New Zealand
        if '<br>New Zealand' in address:
            address = address.replace('<br>New Zealand', '')

        if self.name:
            address = f"{self.name}<br>{address}"

        return address

    def prepare_header_for_letters(self):
        # Get address string
        addr_str = self._display_address(without_company=True)

        # Prepare elements for letter header
        prepared_address = self.prepare_address_string_for_letters(addr_str)

        return prepared_address + '<br>'
