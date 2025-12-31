import json
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def import_payments(self, import_payments_from, company):
        if not self.import_payments_from:
            raise UserError('No date from set in settings')
        date_from = import_payments_from - relativedelta(days=7)

        url = 'https://api.xero.com/api.xro/2.0/Payments?where=Date>=DateTime(%s,%s,%s)' % (
            date_from.year, date_from.month, date_from.day)
        data = self.get_data(url)
        if not data:
            return

        if data.status_code == 401:
            raise ValidationError(
                'Time Out..!!\n Please check your connection or error in application or refresh token.')

        parsed_dict = json.loads(data.text)
        # write to error log so can review issues in processing
        self.env['xero.error.log'].error_log(record=False, name='Payments Processing', error=data.text)
        if parsed_dict.get('Payments'):
            list_of_dicts = parsed_dict.get('Payments')
            for item in list_of_dicts:
                if not item.get('Status') == 'DELETED':
                    self.create_imported_payments(item)
            company.import_payments_from = fields.Date.context_today(self)
            success_form = self.env.ref('xero_integration.import_successfull_view',
                                        False)

            return {
                'name': _('Notification'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'res.company.message',
                'views': [(success_form.id, 'form')],
                'view_id': success_form.id,
                'target': 'new',
            }
        else:
            raise ValidationError('There is no any payment present in XERO.')

    def compute_payment_date(self, datestring):
        timepart = datestring.split('(')[1].split(')')[0]
        milliseconds = int(timepart[:-5])
        hours = int(timepart[-5:]) / 100
        time = milliseconds / 1000

        dt = datetime.utcfromtimestamp(time + hours * 3600)
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + '%02d:00' % hours

    def get_invoice_being_paid(self, pay, dict_for_payment):
        if pay.get('Invoice').get('InvoiceID'):

            invoices = self.env['account.move'].search(
                [
                    ('company_id', '=', self.env.company.id),
                    '|', '|', ('xero_invoice_id', '=', pay.get('Invoice').get('InvoiceID')),
                    ('xero_invoice_number', '=', pay.get('Invoice').get('InvoiceNumber')),
                    ('name', '=', pay.get('Invoice').get('InvoiceNumber')),
                ])

            if invoices:
                invoice_being_paid = invoices[0]
                if pay.get('Invoice').get('Type') and pay.get('Invoice').get('Type') not in \
                        ['APPREPAYMENT', 'ARPREPAYMENT', 'APOVERPAYMENT', 'AROVERPAYMENT']:
                    if invoice_being_paid.state == 'draft':
                        invoice_being_paid.action_post()

                    dict_for_payment['communication'] = invoice_being_paid.name

                    if invoice_being_paid.partner_id.parent_id:
                        dict_for_payment['partner_id'] = invoice_being_paid.partner_id.parent_id.id
                    else:
                        dict_for_payment['partner_id'] = invoice_being_paid.partner_id.id
            else:
                if pay.get('Invoice').get('Contact'):
                    if pay.get('Invoice').get('Contact').get('ContactID'):
                        customer_id = self.env['res.partner'].search(
                            [('xero_cust_id', '=', pay.get('Invoice').get('Contact').get('ContactID')),
                             ('company_id', '=', self.id)], limit=1) or self.env['res.partner'].search(
                            [('name', '=', pay.get('Invoice').get('Contact').get('Name')),
                             ('company_id', '=', self.id)], limit=1)
                        if customer_id:
                            if customer_id.parent_id:
                                dict_for_payment['partner_id'] = customer_id.parent_id.id
                            else:
                                dict_for_payment['partner_id'] = customer_id.id
                        else:
                            self.fetch_the_required_customer(pay.get('Invoice').get('Contact').get('ContactID'))
                            res_partner = self.env['res.partner'].search(
                                [('xero_cust_id', '=', pay.get('Invoice').get('Contact').get('ContactID')),
                                 ('company_id', '=', self.id)], limit=1)
                            if res_partner:
                                if res_partner.parent_id:
                                    dict_for_payment['partner_id'] = res_partner.parent_id.id
                                else:
                                    dict_for_payment['partner_id'] = res_partner.id
        return dict_for_payment, invoice_being_paid

    def get_payment_type(self, pay, dict_g):
        if pay.get('PaymentType') == 'ACCRECPAYMENT':
            dict_g['partner_type'] = 'customer'
            # Receive money - Inbound
            pay_type = 'sale'
        elif pay.get('PaymentType') == 'ACCPAYPAYMENT':
            dict_g['partner_type'] = 'supplier'
            # Send money - Outbound
            pay_type = 'purchase'
        elif pay.get('PaymentType') == 'ARCREDITPAYMENT':
            dict_g['partner_type'] = 'customer'
            # Send money - Outbound
            pay_type = 'purchase'
        elif pay.get('PaymentType') == 'APCREDITPAYMENT':
            dict_g['partner_type'] = 'supplier'
            # Receive money - Inbound
            pay_type = 'sale'
        elif pay.get('PaymentType') == 'AROVERPAYMENTPAYMENT':
            dict_g['partner_type'] = 'customer'
            pay_type = 'sale'
        elif pay.get('PaymentType') == 'APOVERPAYMENTPAYMENT':
            dict_g['partner_type'] = 'supplier'
            pay_type = 'purchase'
        elif pay.get('PaymentType') == 'ARPREPAYMENTPAYMENT':
            dict_g['partner_type'] = 'customer'
            pay_type = 'sale'
        elif pay.get('PaymentType') == 'APPREPAYMENTPAYMENT':
            dict_g['partner_type'] = 'supplier'
            pay_type = 'purchase'
        return pay_type

    def process_invoice_payment(self, pay, dict_for_payment):

        dict_for_payment, invoice_being_paid = self.get_invoice_being_paid(pay, dict_for_payment)

        journal = False
        if pay.get('Code'):
            journal_id = self.env['account.journal'].get_journal_from_account(
                pay.get('Account').get('Code'))
            dict_for_payment['journal_id'] = journal_id.id
            journal = journal_id[0]
        if not journal:
            raise UserError('Valid Journal not found')

        if pay.get('PaymentType'):
            pay_type = self.get_payment_type(pay, dict_for_payment)
            payment_type = 'inbound' if pay_type == 'sale' else 'outbound'

            if payment_type == 'inbound':
                dict_for_payment['payment_type'] = 'inbound'
                payment_method = self.env.ref('account.account_payment_method_manual_in')
                journal_payment_methods = journal.inbound_payment_method_ids
            else:
                dict_for_payment['payment_type'] = 'outbound'
                payment_method = self.env.ref('account.account_payment_method_manual_out')
                journal_payment_methods = journal.outbound_payment_method_ids

            if payment_method:
                dict_for_payment['payment_method_id'] = payment_method.id

            if payment_method not in journal_payment_methods:
                self._cr.commit()
                raise ValidationError(_('No appropriate payment method enabled on journal %s') % journal.name)

        return dict_for_payment, invoice_being_paid

    def account_payment_register(self, dict_g, invoice, pay):
        if dict_g['date']:
            dict_g['payment_date'] = dict_g['date']
            del dict_g['date']
        register_payments = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.id).create(dict_g)
        payment_id = register_payments._create_payments()
        if pay.get('PaymentID') and payment_id:
            payment_id.xero_payment_id = pay.get('PaymentID')

    def get_base_data(self, pay, dict_for_payment):
        if pay.get('Amount'):
            dict_for_payment['amount'] = pay.get('Amount')
        else:
            dict_for_payment['amount'] = 0.0

        if pay.get('Date'):
            payment_date = self.compute_payment_date(pay.get('Date'))
            payment_date_a = payment_date.split('T')
            converted_date = datetime.strptime(payment_date_a[0], '%Y-%m-%d')

            dict_for_payment['date'] = converted_date
        return dict_for_payment

    def create_imported_payments(self, pay):
        acc_pay = self.env['account.payment'].search(
            [('xero_payment_id', '=', pay.get('PaymentID')), ('company_id', '=', self.id)])

        if acc_pay:
            return

        dict_for_payment = {}
        dict_for_payment = self.get_base_data(pay, dict_for_payment)

        if pay.get('Invoice'):
            dict_for_payment, invoice = self.process_invoice_payment(pay, dict_for_payment)
            self.account_payment_register(dict_for_payment, invoice, pay)

        else:
            if 'journal_id' not in dict_for_payment:
                raise ValidationError(_('Payment Journal required'))

            if pay.get('PaymentID'):
                dict_for_payment['xero_payment_id'] = pay.get('PaymentID')
            if 'communication' in dict_for_payment:
                dict_for_payment['ref'] = dict_for_payment['communication']
                del dict_for_payment['communication']

            pay_create = acc_pay.create(dict_for_payment)
            pay_create.action_post()
        self._cr.commit()
