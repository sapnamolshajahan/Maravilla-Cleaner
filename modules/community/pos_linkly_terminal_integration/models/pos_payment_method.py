# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
import uuid
import datetime
import requests
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('linkly', 'EFTPOS')]

    linkly_test_mode = fields.Boolean(help='Run transactions in the test environment.')
    secret = fields.Text(string="Secret")
    posName = fields.Text(string="PosName")
    posVersion = fields.Char(string="PosVersion")
    posId = fields.Char(string="PosId")
    posVendorId = fields.Char(string="PosVendorId")
    token = fields.Text(string="Token")

    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields+=['linkly_test_mode','secret','posName','posVersion','posId','posVendorId','token']
        return fields

    @api.onchange('use_payment_terminal')
    def _on_change_use_payment_terminal(self):
        for rec in self:
            if rec.use_payment_terminal == 'linkly':
                rec.split_transactions = False
                
    def generate_pin_pad_pairing_request(self):
        view = self.env.ref('pos_linkly_terminal_integration.view_pin_pad_pairing_wizard')
        return {
            'name': _("Pin Pad Pairing"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pin.pad.pairing',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': { 'linkly_test_mode' : self.linkly_test_mode, 'pos_payment_method_id' : self.id } 
        }

    @api.model
    def proxy_linkly_request(self, vals):
        if vals and vals.get('order_ref'):
            if vals.get('fail_transaction'):
                trans = self.env['linkly.transaction'].search([('order_ref','=', vals.get('order_ref')),('state','!=','done')])
                if trans:
                    trans.write({ 'state': 'cancel' })
                linkly_vals = {
                    'order_ref': vals.get('order_ref'),
                    'amount': vals.get('amount'),
                    'payment_method_id': vals.get('payment_method_id'),
                    'txnType': vals.get('txnType'),
                    'state':'draft',
                    'pos_session_id':vals.get('pos_session_id'),
                    'order_uid':vals.get('UID'),
                    'opr':vals.get('OPR'),
                    'uid':vals.get('linkly_payment_UUID'),
                }
                if (vals.get('txnType') == 'R') and vals.get('RFN'):
                    linkly_vals['refundtxnRef'] = vals.get('RFN')
                new_trans = self.env['linkly.transaction'].create(linkly_vals)
                data = self.start_transaction(new_trans, vals.get('fail_transaction'))
                return data
            else:
                trans = self.env['linkly.transaction'].search([('order_ref','=', vals.get('order_ref')),('state','!=','done')])
                if trans:
                    trans.write({ 'state': 'cancel' })
                linkly_vals = {
                    'order_ref': vals.get('order_ref'),
                    'amount': vals.get('amount'),
                    'payment_method_id': vals.get('payment_method_id'),
                    'txnType': vals.get('txnType'),
                    'state':'draft',
                    'pos_session_id':vals.get('pos_session_id'),
                    'order_uid':vals.get('UID'),
                    'opr':vals.get('OPR'),
                    'uid':vals.get('linkly_payment_UUID'),
                }
                if (vals.get('txnType') == 'R') and vals.get('RFN'):
                    linkly_vals['refundtxnRef'] = vals.get('RFN')
                new_trans = self.env['linkly.transaction'].create(linkly_vals)
                # self.env.cr.commit()
                data = self.start_transaction(new_trans)
                return data
        else:
            raise ValidationError("Insufficient Data")

    def start_transaction(self, new_trans, fail_transaction=False):
        if new_trans.payment_method_id and new_trans.pos_session_id and not new_trans.pos_session_id.token:
            payment_method_id = new_trans.payment_method_id
            is_linkly_test_mode = payment_method_id.linkly_test_mode
            auth_request_request_payload = {
                'secret': payment_method_id.secret,
                'posName': payment_method_id.posName,
                'posVersion': payment_method_id.posVersion,
                'posId': payment_method_id.posId,
                'posVendorId': payment_method_id.posVendorId,
            }
            if is_linkly_test_mode:
                auth_request_response = requests.post('https://auth.sandbox.cloud.pceftpos.com/v1/tokens/cloudpos', json=auth_request_request_payload)
            else:
                auth_request_response = requests.post('https://auth.cloud.pceftpos.com/v1/tokens/cloudpos', json=auth_request_request_payload)

            auth_request_response_payload = auth_request_response.json()
            if auth_request_response_payload and auth_request_response_payload.get('token'):
                token =  auth_request_response_payload.get('token')
                new_trans.pos_session_id.token = token
                token_expiry_seconds = auth_request_response_payload.get('expirySeconds')
                token_expiry_time = fields.Datetime.to_string(datetime.datetime.utcnow() + datetime.timedelta(seconds=token_expiry_seconds))
                new_trans.pos_session_id.token_expiry_seconds = token_expiry_seconds
                new_trans.pos_session_id.token_expiry_time = token_expiry_time

                if is_linkly_test_mode:
                    url = 'https://rest.pos.sandbox.cloud.pceftpos.com/v1/sessions'
                    amtPurchase = int(new_trans.amount*100)
                else:
                    url = 'https://rest.pos.cloud.pceftpos.com/v1/sessions'
                    # amtPurchase = new_trans.amount
                    amtPurchase = round(new_trans.amount*100)
                new_trans.txnRef = datetime.datetime.now().strftime('%y%m%d%H%M%S%f')[:-4]

                # Check failed transaction
                if fail_transaction:
                    request_payload = {
                        'request': {
                            'txnType': 'P',
                            'amtPurchase': amtPurchase,
                        }
                    }
                    uri = url + '/' + new_trans.uid + '/transaction?async=false'
                    headers = {'Authorization': 'Bearer ' + token}
                    new_trans.request_data = request_payload
                    new_trans.request_url = uri
                    response = requests.get(uri, headers=headers)
                    if response.status_code == 200:
                        response_payload = response.json()
                        new_trans.return_data = response_payload
                        if response_payload and response_payload.get('response'):
                            response =  response_payload.get('response')
                            if response.get('success'):
                                new_trans.state = 'done'
                                new_trans.success_data = response_payload
                            else:
                                new_trans.state = 'failed'
                                new_trans.failed_data = response_payload
                        response_payload['response']['order_uuid'] = new_trans.uid
                        return response_payload
                    elif response.status_code == 400:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 400 (Bad Request : The request is invalid)"
                        return {
                            'responseType' : 'Bad Request',
                            'title' : 'Bad Request : The request is invalid'
                        }
                    elif response.status_code == 401:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 401 (Unauthorised : The client needs to authenticate before it can continue)"
                        return {
                            'responseType' : 'Unauthorised',
                            'title' : "Unauthorised : The client needs to authenticate before it can continue"
                        }
                    elif response.status_code == 403:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 403 (Forbidden : The client doesn't have access to the resource)"
                        return {
                            'responseType' : 'Forbidden',
                            'title' : "Forbidden : The client doesn't have access to the resource"
                        }
                    elif response.status_code == 404:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 404 (Not found : The requested resource wasn't found)"
                        return {
                            'responseType' : 'Not found',
                            'title' : "Not found : The requested resource wasn't found"
                        }
                    elif response.status_code == 408:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 408 (Request Timeout : The payment request was timed out)"
                        return {
                            'responseType' : 'Request Timeout',
                            'title' : "Request Timeout : The payment request was timed out"
                        }
                    elif response.status_code >= 500 or response.status_code <= 599:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : "+response.status_code+" (EFTPOS Server Error : The server encountered an internal error processing the request)"
                        return {
                            'responseType' : 'EFTPOS Server Error',
                            'title' : "EFTPOS Server Error : The server encountered an internal error processing the request"
                        }
                else:
                    request_payload = {
                        'Request': {
                            "Merchant": "00",
                            'txnType': new_trans.txnType,
                            'amtPurchase': amtPurchase,
                            'txnRef': new_trans.txnRef,
                            "Application": "00",
                            "CutReceipt": "1",
                            "ReceiptAutoPrint": "0",
                        }
                    }
                    if new_trans.pos_session_id.config_id:
                        request_payload['Request']['PurchaseAnalysisData'] = {
                            'UID': new_trans.order_uid,
                            'OPR': new_trans.opr,
                            'AMT': new_trans.amount,
                            'REF': new_trans.order_uid,
                            'PCM': "1",
                        }
                    if (new_trans.txnType == 'R') and new_trans.refundtxnRef and new_trans.pos_session_id.config_id:
                        request_payload['Request']['PurchaseAnalysisData'] = {
                            'UID': new_trans.order_uid,
                            'OPR': new_trans.opr,
                            'AMT': new_trans.amount,
                            'REF': new_trans.order_uid,
                            'PCM': "1",
                            'RFN': new_trans.refundtxnRef,
                        }

                    url = url+'/' + new_trans.uid + '/transaction?async=false'
                    headers = {'Authorization': 'Bearer ' + token}
                    new_trans.request_data = request_payload
                    new_trans.request_url = url
                    response = requests.post(url, json=request_payload, headers=headers)
                    # _logger.info("\n\n\nresponse.status_code---------------%r-----------\n\n\n",response.status_code)
                    if response.status_code == 200:
                        response_payload = response.json()
                        new_trans.return_data = response_payload
                        if response_payload and response_payload.get('response'):
                            response =  response_payload.get('response')
                            if response.get('success'):
                                new_trans.state = 'done'
                                new_trans.success_data = response_payload
                            else:
                                new_trans.state = 'failed'
                                new_trans.failed_data = response_payload
                        response_payload['response']['order_uuid'] = new_trans.uid
                        return response_payload
                    elif response.status_code == 400:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 400 (Bad Request : The request is invalid)"
                        return {
                            'responseType' : 'Bad Request',
                            'title' : 'Bad Request : The request is invalid'
                        }
                    elif response.status_code == 401:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 401 (Unauthorised : The client needs to authenticate before it can continue)"
                        return {
                            'responseType' : 'Unauthorised',
                            'title' : "Unauthorised : The client needs to authenticate before it can continue"
                        }
                    elif response.status_code == 403:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 403 (Forbidden : The client doesn't have access to the resource)"
                        return {
                            'responseType' : 'Forbidden',
                            'title' : "Forbidden : The client doesn't have access to the resource"
                        }
                    elif response.status_code == 404:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 404 (Not found : The requested resource wasn't found)"
                        return {
                            'responseType' : 'Not found',
                            'title' : "Not found : The requested resource wasn't found"
                        }
                    elif response.status_code == 408:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : 408 (Request Timeout : The payment request was timed out)"
                        return {
                            'responseType' : 'Request Timeout',
                            'title' : "Request Timeout : The payment request was timed out"
                        }
                    elif response.status_code >= 500 or response.status_code <= 599:
                        new_trans.state = 'failed'
                        new_trans.failed_data = "Error Code : "+response.status_code+" (EFTPOS Server Error : The server encountered an internal error processing the request)"
                        return {
                            'responseType' : 'EFTPOS Server Error',
                            'title' : "EFTPOS Server Error : The server encountered an internal error processing the request"
                        }
            else:
                return auth_request_response_payload
        elif new_trans.payment_method_id and new_trans.pos_session_id and new_trans.pos_session_id.token:
            token_expired = self.is_token_expired(new_trans.pos_session_id.token, new_trans.pos_session_id.token_expiry_time)
            if token_expired:
                new_trans.pos_session_id.token = False
                new_trans.pos_session_id.token_expiry_seconds = False
                new_trans.pos_session_id.token_expiry_time = False
                return self.start_transaction(new_trans, False)
            else:
                token = new_trans.pos_session_id.token
                payment_method_id = new_trans.payment_method_id
                is_linkly_test_mode = payment_method_id.linkly_test_mode
                if is_linkly_test_mode:
                    url = 'https://rest.pos.sandbox.cloud.pceftpos.com/v1/sessions'
                    amtPurchase = int(new_trans.amount*100)
                else:
                    url = 'https://rest.pos.cloud.pceftpos.com/v1/sessions'
                    # amtPurchase = new_trans.amount
                    amtPurchase = round(new_trans.amount*100)
                new_trans.txnRef = datetime.datetime.now().strftime('%y%m%d%H%M%S%f')[:-4]

                # Check failed transaction
                if fail_transaction:
                    request_payload = {
                        'request': {
                            'txnType': 'P',
                            'amtPurchase': amtPurchase,
                        }
                    }
                    uri = url + '/' + new_trans.uid + '/transaction?async=false'
                    headers = {'Authorization': 'Bearer ' + token}
                    new_trans.request_data = request_payload
                    new_trans.request_url = uri
                    try:
                        response = requests.get(uri, headers=headers)
                        if response.status_code == 200:
                            response_payload = response.json()
                            new_trans.return_data = response_payload
                            if response_payload and response_payload.get('response'):
                                response =  response_payload.get('response')
                                if response.get('success'):
                                    new_trans.state = 'done'
                                    new_trans.success_data = response_payload
                                else:
                                    new_trans.state = 'failed'
                                    new_trans.failed_data = response_payload
                            response_payload['response']['order_uuid'] = new_trans.uid
                            return response_payload
                        elif response.status_code == 400:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 400 (Bad Request : The request is invalid)"
                            return {
                                'responseType' : 'Bad Request',
                                'title' : 'Bad Request : The request is invalid'
                            }
                        elif response.status_code == 401:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 401 (Unauthorised : The client needs to authenticate before it can continue)"
                            return {
                                'responseType' : 'Unauthorised',
                                'title' : "Unauthorised : The client needs to authenticate before it can continue"
                            }
                        elif response.status_code == 403:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 403 (Forbidden : The client doesn't have access to the resource)"
                            return {
                                'responseType' : 'Forbidden',
                                'title' : "Forbidden : The client doesn't have access to the resource"
                            }
                        elif response.status_code == 404:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 404 (Not found : The requested resource wasn't found)"
                            return {
                                'responseType' : 'Not found',
                                'title' : "Not found : The requested resource wasn't found"
                            }
                        elif response.status_code == 408:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 408 (Request Timeout : The payment request was timed out)"
                            return {
                                'responseType' : 'Request Timeout',
                                'title' : "Request Timeout : The payment request was timed out"
                            }
                        elif response.status_code >= 500 or response.status_code <= 599:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : "+response.status_code+" (EFTPOS Server Error : The server encountered an internal error processing the request)"
                            return {
                                'responseType' : 'EFTPOS Server Error',
                                'title' : "EFTPOS Server Error : The server encountered an internal error processing the request"
                            }
                    except Exception as e:
                        _logger.info("e : ( %r) ",e)
                else:
                    request_payload = {
                        'Request': {
                            "Merchant": "00",
                            'txnType': new_trans.txnType,
                            'amtPurchase': amtPurchase,
                            'txnRef': new_trans.txnRef,
                            "Application": "00",
                            "CutReceipt": "1",
                            "ReceiptAutoPrint": "0",
                        }
                    }
                    if new_trans.pos_session_id.config_id:
                        request_payload['Request']['PurchaseAnalysisData'] = {
                            'UID': new_trans.order_uid,
                            'OPR': new_trans.opr,
                            'AMT': new_trans.amount,
                            'REF': new_trans.order_uid,
                            'PCM': "1",
                        }
                    if (new_trans.txnType == 'R') and new_trans.refundtxnRef and new_trans.pos_session_id.config_id:
                        request_payload['Request']['PurchaseAnalysisData'] = {
                            'UID': new_trans.order_uid,
                            'OPR': new_trans.opr,
                            'AMT': new_trans.amount,
                            'REF': new_trans.order_uid,
                            'PCM': "1",
                            'RFN': new_trans.refundtxnRef,
                        }

                    url = url+'/' + new_trans.uid + '/transaction?async=false'
                    headers = {'Authorization': 'Bearer ' + token}
                    try:
                        new_trans.request_data = request_payload
                        new_trans.request_url = url
                        response = requests.post(url, json=request_payload, headers=headers)
                        if response.status_code == 200:
                            response_payload = response.json()
                            new_trans.return_data = response_payload
                            if response_payload and response_payload.get('response'):
                                response =  response_payload.get('response')
                                if response.get('success'):
                                    new_trans.state = 'done'
                                    new_trans.success_data = response_payload
                                else:
                                    new_trans.state = 'failed'
                                    new_trans.failed_data = response_payload
                            response_payload['response']['order_uuid'] = new_trans.uid
                            return response_payload
                        elif response.status_code == 400:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 400 (Bad Request : The request is invalid)"
                            return {
                                'responseType' : 'Bad Request',
                                'title' : 'Bad Request : The request is invalid'
                            }
                        elif response.status_code == 401:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 401 (Unauthorised : The client needs to authenticate before it can continue)"
                            return {
                                'responseType' : 'Unauthorised',
                                'title' : "Unauthorised : The client needs to authenticate before it can continue"
                            }
                        elif response.status_code == 403:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 403 (Forbidden : The client doesn't have access to the resource)"
                            return {
                                'responseType' : 'Forbidden',
                                'title' : "Forbidden : The client doesn't have access to the resource"
                            }
                        elif response.status_code == 404:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 404 (Not found : The requested resource wasn't found)"
                            return {
                                'responseType' : 'Not found',
                                'title' : "Not found : The requested resource wasn't found"
                            }
                        elif response.status_code == 408:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : 408 (Request Timeout : The payment request was timed out)"
                            return {
                                'responseType' : 'Request Timeout',
                                'title' : "Request Timeout : The payment request was timed out"
                            }
                        elif response.status_code >= 500 or response.status_code <= 599:
                            new_trans.state = 'failed'
                            new_trans.failed_data = "Error Code : "+response.status_code+" (EFTPOS Server Error : The server encountered an internal error processing the request)"
                            return {
                                'responseType' : 'EFTPOS Server Error',
                                'title' : "EFTPOS Server Error : The server encountered an internal error processing the request"
                            }
                    except Exception as e:
                        _logger.info("e : ( %r) ",e)
                        new_trans.pos_session_id.token = False
                        return self.start_transaction(new_trans, False)
    
    def is_token_expired(self, token, token_expiry_time):
        if not token or not token_expiry_time:
            return True
        current_datetime = fields.Datetime.now()
        return current_datetime >= token_expiry_time

    @api.model
    def reprint_linkly_receipt(self, vals):
        linkly_transaction = self.env['linkly.transaction'].search([('txnRef', '=', vals.get('txnRef').replace(' ', ''))])
        if linkly_transaction:
            payment_method_id = linkly_transaction.payment_method_id
            is_linkly_test_mode = payment_method_id.linkly_test_mode
            auth_request_request_payload = {
                'secret': payment_method_id.secret,
                'posName': payment_method_id.posName,
                'posVersion': payment_method_id.posVersion,
                'posId': payment_method_id.posId,
                'posVendorId': payment_method_id.posVendorId,
            }
            if is_linkly_test_mode:
                auth_request_response = requests.post('https://auth.sandbox.cloud.pceftpos.com/v1/tokens/cloudpos', json=auth_request_request_payload)
            else:
                auth_request_response = requests.post('https://auth.cloud.pceftpos.com/v1/tokens/cloudpos', json=auth_request_request_payload)

            auth_request_response_payload = auth_request_response.json()
            if auth_request_response_payload and auth_request_response_payload.get('token'):
                token =  auth_request_response_payload.get('token')
                if linkly_transaction.pos_session_id:
                    linkly_transaction.pos_session_id.token = token
                    token_expiry_seconds = auth_request_response_payload.get('expirySeconds')
                    token_expiry_time = fields.Datetime.to_string(datetime.datetime.utcnow() + datetime.timedelta(seconds=token_expiry_seconds))
                    linkly_transaction.pos_session_id.token_expiry_seconds = token_expiry_seconds
                    linkly_transaction.pos_session_id.token_expiry_time = token_expiry_time

                if is_linkly_test_mode:
                    url = 'https://rest.pos.sandbox.cloud.pceftpos.com/v1/sessions'
                else:
                    url = 'https://rest.pos.cloud.pceftpos.com/v1/sessions'

                request_payload = {
                    'request': {
                        "reprintType": "1",
                        "TxnRef": vals.get('txnRef').replace(' ', ''),
                        "TxnType":linkly_transaction.txnType
                    }
                }
                url = url+'/' + str(uuid.uuid4()) + '/reprintreceipt?async=false'
                headers = {'Authorization': 'Bearer ' + token}
                try:
                    response = requests.post(url, json=request_payload, headers=headers)
                    response_payload = response.json()
                    return response_payload
                except Exception as e:
                    _logger.info("e : ( %r) ",e)
                    return False
            else:
                return auth_request_response_payload
        else:
            return False

class PosSession(models.Model):
    _inherit = 'pos.session'

    token = fields.Text(string="Token")
    token_expiry_seconds = fields.Integer(string="Token Validity (Seconds)")
    token_expiry_time = fields.Datetime(string="Token Expiry Time")
