# -*- coding: utf-8 -*-

from odoo import models,fields, tools, api


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    def get_count(self):
        for record in self:
            if record.purchases:
                record.purchase_count = len(record.purchases)
            else:
                record.purchase_count = 0

    purchases = fields.One2many('purchase.order', 'crm_lead', string='Purchases')
    purchase_count = fields.Integer(string='Purchase Count', compute='get_count')

    def action_view_purchases(self):
        self.ensure_one()
        if not self.purchases:
            action_window = {
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "name": "Purchases",
                "views": [[False, "form"]],
                "context": {"create": True, "opportunity": self.id},
            }
            return action_window
        else:
            action_window = {
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "name": "Purchases",
                "views": [[False, "list"], [False, "form"]],
                "context": {"create": True, "opportunity": self.id},
                "domain": [["id", "in", [x.id for x in self.purchases]]],
            }
            if len(self.purchases) == 1:
                action_window["views"] = [[False, "form"]]
                action_window["res_id"] = self.purchases[0].id

        return action_window

