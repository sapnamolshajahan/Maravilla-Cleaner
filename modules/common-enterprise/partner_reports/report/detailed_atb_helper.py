# -*- coding: utf-8 -*-
from odoo.addons.jasperreports_viaduct.viaduct_helper import ViaductHelper


class DetailedAtbHelper(ViaductHelper):

    def statement(self, statement_id):
        statement_pool = self.env["res.partner.statement"]
        statement = statement_pool.browse(statement_id)

        result = {}

        result["period"] = statement.as_at_date
        result["currency"] = statement.statement_currency.name

        return result
