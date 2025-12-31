import base64
import json
import logging
import math
from datetime import date, datetime
import datetime
from math import ceil, floor
from dateutil.relativedelta import relativedelta

import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"


    def import_payments(self,date_from=None):
        """IMPORT PAYMENTS(Customer payments and Vendor payments) FROM XERO TO ODOO"""
        if date_from:
            date_from = date_from - relativedelta(days=7)
        else:
            date_from = 0

        if date_from:
            url = 'https://api.xero.com/api.xro/2.0/Payments?where=Date>=DateTime(%s,%s,%s)' % (
                date_from.year, date_from.month, date_from.day)
        else:
            url = 'https://api.xero.com/api.xro/2.0/Payments'
        data = self.get_data(url)
        if data:
            recs = []

            parsed_dict = json.loads(data.text)
            self.env['xero.error.log'].error_log(record=False, name='Payments Processing', error=data.text)
            if parsed_dict.get('Payments'):
                list_of_dicts = parsed_dict.get('Payments')
                for item in list_of_dicts:
                    if not item.get('Status') == 'DELETED':
                        self.create_imported_payments(item)
                success_form = self.env.ref('xero_integration.import_successfull_view',
                                                False)
                date_from = datetime.datetime.today().strftime('%Y-%m-%d')

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

        elif data.status_code == 401:
            raise ValidationError(
                'Time Out..!!\n Please check your connection or error in application or refresh token.')

    def compute_payment_date(self, datestring):
        timepart = datestring.split('(')[1].split(')')[0]
        milliseconds = int(timepart[:-5])
        hours = int(timepart[-5:]) / 100
        time = milliseconds / 1000

        dt = datetime.datetime.utcfromtimestamp(time + hours * 3600)
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + '%02d:00' % hours

    @api.model
    def create_imported_payments(self, pay):
        acc_pay = self.env['account.payment'].search([
            ('xero_payment_id', '=', pay.get('PaymentID')), ('company_id', '=', self.env.company.id)
        ])

        dict_g = {
            'amount': pay.get('Amount', 0.0)
        }
        invoice_pay = False

        if pay.get('Date'):
            payment_date = self.compute_payment_date(pay.get('Date')).split('T')[0]
            dict_g['date'] = datetime.datetime.strptime(payment_date, '%Y-%m-%d')

        try:
            invoice_data = pay.get('Invoice')
            if invoice_data and invoice_data.get('InvoiceID'):
                inv = self.env['account.move'].search([
                    '|', ('xero_invoice_id', '=', invoice_data.get('InvoiceID')),
                    ('xero_invoice_number', '=', invoice_data.get('InvoiceNumber'))
                ])
                invoices = inv.filtered(lambda i: i.company_id == self)
                invoice_pay = invoices[:1]

                if invoice_pay and invoice_data.get('Type') not in ['APPREPAYMENT', 'ARPREPAYMENT', 'APOVERPAYMENT',
                                                                    'AROVERPAYMENT']:
                    if invoice_pay.state == 'draft':
                        invoice_pay.action_post()

                    dict_g.update({
                        'communication': invoice_pay.name,
                        'partner_id': invoice_pay.partner_id.parent_id.id if invoice_pay.partner_id.parent_id else invoice_pay.partner_id.id
                    })

                elif invoice_data.get('Contact') and invoice_data['Contact'].get('ContactID'):
                    customer_id = self.env['res.partner'].search([
                        ('xero_cust_id', '=', invoice_data['Contact'].get('ContactID')),
                        ('company_id', '=', self.env.company.id)
                    ], limit=1) or self.env['res.partner'].search([
                        ('name', '=', invoice_data['Contact'].get('Name')),
                        ('company_id', '=', self.env.company.id)
                    ], limit=1)

                    if not customer_id:
                        self.fetch_the_required_customer(invoice_data['Contact'].get('ContactID'))
                        customer_id = self.env['res.partner'].search([
                            ('xero_cust_id', '=', invoice_data['Contact'].get('ContactID')),
                            ('company_id', '=', self.env.company.id)
                        ], limit=1)

                    if customer_id:
                        dict_g['partner_id'] = customer_id.parent_id.id if customer_id.parent_id else customer_id.id

            payment_type_map = {
                'ACCRECPAYMENT': ('customer', 'sale'),
                'ACCPAYPAYMENT': ('supplier', 'purchase'),
                'ARCREDITPAYMENT': ('customer', 'purchase'),
                'APCREDITPAYMENT': ('supplier', 'sale'),
                'AROVERPAYMENTPAYMENT': ('customer', 'sale'),
                'APOVERPAYMENTPAYMENT': ('supplier', 'purchase'),
                'ARPREPAYMENTPAYMENT': ('customer', 'sale'),
                'APPREPAYMENTPAYMENT': ('supplier', 'purchase')
            }

            if pay.get('PaymentType') in payment_type_map:
                dict_g['partner_type'], pay_type = payment_type_map[pay.get('PaymentType')]

            if 'partner_id' in dict_g:
                journal_id = self.env['account.journal'].get_journal_from_account(pay.get('Account').get('Code'))
                if not journal_id:
                    raise ValidationError(_('Payment Journal required'))

                dict_g['journal_id'] = journal_id.id
                payment_type = 'inbound' if pay_type == 'sale' else 'outbound'

                payment_method = self.env.ref(
                    f'account.account_payment_method_manual_{"in" if payment_type == "inbound" else "out"}')
                journal_payment_method_line = journal_id.inbound_payment_method_line_ids.filtered(lambda
                                                                                                      l: l.payment_method_id.id == payment_method.id) if payment_type == 'inbound' else journal_id.outbound_payment_method_line_ids.filtered(
                    lambda l: l.payment_method_id.id == payment_method.id)
                if payment_method and journal_payment_method_line:
                    dict_g['payment_method_line_id'] = journal_payment_method_line.id
                else:
                    raise ValidationError(_('No appropriate payment method enabled on journal %s') % journal_id.name)

            if not acc_pay:
                if invoice_pay:
                    dict_g['payment_date'] = dict_g.pop('date', None)
                    register_payments = self.env['account.payment.register'].with_context(
                        active_model='account.move', active_ids=invoice_pay.id
                    ).create(dict_g)
                    payment_id = register_payments._create_payments()
                    if pay.get('PaymentID') and payment_id:
                        payment_id.xero_payment_id = pay.get('PaymentID')

                    if not invoice_pay.amount_residual:
                        invoice_pay.write({'payment_state': 'paid'})

                else:
                    dict_g['xero_payment_id'] = pay.get('PaymentID')
                    dict_g['ref'] = dict_g.pop('communication', '')

                    pay_create = self.env['account.payment'].create(dict_g)
                    pay_create.action_post()

        except Exception as e:
            self.env['xero.error.log'].create({
                'record_id': False,
                'transaction': 'Payment Import',
                'xero_error_msg': str(e)
            })
            self._cr.commit()

    def import_prepayments(self,from_date=None):
        """IMPORT PREPAYMENTS(Customer payments and Vendor payments) FROM XERO TO ODOO"""

        if from_date:
            date_from = datetime.datetime.strptime(str(from_date), '%Y-%m-%d').date()
        else:
            date_from = 0

        if date_from:
            url = 'https://api.xero.com/api.xro/2.0/Prepayments?where=Date>=DateTime(%s,%s,%s)' % (
                date_from.year, date_from.month, date_from.day)
        else:
            url = 'https://api.xero.com/api.xro/2.0/Prepayments'
        data = self.get_data(url)

        if data:

            parsed_dict = json.loads(data.text)

            if parsed_dict.get('Prepayments'):
                if parsed_dict.get('Prepayments'):
                    record = parsed_dict.get('Prepayments')
                    if isinstance(record, (dict,)):
                        if not record.get('Status') == 'VOIDED':
                            self.create_imported_prepayments(record)
                    else:
                        for grp in parsed_dict.get('Prepayments'):
                            if not grp.get('Status') == 'VOIDED':
                                self.create_imported_prepayments(grp)
                    success_form = self.env.ref('xero_integration.import_successfull_view',
                                                False)
                    from_date = datetime.datetime.today().strftime('%Y-%m-%d')

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
                raise UserError('There is no any payment present in XERO.')

        elif data.status_code == 401:
            raise UserError('Time Out..!!\n Please check your connection or error in application or refresh token.')

    @api.model
    def create_imported_prepayments(self, pay):
        acc_pay = self.env['account.payment'].search([
            ('xero_prepayment_id', '=', pay.get('PrepaymentID')), ('company_id', '=', self.env.company.id)])

        dict_g = {
            'date': pay.get('DateString'),
            'amount': pay.get('Total', 0.0)
        }

        def get_invoice_data(invoice):
            inv = self.env['account.move'].search([
                '|', ('xero_invoice_id', '=', invoice.get('Invoice').get('InvoiceID')),
                ('xero_invoice_number', '=', invoice.get('Invoice').get('InvoiceNumber'))]) or self.env[
                      'account.move'].search([
                '|', ('xero_invoice_id', '=', invoice.get('Invoice').get('InvoiceID')),
                ('name', '=', invoice.get('Invoice').get('InvoiceNumber'))])
            return self.env['account.move'].search([('id', 'in', inv.ids), ('company_id', '=', self.env.company.id)])

        def set_partner_and_communication(invoice_pay):
            dict_g['communication'] = invoice_pay.name
            dict_g[
                'partner_id'] = invoice_pay.partner_id.parent_id.id if invoice_pay.partner_id.parent_id else invoice_pay.partner_id.id

        def set_payment_type_and_journal(pay_type):
            dict_g.update({
                'partner_type': 'customer' if pay_type == 'sale' else 'supplier',
                'journal_id': self.prepayment_journal.id,
                'payment_type': 'inbound' if pay_type == 'sale' else 'outbound'
            })

            payment_method = self.env.ref(
                'account.account_payment_method_manual_in' if pay_type == 'sale' else 'account.account_payment_method_manual_out')
            journal_payment_methods = self.prepayment_journal.inbound_payment_method_line_ids if pay_type == 'sale' else self.prepayment_journal.outbound_payment_method_line_ids

            if payment_method not in journal_payment_methods:
                self._cr.commit()
                raise UserError(_('No appropriate payment method enabled on journal %s') % self.prepayment_journal.name)

            dict_g['payment_method_id'] = payment_method.id

        pay_type = 'sale' if pay.get('Type') == 'RECEIVE-PREPAYMENT' else 'purchase'

        allocations = pay.get('Allocations', [])
        if allocations:
            communication, invoice_ids = '', []
            for invoice in allocations:
                invoice_pay = get_invoice_data(invoice.get('Invoice'))[:1]
                if invoice_pay:
                    set_partner_and_communication(invoice_pay)
                    communication = f"{communication},{invoice_pay.name}" if communication else invoice_pay.name
                    invoice_ids.append(invoice_pay.id)

            dict_g['communication'] = communication
            dict_g['partner_id'] = dict_g.get('partner_id') or self.get_payment_contact(pay)
            set_payment_type_and_journal(pay_type)
        else:
            dict_g['partner_id'] = self.get_payment_contact(pay)
            set_payment_type_and_journal(pay_type)

        if not acc_pay and 'partner_id' in dict_g:
            if 'journal_id' not in dict_g:
                raise ValidationError(_('Payment Journal required'))

            dict_g['xero_prepayment_id'] = pay.get('PrepaymentID')
            dict_g['ref'] = dict_g.pop('communication', None)

            pay_create = self.env['account.payment'].create(dict_g)
            pay_create.action_post()
            self._cr.commit()

    def import_overpayments(self,date_from=None):
        """IMPORT OVERPAYMENTS(Customer payments and Vendor payments) FROM XERO TO ODOO"""

        if date_from:
            date_from = datetime.datetime.strptime(str(date_from), '%Y-%m-%d').date()
        else:
            date_from = 0

        if date_from:
            url = 'https://api.xero.com/api.xro/2.0/Overpayments?where=Date>=DateTime(%s,%s,%s)' % (
                date_from.year, date_from.month, date_from.day)
        else:
            url = 'https://api.xero.com/api.xro/2.0/Overpayments'
        data = self.get_data(url)
        if data:

            parsed_dict = json.loads(data.text)
            if parsed_dict.get('Overpayments'):
                if parsed_dict.get('Overpayments'):
                    record = parsed_dict.get('Overpayments')
                    if isinstance(record, (dict,)):
                        if not record.get('Status') == 'VOIDED':
                            self.create_imported_overpayments(record)
                    else:
                        for grp in parsed_dict.get('Overpayments'):
                            if not grp.get('Status') == 'VOIDED':
                                self.create_imported_overpayments(grp)
                    success_form = self.env.ref('xero_integration.import_successfull_view',
                                                False)
                    date_from = datetime.datetime.today().strftime('%Y-%m-%d')

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
                raise UserError('There is no any payment present in XERO.')

        elif data.status_code == 401:
            raise UserError('Time Out..!!\n Please check your connection or error in application or refresh token.')

    def create_imported_overpayments(self, pay):
        acc_pay = self.env['account.payment'].search([
            ('xero_overpayment_id', '=', pay.get('OverpaymentID')), ('company_id', '=', self.env.company.id)])

        dict_g = {
            'date': pay.get('DateString'),
            'amount': pay.get('Total', 0.0)
        }

        def get_invoice_data(invoice):
            inv = self.env['account.move'].search(
                ['|', ('xero_invoice_id', '=', invoice.get('Invoice').get('InvoiceID')),
                 ('xero_invoice_number', '=', invoice.get('Invoice').get('InvoiceNumber'))]) or \
                  self.env['account.move'].search(
                      ['|', ('xero_invoice_id', '=', invoice.get('Invoice').get('InvoiceID')),
                       ('name', '=', invoice.get('Invoice').get('InvoiceNumber'))])
            return self.env['account.move'].search([
                ('id', 'in', inv.ids), ('company_id', '=', self.env.company.id)])

        def set_payment_details(pay_type):
            dict_g['partner_type'] = 'customer' if pay_type == 'sale' else 'supplier'
            dict_g['journal_id'] = self.overpayment_journal.id
            payment_method = self.env.ref(
                'account.account_payment_method_manual_in' if pay_type == 'sale' else 'account.account_payment_method_manual_out')
            journal_payment_methods = self.overpayment_journal.inbound_payment_method_ids if pay_type == 'sale' else self.overpayment_journal.outbound_payment_method_ids
            dict_g['payment_type'] = 'inbound' if pay_type == 'sale' else 'outbound'
            dict_g['payment_method_id'] = payment_method.id

            if payment_method not in journal_payment_methods:
                self._cr.commit()
                raise UserError(
                    _('No appropriate payment method enabled on journal %s') % self.overpayment_journal.name)

        if pay.get('Allocations'):
            communication = ''
            invoice_ids = []

            for invoice in pay.get('Allocations'):
                invoice_pay = get_invoice_data(invoice).filtered(lambda i: i)
                if invoice_pay:
                    communication = f"{communication},{invoice_pay.name}" if communication else invoice_pay.name
                    invoice_ids.append(invoice_pay.id)

            dict_g['communication'] = communication
            dict_g['partner_id'] = self.get_payment_contact(pay)

            pay_type = 'sale' if pay.get('Type') == 'RECEIVE-OVERPAYMENT' else 'purchase'
            set_payment_details(pay_type)
        else:
            dict_g['partner_id'] = self.get_payment_contact(pay)
            pay_type = 'sale' if pay.get('Type') == 'RECEIVE-OVERPAYMENT' else 'purchase'
            set_payment_details(pay_type)

        if not acc_pay and 'partner_id' in dict_g:
            if 'journal_id' not in dict_g:
                raise ValidationError(_('Payment Journal required'))

            _logger.info('[Payment] DICTIONARY :: %s', dict_g)

            if pay.get('Allocations'):
                dict_g['xero_overpayment_id'] = pay.get('OverpaymentID')
                dict_g['ref'] = dict_g.pop('communication', '')
                pay_create = acc_pay.create(dict_g)
                pay_create.action_post()
            elif not pay.get('Allocations') and not pay.get('Payments'):
                dict_g['xero_overpayment_id'] = pay.get('OverpaymentID')
                dict_g['ref'] = dict_g.pop('communication', '')
                pay_create = acc_pay.create(dict_g)
                pay_create.action_post()

            self._cr.commit()

    def get_payment_contact(self, pay):
        partner_id = ''
        if pay.get('Contact'):
            if pay.get('Contact').get('ContactID'):
                customer_id = self.env['res.partner'].search(
                    [('xero_cust_id', '=', pay.get('Contact').get('ContactID')),
                     ('company_id', '=', self.env.company.id)], limit=1) or self.env['res.partner'].search(
                    [('name', '=', pay.get('Contact').get('Name')),
                     ('company_id', '=', self.env.company.id)], limit=1)
                if customer_id:
                    if customer_id.parent_id:
                        partner_id = customer_id.parent_id.id
                        _logger.info('[Payment] existing CUSTOMER :parent :: %s', customer_id)
                    else:
                        partner_id = customer_id.id
                        _logger.info('[Payment] existing CUSTOMER :child :: %s', customer_id)
                else:
                    self.fetch_the_required_customer(
                        pay.get('Contact').get('ContactID'))
                    res_partner = self.env['res.partner'].search(
                        [('xero_cust_id', '=',
                          pay.get('Contact').get('ContactID')),
                         ('company_id', '=', self.id)], limit=1)
                    if res_partner:
                        if res_partner.parent_id:
                            partner_id = res_partner.parent_id.id
                            _logger.info('[Payment] CUSTOMER :parent :: %s', res_partner)
                        else:
                            partner_id = res_partner.id
                            _logger.info('[Payment] CUSTOMER :child :: %s', res_partner)
        return partner_id