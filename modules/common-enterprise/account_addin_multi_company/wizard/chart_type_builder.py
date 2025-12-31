# -*- coding: utf-8 -*-
from odoo.addons.account_addin_financial_reporting.wizard.chart_type_builder import ProfitLossBuilder


class MCProfitLossBuilder(ProfitLossBuilder):

    def _dig_child_companies(self, company_id, id_set):

        id_set.add(company_id)
        children = self.env["res.company"].search([("parent_id", "=", company_id)])
        for child in children:
            self._dig_child_companies(child.id, id_set)

    def get_companies(self):
        """
        Override to include subsidiaries
        """
        company_ids = super(MCProfitLossBuilder, self).get_companies()
        child_set = set()
        for company_id in company_ids:
            self._dig_child_companies(company_id, child_set)
        return company_ids.extend(list(child_set))

    def multi_company_hook(self, acid_items, page):

        if not page.company_ids:
            return acid_items

        acid_items = super(MCProfitLossBuilder, self).multi_company_hook(acid_items, page)
        if page.all_subsidiaries:
            id_set = set()
            for company in page.company_ids:
                self._dig_child_companies(company, id_set)
        else:
            id_set = set([x.id for x in page.company_ids])

        revised_acid_items = []
        for item in acid_items:
            if self.env['account.account'].browse(item.acid).company_id.id in id_set:
                revised_acid_items.append(item)
        return revised_acid_items
