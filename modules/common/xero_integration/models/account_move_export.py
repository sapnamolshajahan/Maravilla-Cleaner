import json
import logging
import time

import requests

from odoo import models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def remove_note_section(self, vals):

        if 'LineItems' in vals:
            vals.get('LineItems')[:] = [item for item in vals.get('LineItems') if
                                        item['AccountCode'] != None and item['Quantity'] != 0.0]
        return vals

    def post_data(self, url, parsed_dict):
        token = self.env.company.xero_oauth_token
        headers = self.env['xero.token'].get_head()
        if not token or not headers:
            raise UserError('Missing token or header for call to Xero')

        protected_url = url
        data = requests.request('PUT', url=protected_url, data=parsed_dict, headers=headers)
        # Set a delay between sending requests as a rate limiting precaution
        delay = self.env.company.xero_integration_delay
        if delay:
            time.sleep(delay)
        return data

    def show_error_message(self, data):
        response_data = json.loads(data.text)
        if response_data:
            if response_data.get('Elements'):
                for element in response_data.get('Elements'):
                    if element.get('ValidationErrors'):
                        for err in element.get('ValidationErrors'):
                            raise ValidationError(
                                '(Invoice/Vendor Bill/Credit Note) Xero Exception : ' + err.get('Message'))
            elif response_data.get('Message'):
                raise ValidationError(
                    '(Invoice/Vendor Bill/Credit Note) Xero Exception : ' + response_data.get('Message'))
            else:
                raise ValidationError(
                    '(Invoice/Vendor Bill/Credit Note) Xero Exception : please check xero logs in odoo for more details')

    def get_xero_tax_state_literal(self, tax_state):
        literal_tax_state = 'NoTax'
        if tax_state:
            if tax_state == 'inclusive':
                literal_tax_state = 'Inclusive'
            elif self.tax_state == 'exclusive':
                literal_tax_state = 'Exclusive'
            elif self.tax_state == 'no_tax':
                literal_tax_state = 'NoTax'

        return literal_tax_state

    def prepare_line(self, line):
        company = self.env.company
        account_code = None
        qty = abs(line.quantity)
        price = abs(line.price_unit)
        discount = line.discount if line.discount else 0.0

        if line.account_id:
            account_code = line.account_id.code
            if not line.account_id.xero_account_id:
                self.env['account.account'].create_account_ref_in_xero(line.account_id)

        tax = False
        line_tax = self.env['account.tax'].search([('id', '=', line.tax_ids[0].id), ('company_id', '=', company.id)])
        if line_tax:
            tax = line_tax.xero_tax_type_id
            if not tax:
                raise UserError('Tax code for Xero not set up for {tax_name'.format(tax_name=line_tax.name))

            if line.product_id and not company.export_bill_without_product:
                if not line.product_id.xero_product_id:
                    self.env['product.product'].get_xero_product_ref(line.product_id)

        line_vals = {
            'Description': line.name,
            'UnitAmount': price,
            'ItemCode': line.product_id.default_code if line.product_id else '',
            'AccountCode': account_code,
            'Quantity': qty,
            'DiscountRate': discount,
            'TaxType': tax if tax else '',
        }
        tracking_list = []
        tracking_dict = {}
        if line.analytic_account_id:
            line.analytic_account_id.create_analytic_account_in_xero(account_id=line.analytic_account_id.id)
            tracking_dict.update({'TrackingCategoryID': line.analytic_account_id.xero_tracking_opt_id,
                                  'Name': line.name,
                                  'Option': line.analytic_account_id.name})
            tracking_list.append(tracking_dict)

        line_vals.update({
            'Tracking': tracking_list
        })

        return line_vals

    def prepare_credit_vals(self, tax_state, origin_credit_note, xero_cust_id, currency_code, move, status, tr_type):
        return {
            "Type": tr_type,
            "LineAmountTypes": tax_state,
            'Reference': origin_credit_note,
            "Contact": {"ContactID": xero_cust_id},
            "DueDate": str(move.invoice_date_due),
            "CurrencyCode": currency_code,
            "Date": str(move.invoice_date),
            "CreditNoteNumber": self.xero_invoice_number if (
                    move.xero_invoice_number and move.xero_invoice_id) else move.name,
            "Status": status,
        }

    def prepare_invoice_vals(self, tax_state, origin_reference, xero_cust_id, currency_code, move, status, tr_type):
        return {
            "Type": tr_type,
            "LineAmountTypes": tax_state,
            'Reference': origin_reference,
            "Contact": {"ContactID": xero_cust_id},
            "DueDate": str(move.invoice_date_due),
            "CurrencyCode": currency_code,
            "Date": str(move.invoice_date),
            "InvoiceNumber": self.xero_invoice_number if (
                    move.xero_invoice_number and move.xero_invoice_id) else move.name,
            "Status": status,
        }

    def c_move_type(self, move_type):
        if move_type == 'out_refund':
            tr_type = 'ACCRECCREDIT'
        elif move_type == 'in_refund':
            tr_type = 'ACCPAYCREDIT'
        elif move_type == 'out_invoice':
            tr_type = 'ACCREC'
        elif move_type == 'in_invoice':
            tr_type = 'ACCPAY'
        return tr_type

    def prepare_export_dict(self, move, move_type):
        company = self.env.company
        if not move.partner_id:
            raise UserError('All invoices or credits must have a partner')

        xero_cust_id = self.env['res.partner'].get_xero_partner_ref(move.partner_id)
        vals = {}
        lst_line = []
        currency_code = ''
        tr_type = self.c_move_type(move_type)
        if not tr_type:
            raise UserError('Type {move_type} not handled'.format(move_type=move_type))

        if self.invoice_origin:
            origin_reference = self.invoice_origin
        elif move.xero_invoice_number and move.xero_invoice_id:
            origin_reference = self.xero_invoice_number
        else:
            origin_reference = move.ref if move.ref else move.name

        if self.currency_id:
            currency_code = self.currency_id.name

        tax_state = self.get_xero_tax_state_literal(self.tax_state)
        status = 'AUTHORISED'

        if company.invoice_status and company.invoice_status == 'draft':
            status = 'DRAFT'
        header_dict = self.prepare_credit_vals(tax_state, origin_reference, xero_cust_id, currency_code, move, status,
                                               tr_type)
        vals.update(header_dict)

        for line in self.invoice_line_ids:
            line_vals = self.prepare_line(line)
            lst_line.append(line_vals)
            vals.update({"LineItems": lst_line})

        return vals

    def process_refund(self, move, move_type):
        values = self.prepare_export_dict(move, move_type)
        vals = self.remove_note_section(values)
        parsed_dict = json.dumps(vals)
        _logger.info(_("PARSED DICT : %s %s" % (parsed_dict, type(parsed_dict))))
        url = 'https://api.xero.com/api.xro/2.0/CreditNotes'
        data = self.post_data(url, parsed_dict)
        _logger.info('Response From Server : {}'.format(data.text))

        if data.status_code == 200:
            self.env['xero.error.log'].success_log(record=move, name='CreditNote Export')
            parsed_data = json.loads(data.text)
            if parsed_data:
                if parsed_data.get('CreditNotes'):
                    move.xero_invoice_number = parsed_data.get('CreditNotes')[0].get('CreditNoteNumber')
                    move.xero_invoice_id = parsed_data.get(
                        'CreditNotes')[0].get('CreditNoteID')
                    self._cr.commit()
                    _logger.info(_("(CREATE) Exported successfully to XERO"))
        elif data.status_code == 400:
            self.env['xero.error.log'].error_log(record=t, name='CreditNote Export', error=data.text)
            self._cr.commit()
            self.show_error_message(data)
        elif data.status_code == 401:
            raise ValidationError(
                "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")

        return

    def process_out_invoice(self, move, move_type, headers):
        dict_values = self.prepare_export_dict(move, move_type)
        dict_vals = self.remove_note_section(dict_values)
        parsed_dict_vals = json.dumps(dict_vals)
        _logger.info(_("PARSED DICT : %s %s" % (parsed_dict_vals, type(parsed_dict_vals))))
        invoice_url = 'https://api.xero.com/api.xro/2.0/Invoices'
        invoice_response_data = requests.request('POST', url=invoice_url, data=parsed_dict_vals, headers=headers)
        _logger.info('Response From Server : {}'.format(invoice_response_data.text))

        if invoice_response_data.status_code == 200:
            self.env['xero.error.log'].success_log(record=move, name='Invoice Export')

            parsed_data = json.loads(invoice_response_data.text)
            if parsed_data:
                if parsed_data.get('Invoices'):
                    move.xero_invoice_number = parsed_data.get('Invoices')[0].get('InvoiceNumber')
                    move.xero_invoice_id = parsed_data.get(
                        'Invoices')[0].get('InvoiceID')
                    self._cr.commit()
                    _logger.info(_("(CREATE) Exported successfully to XERO"))
                    delay = self.env.company.xero_integration_delay
                    if delay:
                        time.sleep(delay)
        elif invoice_response_data.status_code == 400:
            self.env['xero.error.log'].error_log(record=move, name='Invoice Export', error=invoice_response_data.text)
            self._cr.commit()
            self.show_error_message(invoice_response_data)
        elif invoice_response_data.status_code == 401:
            raise ValidationError(
                "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")

        return

    def process_in_invoice(self, move, move_type, headers):
        dict_values = self.prepare_export_dict(move, move_type)
        dict_vals = self.remove_note_section(dict_values)
        parsed_dict_vals = json.dumps(dict_vals)
        _logger.info(_("PARSED DICT : %s %s" % (parsed_dict_vals, type(parsed_dict_vals))))
        invoice_url = 'https://api.xero.com/api.xro/2.0/Invoices'
        invoice_response_data = requests.request('POST', url=invoice_url, data=parsed_dict_vals, headers=headers)
        _logger.info('Response From Server : {}'.format(invoice_response_data.text))

        if invoice_response_data.status_code == 200:
            self.env['xero.error.log'].success_log(record=move, name='Invoice Export')

            parsed_data = json.loads(invoice_response_data.text)
            if parsed_data:
                if parsed_data.get('Invoices'):
                    move.xero_invoice_number = parsed_data.get('Invoices')[0].get('InvoiceNumber')
                    move.xero_invoice_id = parsed_data.get(
                        'Invoices')[0].get('InvoiceID')
                    self._cr.commit()
                    _logger.info(_("(CREATE) Exported successfully to XERO"))
                    delay = self.env.company.xero_integration_delay
                    if delay:
                        time.sleep(delay)
        elif invoice_response_data.status_code == 400:
            self.env['xero.error.log'].error_log(record=move, name='Invoice Export', error=invoice_response_data.text)
            self._cr.commit()
            self.show_error_message(invoice_response_data)
        elif invoice_response_data.status_code == 401:
            raise ValidationError(
                "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")

        return

    def line_amount_type(self, move):
        lineamounttype = ''
        if move.tax_state == 'no_tax':
            lineamounttype = 'NoTax'
        elif move.tax_state == 'inclusive':
            lineamounttype = 'Inclusive'
        elif move.tax_state == 'exclusive':
            lineamounttype = 'Exclusive'
        return lineamounttype

    def process_journal(self, move, move_type, headers):
        vals = {}
        status = 'POSTED'
        line_amount = 0.0
        account_code = ''
        narration = move.ref or move.name
        date = str(move.date)
        lineamounttype = self.line_amount_type(move)
        journal_line_ids = []

        for line in self.line_ids:
            line_dict = {}

            if line.credit > 0:
                line_amount = -float(line.credit)
            elif line.debit > 0:
                line_amount = float(line.debit)

            if line.account_id:
                account_code = line.account_id.code
                if not line.account_id.xero_account_id:
                    self.env['account.account'].create_account_ref_in_xero(line.account_id)

            line_dict.update({
                "Description": line.name,
                "LineAmount": line_amount,
                "AccountCode": account_code,
            })

            tracking_list = []
            tracking_dict = {}

            if line.analytic_account_id:
                line.analytic_account_id.create_analytic_account_in_xero(account_id=line.analytic_account_id.id)
                tracking_dict.update({'Name': line.name,
                                      'Option': line.analytic_account_id.name})
                tracking_list.append(tracking_dict)

            line_dict.update({
                'Tracking': tracking_list
            })

            journal_line_ids.append(line_dict)

        if journal_line_ids:
            vals.update({"JournalLines": journal_line_ids})
            vals.update({
                "Date": date,
                "Status": status,
                "Narration": narration,
                "LineAmountTypes": lineamounttype,
                "ShowOnCashBasisReports": "false"
            })

            parsed_dict = json.dumps(vals)
            _logger.info("\n\nPrepared Dictionary :   {} ".format(parsed_dict))

            url = 'https://api.xero.com/api.xro/2.0/ManualJournals'
            data = requests.request('POST', url=url, data=parsed_dict, headers=headers)
            _logger.info("Response 2 From Server :{} {}".format(data.status_code, data.text))

            if data.status_code == 200:
                self.env['xero.error.log'].success_log(record=move, name='ManualJournals Export')
                response_data = json.loads(data.text)

                if response_data.get('ManualJournals'):
                    move.xero_invoice_id = response_data.get('ManualJournals')[0].get('ManualJournalID')
                    self._cr.commit()
                    _logger.info(_("Exported successfully to XERO"))
                    delay = self.env.company.xero_integration_delay
                    if delay:
                        time.sleep(delay)

            elif data.status_code == 400:
                self.env['xero.error.log'].error_log(record=move, name='ManualJournals Export', error=data.text)
                self._cr.commit()
                self.show_error_message(data)

            elif data.status_code == 401:
                raise ValidationError(
                    "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
        else:
            _logger.error("No Journal lines are present for this Invoice.")

        return

    def export_move(self, move):
        headers = self.env['xero.token'].get_head()

        if move.move_type in ('out_refund', 'in_refund'):
            self.process_refund(move, move.move_type)
        elif move.move_type == 'out_invoice':
            self.process_out_invoice(move, move.move_type, headers)
        elif move.move_type == 'in_invoice':
            self.process_in_invoice(move, move.move_type, headers)
        elif move.move_type == 'entry':
            self.process_journal(move, move.move_type, headers)
        else:
            raise UserError('Move Type {move_type} not catered for'.format(move_type=move.move_type))

    def export_move_cron(self):
        moves = self.env['account.move'].search([('xero_invoice_id', '=', False), ('state', '=', 'posted'),
                                                 ('journal_id.type', 'not in', ('bank', 'cash'))])
        for move in moves:
            try:
                self.export_move(move)
            except:
                pass
