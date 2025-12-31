# -*- coding: utf-8 -*-
import re

from markupsafe import Markup

from odoo import fields
from odoo.addons.jasperreports_viaduct.viaduct_helper import ViaductHelper


class GenericLettercontact(ViaductHelper):

    def partner(self, source_partner_id):
        ctx = dict(self.env.context, tz="Pacific/Auckland")
        partner = self.env["res.partner"].with_context(ctx).browse(source_partner_id)
        return {
            'name': partner.name,
            'email': partner.email,
            'address': self.get_address_header(partner),
            'current-date': self._2localtime(fields.Datetime.now())
        }

    def body(self, wizard_id):
        wizard = self.env['letter.template.report.wizard'].browse(wizard_id)

        body = wizard.body or ""

        if body:
            body = Markup(re.sub(r'</p>\s*<p>', '</p><p></p><p>', wizard.body))
            body = Markup(re.sub(r'</li></ul>', '</li></ul><br/>', wizard.body))

        return {
            'body': body,
            'logo': self.env.company.logo or "",
            'title': wizard.title or "",
            'footer-text': self.env.company.configurable_letter_footer_text or "",
        }

    @staticmethod
    def get_address_header(partner):
        return partner.prepare_header_for_letters()
