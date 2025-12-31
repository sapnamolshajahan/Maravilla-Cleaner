# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('line_ids')
    def calc_analytic_account(self):
        for record in self:
            record.analytic_account_id = False
            for line in record.line_ids:
                if line.analytic_distribution:
                    distribution_json = line.analytic_distribution
                    account_ids = [int(account_id) for key in distribution_json.keys() for account_id in
                                   key.split(',')]
                    if account_ids:
                        for account in account_ids:
                            if account:
                                record.analytic_account_id = account
                                break

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          compute='calc_analytic_account', store=True)
    project_id = fields.Many2one('project.project', string='Project')

    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft=soft)
        for record in self:
            if record.project_id:
                break
            if record.line_ids.filtered(lambda x: x.analytic_distribution):
                lines = record.line_ids.filtered(lambda x: x.analytic_distribution)
                distribution_json = lines[0].analytic_distribution
                account_ids = [int(account_id) for key in distribution_json.keys() for account_id in
                               key.split(',')]
                for account_id in account_ids:
                    if account_id:
                        record.analytic_account_id = account_id
                        project = self.env['project.project'].search([('account_id', '=', account_id)])
                        if project:
                            record.project_id = project.id
                        break

        return res



class ProjectProject(models.Model):
    _inherit = 'project.project'

    def _calc_invoices(self):
        for record in self:
            if record.customer_invoices:
                record.customer_invoice_count = len(record.customer_invoices)
            else:
                record.customer_invoice_count = 0
            if record.supplier_invoices:
                record.supplier_invoice_count = len(record.supplier_invoices)
            else:
                record.supplier_invoice_count = 0

    customer_invoices = fields.One2many('account.move', 'project_id', string='Customer Invoices',
                                        domain=[('move_type', 'in', ('out_invoice', 'out_refund'))])
    supplier_invoices = fields.One2many('account.move', 'project_id', string='Supplier Invoices',
                                        domain=[('move_type', 'in', ('in_invoice', 'in_refund'))])
    customer_invoice_count = fields.Integer(string='Customer Invoice Count', compute='_calc_invoices')
    supplier_invoice_count = fields.Integer(string='Supplier Invoice Count', compute='_calc_invoices')

    def action_view_customer_invoices(self):
        self.ensure_one()
        if not self.customer_invoices:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('No Customer Invoices'),
                    'message': _('There are no customer invoices in this project'),
                }
            }

        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "name": "Customer Invoices",
            "views": [[False, "list"], [False, "form"]],
            "context": {"create": False},
            "domain": [["id", "in", [x.id for x in self.customer_invoices]]],
        }
        if len(self.customer_invoices) == 1:
            action_window["views"] = [[False, "form"]]
            action_window["res_id"] = self.customer_invoices[0].id

        return action_window

    def action_view_supplier_invoices(self):
        self.ensure_one()
        if not self.supplier_invoices:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('No Supplier Invoices'),
                    'message': _('There are no supplier invoices in this project'),
                }
            }
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "name": "Customer Invoices",
            "views": [[False, "list"], [False, "form"]],
            "context": {"create": False},
            "domain": [["id", "in", [x.id for x in self.supplier_invoices]]],
        }
        if len(self.supplier_invoices) == 1:
            action_window["views"] = [[False, "form"]]
            action_window["res_id"] = self.supplier_invoices[0].id

        return action_window
