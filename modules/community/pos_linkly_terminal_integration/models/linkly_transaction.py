# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from odoo import fields, models, api,_

class LinklyTransaction(models.Model):
    _name =  'linkly.transaction'
    _description = 'Linkly Payment Terminal Transaction'

    name = fields.Char(compute='_compute_transaction_name')
    state = fields.Selection(string='State',
        selection=[('draft', 'Draft'), ('pending', 'Pending'), ('done', 'Done'), ('cancel','Cancel'), ('failed','Failed')])
    order_ref = fields.Char(string="Order Ref")
    payment_method_id = fields.Many2one("pos.payment.method")
    amount = fields.Float(string="Amount")
    transaction_id = fields.Char(string="Transaction Ref")
    txnType = fields.Selection(string='Transaction Type', selection=[('P', 'Purchase'), ('R', 'Refund')])
    txnRef = fields.Char(string="TxnRef")
    refundtxnRef = fields.Char(string="Refund TxnRef")
    uid = fields.Char(string="UID")
    return_data = fields.Text(string="Return Data")
    success_data = fields.Text(string="Success Data")
    failed_data = fields.Text(string="Failed Data")
    pos_session_id = fields.Many2one('pos.session', string="POS Session")
    order_uid = fields.Char("UID")
    opr = fields.Char("OPR")
    request_data = fields.Text(string="Request Data")
    request_url = fields.Text(string="Request URL")

    @api.depends('order_ref')
    def _compute_transaction_name(self):
        for record in self:
            record.name = record.order_ref
