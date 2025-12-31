import json
import logging

import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    xero_payment_id = fields.Char(string="Xero Payment Id", copy=False)
    xero_prepayment_id = fields.Char(string="Xero Prepayment Id", copy=False)
    xero_overpayment_id = fields.Char(string="Xero Overpayment Id", copy=False)

    def prepare_payment_export_dict(self):
        vals = {}

        if self.journal_id.default_account_id and not self.journal_id.default_account_id.xero_account_id:
            self.env['account.account'].create_account_ref_in_xero(self.journal_id.default_account_id)

        invoice_ids = []
        if self.reconciled_invoice_ids:
            invoice_ids = self.reconciled_invoice_ids
        if self.reconciled_bill_ids:
            invoice_ids = self.reconciled_bill_ids

        for invoice in invoice_ids:
            xero_id = False
            if not invoice.xero_invoice_id:
                if invoice.state == 'posted':
                    if invoice.move_type == 'out_invoice' or invoice.move_type == 'in_invoice':
                        invoice.exportInvoice(payment_export=True)
                    if invoice.move_type == 'out_refund' or invoice.move_type == 'in_refund':
                        invoice.exportCreditNote(payment_export=True)
                    xero_id = invoice.xero_invoice_id
            if invoice.xero_invoice_id:
                xero_id = invoice.xero_invoice_id
            if invoice.move_type == 'out_invoice' or invoice.move_type == 'in_invoice':
                ApplyOn = "Invoice"
                ApplyOn_Dict = {"InvoiceID": xero_id}
            elif invoice.move_type == 'out_refund' or invoice.move_type == 'in_refund':
                ApplyOn = "CreditNote"
                ApplyOn_Dict = {"CreditNoteID": xero_id}

            if xero_id and ApplyOn and ApplyOn_Dict:
                vals.update({
                    ApplyOn: ApplyOn_Dict,
                    "Account": {"AccountID": self.journal_id.default_account_id.xero_account_id},
                    "Date": str(self.date),
                    "Amount": self.amount,
                    "Reference": self.name
                })
        return vals

    @api.model
    def create_payment_in_xero(self):
        xero_config = self.env.company
        if self._context.get('active_ids'):
            payments = self.browse(self._context.get('active_ids'))
        else:
            payments = self

        for payment in payments.filtered(lambda x: not x.xero_payment_id):
            vals = payment.prepare_payment_export_dict()
            if not vals:
                raise ValidationError("Payment can not be exported, something went wrong...!!")

            parsed_dict = json.dumps(vals)
            token = xero_config.xero_oauth_token
            headers = self.env['xero.token'].get_head()
            if not token or not headers:
                raise UserError('Missing token or headers')

            protected_url = 'https://api.xero.com/api.xro/2.0/Payments'
            data = requests.request('POST', url=protected_url, data=parsed_dict, headers=headers)

            if data.status_code == 200:
                self.env['xero.error.log'].success_log(record=payment, name='Payment Export')
                response_data = json.loads(data.text)
                if response_data.get('Payments')[0].get('PaymentID'):
                    payment.xero_payment_id = response_data.get('Payments')[0].get('PaymentID')
                    _logger.info(_("(CREATE) - Exported successfully to XERO"))
            elif data.status_code == 401:
                raise ValidationError(
                    "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
            elif data.status_code == 400:
                self.env['xero.error.log'].error_log(record=payment, name='Payment Export', error=data.text)
                self._cr.commit()

                response_data = json.loads(data.text)
                if response_data:
                    if response_data.get('Elements'):
                        for element in response_data.get('Elements'):
                            if element.get('ValidationErrors'):
                                for err in element.get('ValidationErrors'):
                                    raise ValidationError(
                                        '(Payment) Xero Exception : ' + err.get(
                                            'Message'))
                    elif response_data.get('Message'):
                        raise ValidationError(
                            '(Payment) Xero Exception : ' + response_data.get(
                                'Message'))
                    else:
                        raise ValidationError(
                            '(Payment) Xero Exception : please check xero logs in odoo for more details')
            else:
                raise ValidationError("Please Check Your Connection or error in application or refresh token..!!")

    def export_payment_cron(self):
        payment_records = self.env['account.payment'].search([('xero_payment_id', '=', False)])
        for payment in payment_records:
            payment.create_payment_in_xero()
