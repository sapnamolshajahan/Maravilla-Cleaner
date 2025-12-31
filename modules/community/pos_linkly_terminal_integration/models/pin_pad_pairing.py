# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
import requests
from odoo import fields, models, _
from odoo.exceptions import ValidationError

class PinPadPairing(models.TransientModel):
    _name = 'pin.pad.pairing'
    _description = 'Pin Pad Terminal Pairing Wizard'

    username = fields.Char('Username')
    password = fields.Char('Password')
    pairCode = fields.Char('Pair Code')

    def generate_request(self):
        request_payload = {
            'username': self.username,
            'password': self.password,
            'pairCode': self.pairCode
        }
        if self.env.context.get('linkly_test_mode'):
            response = requests.post('https://auth.sandbox.cloud.pceftpos.com/v1/pairing/cloudpos', json=request_payload)
        else:
            response = requests.post('https://auth.cloud.pceftpos.com/v1/pairing/cloudpos', json=request_payload)
        if response.status_code == 401:
            raise ValidationError(""+ response.reason +" : Invalid details (username, password, or paircode).",)
        elif response.status_code == 400:
            raise ValidationError(""+ response.reason +" : Invalid request.")
        elif response.status_code == 408:
            raise ValidationError(""+ response.reason +" : Request Timeout.")
        elif response.status_code >= 500 and response.status_code <= 599:
            raise ValidationError(""+ response.reason +" : EFTPOS Server Error.")
        elif response.status_code == 200:
            response_payload = response.json()
            if response_payload.get('secret') and self.env.context.get('pos_payment_method_id'):
                pos_payment_method = self.env['pos.payment.method'].browse([self.env.context.get('pos_payment_method_id')])
                if pos_payment_method:
                    pos_payment_method.secret = response_payload.get('secret')
                return self._linkly_message('Paired Successfully.')
            else:
                raise ValidationError(response_payload)
            
    def _linkly_message(self,message):
        message_id = self.env['linkly.wizard.message'].create(dict(text=message))
        return {
            'name':"EFTPOS Payment",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'linkly.wizard.message',
            'res_id': message_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
        }
