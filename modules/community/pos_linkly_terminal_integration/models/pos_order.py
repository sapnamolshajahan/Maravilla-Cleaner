# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _export_for_ui(self, order):
        res = super(PosOrder, self)._export_for_ui(order)
        linkly_transaction =  self.env['linkly.transaction'].search([('order_ref', '=', res.get('uid'))], limit=1)
        if linkly_transaction:
            res.update({
                'txnRef': linkly_transaction.txnRef if linkly_transaction.txnRef else False
            })
        return res

    @api.model 
    def _payment_fields(self, order, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        res['linkly_receipt'] = ui_paymentline.get('linkly_receipt') or ''
        return res
    
class PosPayment(models.Model):
    _inherit = 'pos.payment'

    linkly_receipt = fields.Text('EFTPOS Receipt')

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_payment_method(self):
        result = super()._loader_params_pos_payment_method()
        result['search_params']['fields'].append('linkly_test_mode')
        result['search_params']['fields'].append('secret')
        return result
