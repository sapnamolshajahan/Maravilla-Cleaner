# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    account_analytic = fields.Many2one(comodel_name='account.analytic.account', string='Project')
    projects = fields.Many2one(comodel_name='project.project', string='Actual Project')

    @api.onchange('account_analytic')
    def onchange_account_analytic(self):
        if self.account_analytic:
            project = self.env['project.project'].search([('account_id','=', self.account_analytic.id)])
            if project:
                self.projects = project[0].id


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def _calc_purchases(self):
        for record in self:
            if record.purchase_orders:
                record.purchase_orders_count = len(record.purchase_orders)
            else:
                record.purchase_orders_count = 0

    purchase_orders = fields.One2many('purchase.order', 'projects', string='Purchase Orders')
    purchase_orders_count = fields.Integer(string='Purchase Count', compute='_calc_purchases')

    def action_view_po(self):
        self.ensure_one()
        if not self.purchase_orders:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('No Purchase Orders'),
                    'message': _('There are no purchase orders in this project'),
                }
            }
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "name": "Purchase Order",
            "views": [[False, "list"], [False, "form"]],
            "context": {"create": False},
            "domain": [["id", "in", [x.id for x in self.purchase_orders]]],
        }
        if len(self.purchase_orders) == 1:
            action_window["views"] = [[False, "form"]]
            action_window["res_id"] = self.purchase_orders[0].id

        return action_window


    def action_create_po(self):
        if not self.partner_id:
            raise UserError('You must set a partner first')
        input_values={
            'partner_id':self.partner_id.id,
            'account_analytic':self.account_id.id,
            'projects': self.id
        }
        order = self.env['purchase.order'].create(input_values)
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "name": "Purchase Order",
            "views": [[False, "form"]],
            "context": {},
            "res_id": order.id,
        }


