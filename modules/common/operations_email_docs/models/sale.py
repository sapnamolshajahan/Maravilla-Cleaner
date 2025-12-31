# -*- coding: utf-8 -*-
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class SaleOrderEmailDocs (models.Model):

    _inherit = 'sale.order'

    def action_confirm(self):

        res = super(SaleOrderEmailDocs, self).action_confirm()

        for sale in self:
            self.env["email.async.send"].send("sale_order", sale.ids, sale.partner_id.id)

        return res


    def email_doc_report(self):
        """
        Return the report-name to use for Packing Slips.

        Override to provide customer-specific report-names.
        :return:
        """
        self.ensure_one()
        return self.get_sale_report()
