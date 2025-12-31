# -*- coding: utf-8 -*-
from odoo import api, models


class Picking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        """
        Intercept to send out packing slips, if configured.
        :return:
        """
        result = super(Picking, self)._action_done()

        if self.picking_type_code == "outgoing" and self.state == 'done':
            partner = self.partner_id.parent_id or self.partner_id
            self.env["email.async.send"].send("packing_slip", self.ids, partner.id)

        return result

    def email_doc_report(self):
        """
        Return the report-name to use for Packing Slips.

        Override to provide customer-specific report-names.
        :return:
        """
        self.ensure_one()
        return self.get_delivery_report()
