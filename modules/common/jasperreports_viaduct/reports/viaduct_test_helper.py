# -*- coding: utf-8 -*-
from datetime import date

from odoo import fields
from ..viaduct_helper import ViaductHelper


class ViaductTestHelper(ViaductHelper):

    def company(self, company_id):
        result = {}

        company_model = self.env["res.company"]
        company = company_model.browse(company_id)

        result["name"] = company.name
        result["logo-path"] = self.image_path(company, "logo")
        result["none"] = None
        result["float"] = 1.0
        result["date"] = date.today()  # UTC date
        result["now"] = fields.Datetime.now()  # UTC time

        return result
