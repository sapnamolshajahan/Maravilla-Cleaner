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

    def _get_access_token(self):
        for record in self:
            token = self.env['xero.token'].search([('company_id', '=', record.id)])
            if token.access_token:
                record.xero_access_token = token.access_token

    xero_client_id = fields.Char('Client Id', copy=False,
                                 help="The Client Id that you obtain from the developer dashboard.")
    xero_client_secret = fields.Char('Client Secret', copy=False,
                                     help="The Client Secret that you obtain from the developer dashboard.")
    xero_user_id = fields.Char('User Id', copy=False,
                               help="The Email id that you use to login to your odoo account")
    xero_password = fields.Char('Password', copy=False,
                                help="The Password that you use to login to your odoo account")
    xero_auth_base_url = fields.Char('Authorization URL',
                                     default="https://login.xero.com/identity/connect/authorize   ",
                                     help="User authenticate uri")
    xero_access_token_url = fields.Char('Access Token URL',
                                        default="https://identity.xero.com/connect/token",
                                        help="One of the redirect URIs listed for this project in the developer"
                                             "dashboard used to get the verifier code.")
    xero_tenant_id_url = fields.Char('Tenant ID URL', default="https://api.xero.com/connections",
                                     help="Check the full set of tenants you've been authorized to access.")
    xero_redirect_url = fields.Char('Redirect URL', help="http://localhost:8069/get_auth_code")

    xero_access_token = fields.Char('Access Token', compute='_get_access_token')
    xero_oauth_token = fields.Char('Oauth Token', help="OAuth Token")
    xero_oauth_token_secret = fields.Char('Oauth Token Secret')
    xero_company_id = fields.Char('Xero Company ID')
    xero_country_name = fields.Char('Xero Country Name')
    xero_company_name = fields.Char('Xero Company Name/Organisation', help="Add name of your organisation.")
    xero_tenant_id = fields.Char('Tenant Id')
    refresh_token_xero = fields.Char('Refresh Token')
    skip_emails = fields.Char('Skip the following emails',
                              help='This field is used to skip the contacts having following email ids. \n Note : Separate the email ids with comma.')
    revenue_default_account = fields.Many2one(comodel_name='account.account',
                                              help='This Account will be attached to the invoice lines which does not contain quantity,unit price and account',
                                              string='Default Account')
    overpayment_journal = fields.Many2one(comodel_name='account.journal', help='Overpayment Journal')
    prepayment_journal = fields.Many2one(comodel_name='account.journal', help='Prepayment Journal')
    xero_tenant_name = fields.Char('Xero Company', copy=False)
    manual_journal = fields.Many2one(comodel_name='account.journal', help="Manual Journal")
    export_invoice_without_product = fields.Boolean('Export Invoices with description only', copy=False)
    export_bill_without_product = fields.Boolean('Export Bills with description only', copy=False)
    invoice_status = fields.Selection([('draft', 'DRAFT'), ('authorised', 'AUTHORISED')], 'Invoice/Bill Status',
                                      default='authorised')
    non_tracked_item = fields.Boolean('Export Stockable Product as Non Tracked Items', copy=False)
    import_payments_from = fields.Date(string='Import payments from')
    xero_integration_delay = fields.Integer(string='Delay between sending Xero documents', copy=False, default=5)

    def get_headers(self):
        headers = {}
        headers['Authorization'] = 'Bearer ' + str(self.xero_oauth_token)
        headers['Xero-tenant-id'] = self.xero_tenant_id
        headers['Accept'] = 'application/json'

        return headers

    @api.model
    def get_data(self, url, post=0):
        if not self:
            self = self.env.company
        if self.xero_oauth_token:
            headers = self.get_headers()
            protected_url = url
            if post == 0:
                data = requests.request('GET', protected_url, headers=headers)
            else:
                data = requests.request('POST', protected_url, headers=headers)

        else:
            raise UserError('Please Authenticate First With Xero.')
        return data

    def import_country(self):
        url = 'https://api.xero.com/api.xro/2.0/Organisations'
        data = self.get_data(url)
        if data:
            parsed_dict = json.loads(data.text)

            if parsed_dict.get('Organisations'):
                if parsed_dict.get('Organisations'):
                    record = parsed_dict.get('Organisations')
                    if isinstance(record, (dict,)):
                        country_id = self.env['res.country'].search(
                            [('code', '=', record.get('CountryCode'))])
                        country_name = country_id.name
                        return country_name
                    else:
                        for c_id in parsed_dict.get('Organisations'):
                            country_id = self.env['res.country'].search(
                                [('code', '=', c_id.get('CountryCode'))])
                            country_name = country_id.name
                            return country_name

    def import_invoice(self,date_from=None):
        """IMPORT INVOICE(Customer Invoice and Vendor Bills) FROM XERO TO ODOO"""
        _logger.info("\n\n\n<-----------------------------------INVOICE-------------------------------------->", )

        for i in range(10000):
            res = self.invoice_main_function(i + 1,date_from)
            _logger.info("RESPONSE : %s", res)
            if not res:
                break
        success_form = self.env.ref('xero_integration.import_successfull_view', False)
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

    @api.model
    def invoice_main_function(self, page_no,date_from=None):
        _logger.info("INVOICE PAGE NO : %s", page_no)
        if date_from:
            date_from = datetime.datetime.strptime(str(date_from), '%Y-%m-%d').date()
        else:
            date_from = 0

        if date_from:
            url = 'https://api.xero.com/api.xro/2.0/Invoices?page=' + str(
                page_no) + '&where=Date>=DateTime(%s,%s,%s)' % (date_from.year, date_from.month, date_from.day)
        else:
            url = 'https://api.xero.com/api.xro/2.0/Invoices?page=' + str(page_no)
        data = self.get_data(url)
        if data:
            recs = []

            parsed_dict = json.loads(data.text)
            if parsed_dict.get('Invoices'):
                record = parsed_dict.get('Invoices')
                if isinstance(record, (dict,)):
                    if not (record.get('Status') == 'DRAFT' or record.get('Status') == 'DELETED' or record.get(
                            'Status') == 'VOIDED' or record.get('Status') == 'SUBMITTED'):
                        self.create_imported_invoice(record)
                else:
                    for cust in parsed_dict.get('Invoices'):
                        if not (cust.get('Status') == 'DRAFT' or cust.get('Status') == 'DELETED' or cust.get(
                                'Status') == 'VOIDED' or cust.get('Status') == 'SUBMITTED'):
                            self.create_imported_invoice(cust)
                return True
            else:
                if page_no == 1:
                    raise ValidationError('There is no any invoice present in XERO.')
                else:
                    date_from = datetime.datetime.today().strftime('%Y-%m-%d')
                    return False

        elif data.status_code == 401:
            raise ValidationError(
                'Time Out..!!\n Please check your connection or error in application or refresh token.')

    @api.model
    def create_imported_invoice(self, cust):
        if cust.get('InvoiceNumber'):
            _logger.info("PROCESSING INVOICE NUMBER : %s", cust.get('InvoiceNumber'))
        _logger.info("PROCESSING INVOICE ID : %s", cust.get('InvoiceID'))

        account_invoice = self.env['account.move'].search(
            [('xero_invoice_id', '=', cust.get('InvoiceID')), ('company_id', '=', self.env.company.id)])
        if not account_invoice:
            res_partner = self.env['res.partner'].search(
                [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)], limit=1)
            if res_partner:
                self.create_customer_for_invoice(cust, res_partner)
            else:
                self.fetch_the_required_customer(cust.get('Contact').get('ContactID'))
                res_partner2 = self.env['res.partner'].search(
                    [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)],
                    limit=1)
                if res_partner2:
                    self.create_customer_for_invoice(cust, res_partner2)
        else:
            _logger.info("INVOICE OBJECT : %s", account_invoice)
            for inv in account_invoice:
                if inv.state == 'posted':
                    _logger.info("You cannot update a posted invoice.")
                if inv.state == 'draft':
                    _logger.info(
                        "Code is not available for updating invoices, please delete the particular invoice and import the invoice again.")
                if inv.state == 'cancel':
                    _logger.info("You cannot update a cancelled invoice.")

    def get_tax_state(self, line_amount_type):
        return {
            "Exclusive": "exclusive",
            "Inclusive": "inclusive",
            "NoTax": "no_tax"
        }.get(line_amount_type)

    @api.model
    def get_move_type(self, invoice_type):
        return {
            'ACCREC': 'out_invoice',
            'ACCPAY': 'in_invoice'
        }.get(invoice_type)

    @api.model
    def get_journal(self, invoice_type):
        journal_type = 'sale' if invoice_type == 'ACCREC' else 'purchase'
        return self.env['account.journal'].search([('type', '=', journal_type)], limit=1)

    def get_tax(self,tax_type, tax_use):
        tax = self.env['account.tax'].search([
            ('xero_tax_type_id', '=', tax_type),
            ('type_tax_use', '=', tax_use),
            ('price_include', '=', False),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        if not tax:
            self.import_tax()
            tax = self.env['account.tax'].search([
                ('xero_tax_type_id', '=', tax_type),
                ('type_tax_use', '=', tax_use),
                ('price_include', '=', False),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
        return [(6, 0, [tax.id])] if tax else False

    def get_account(self, account_code):
        account = self.env['account.account'].search([
            ('code', '=', account_code),
            ('company_ids', 'in', self.env.company.id)
        ], limit=1)
        if not account:
            self.import_accounts()
            account = self.env['account.account'].search([
                ('code', '=', account_code),
                ('company_ids', 'in', self.env.company.id)
            ], limit=1)
        return account.id if account else False

    @api.model
    def create_customer_for_invoice(self, cust, res_partner):
        dict_i = {
            'partner_id': res_partner.id,
            'xero_invoice_id': cust.get('InvoiceID'),
            'company_id': self.env.company.id,
            'currency_id': self.env['res.currency'].search([('name', '=', cust.get('CurrencyCode'))], limit=1).id,
            'journal_id': self.get_journal(cust.get('Type')).id,
            'tax_state': self.get_tax_state(cust.get('LineAmountTypes')),
            'state': 'draft' if cust.get('Status') in ['AUTHORISED', 'PAID'] else None,
            'xero_invoice_number': cust.get('InvoiceNumber'),
            'invoice_date_due': cust.get('DueDateString'),
            'invoice_date': cust.get('DateString'),
            'move_type': self.get_move_type(cust.get('Type')),
            'ref': cust.get('Reference'),
            'invoice_line_ids': []
        }

        invoice_type = dict_i['move_type']
        tax_state = dict_i['tax_state']

        if cust.get('LineItems'):
            order_lines = cust.get('LineItems') if isinstance(cust.get('LineItems'), list) else [cust.get('LineItems')]
            for i in order_lines:
                res_product = self.env['product.product'].search([('default_code', '=', i.get('ItemCode'))]) if i.get(
                    'ItemCode') else ''
                if not res_product and i.get('ItemCode'):
                    self.fetch_the_required_product(i.get('ItemCode'))
                    res_product = self.env['product.product'].search([('default_code', '=', i.get('ItemCode'))])

                invoice_line_vals = self.create_invoice_line(i, res_product, cust, invoice_type, tax_state)
                if invoice_line_vals:
                    dict_i['invoice_line_ids'].append((0, 0, invoice_line_vals))

        _logger.info("Xero Invoice Data :----------------> %s ", cust)
        _logger.info("Invoice Dictionary :----------------> %s ", dict_i)

        invoice_obj = self.env['account.move'].sudo().create(dict_i)
        if invoice_obj:
            if invoice_obj.state == 'draft':
                invoice_obj.action_post()
            _logger.info("Invoice Object created in odoo :  %s ", invoice_obj)
            if cust.get('InvoiceNumber'):
                _logger.info("Invoice Created Successfully...!!! INV NO = %s ", cust.get('InvoiceNumber'))
    @api.model
    def create_invoice_line(self, i, res_product, cust, invoice_type, tax_state):

        dict_ol = {}

        if res_product:
            dict_ol['product_id'] = res_product.id
        else:
            _logger.info("Product Not Defined.")

        dict_ol.update({
            'xero_invoice_line_id': i.get('LineItemID'),
            'discount': i.get('DiscountRate'),
            'quantity': i.get('Quantity', 0),
            'price_unit': i.get('UnitAmount'),
            'name': i.get('Description', 'NA')
        })

        if i.get('TaxType'):
            tax_use = 'sale' if invoice_type == 'out_invoice' else 'purchase'
            acc_tax = self.get_tax(i.get('TaxType'), tax_use)
            if tax_state == 'exclusive':
                dict_ol['tax_ids'] = acc_tax if acc_tax else [(6, 0, [])]
            elif tax_state == 'inclusive':
                dict_ol['tax_ids'] = acc_tax if acc_tax else [(6, 0, [])]
            elif tax_state == 'no_tax':
                dict_ol['tax_ids'] = [(6, 0, [])]

        if i.get('AccountCode'):
            acc_id_s = self.get_account(i.get('AccountCode'))
            if acc_id_s:
                dict_ol['account_id'] = acc_id_s
        elif not i.get('AccountCode') and not i.get('Quantity') and not i.get('UnitAmount'):
            if not self.revenue_default_account:
                raise ValidationError('Please set the Default Account in Xero Configuration.')
            dict_ol.update({'account_id': self.revenue_default_account.id, 'quantity': 1.0, 'price_unit': 0.0})
        elif not i.get('AccountCode') and not i.get('ItemCode'):
            if not self.revenue_default_account:
                raise ValidationError('Please set the Default Account in Xero Configuration.')
            dict_ol['account_id'] = self.revenue_default_account.id

        if i.get('ItemCode') and not i.get('AccountCode') and res_product:
            if invoice_type == 'out_invoice':
                dict_ol[
                    'account_id'] = res_product.property_account_income_id.id or res_product.categ_id.property_account_income_categ_id.id
            else:
                dict_ol[
                    'account_id'] = res_product.property_account_expense_id.id or res_product.categ_id.property_account_expense_categ_id.id

        return dict_ol

    def import_credit_notes(self,date_from=None):
        """IMPORT CREDIT NOTES(Customer refund bill and vendor refund bill) FROM XERO TO ODOO"""
        for i in range(10000):
            res = self.cn_main_function(i + 1,date_from)
            _logger.info("RESPONSE : %s", res)
            if not res:
                break;
        success_form = self.env.ref('xero_integration.import_successfull_view', False)
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

    @api.model
    def cn_main_function(self, page_no,date_from=None):
        _logger.info("CREDIT NOTE PAGE NO : %s", page_no)

        if date_from:
            date_from = datetime.datetime.strptime(str(date_from), '%Y-%m-%d').date()
        else:
            date_from = 0

        if date_from:
            url = 'https://api.xero.com/api.xro/2.0/CreditNotes?page=' + str(
                page_no) + '&where=Date>=DateTime(%s,%s,%s)' % (date_from.year, date_from.month, date_from.day)
        else:
            url = 'https://api.xero.com/api.xro/2.0/CreditNotes?page=' + str(page_no)
        data = self.get_data(url)

        if data:
            recs = []

            parsed_dict = json.loads(data.text)

            if parsed_dict.get('CreditNotes'):
                if parsed_dict.get('CreditNotes'):
                    record = parsed_dict.get('CreditNotes')
                    if isinstance(record, (dict,)):
                        if not (record.get('Status') == 'DRAFT' or record.get('Status') == 'DELETED' or record.get(
                                'Status') == 'VOIDED' or record.get('Status') == 'SUBMITTED'):
                            self.create_imported_credit_notes(record)
                    else:
                        for cust in parsed_dict.get('CreditNotes'):
                            if not (cust.get('Status') == 'DRAFT' or cust.get('Status') == 'DELETED' or cust.get(
                                    'Status') == 'VOIDED' or cust.get('Status') == 'SUBMITTED'):
                                self.create_imported_credit_notes(cust)
                    return True
            else:
                if page_no == 1:
                    raise ValidationError('There is no any credit note present in XERO.')
                else:
                    date_from = datetime.datetime.today().strftime('%Y-%m-%d')
                    return False
        elif data.status_code == 401:
            raise ValidationError(
                'Time Out..!!\n Please check your connection or error in application or refresh token.')

    @api.model
    def create_imported_credit_notes(self, cust):
        if cust.get('CreditNoteNumber'):
            _logger.info("PROCESSING CREDIT NOTE NUMBER : %s", cust.get('CreditNoteNumber'))
        _logger.info("PROCESSING CREDIT NOTE ID : %s", cust.get('CreditNoteID'))

        account_invoice = self.env['account.move'].search(
            [('xero_invoice_id', '=', cust.get('CreditNoteID')), ('company_id', '=', self.env.company.id)])
        if not account_invoice:

            res_partner = self.env['res.partner'].search(
                [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)], limit=1)

            if res_partner:
                self.create_customer_for_credit_note(cust, res_partner)
            else:
                self.fetch_the_required_customer(cust.get('Contact').get('ContactID'))
                res_partner2 = self.env['res.partner'].search(
                    [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)],
                    limit=1)
                if res_partner2:
                    self.create_customer_for_credit_note(cust, res_partner2)
        else:

            _logger.info("CREDIT NOTE OBJECT : %s", account_invoice)
            _logger.info("CREDIT NOTE STATE : %s", account_invoice.state)

            if account_invoice.state == 'posted':
                _logger.info("You cannot update a posted credit note.")
            if account_invoice.state == 'draft':
                _logger.info(
                    "Code is not available for updating credit note, please delete the particular credit note and import the credit notes again.")
            if account_invoice.state == 'cancel':
                _logger.info("You cannot update a cancelled credit note.")

    @api.model
    def create_customer_for_credit_note(self, cust, res_partner):
        dict_i = {
            'partner_id': res_partner.id,
            'xero_invoice_id': cust.get('CreditNoteID'),
            'company_id': self.env.company.id,
            'currency_id': self.env['res.currency'].search([('name', '=', cust.get('CurrencyCode'))],
                                                           limit=1).id if cust.get('CurrencyCode') else False,
            'xero_invoice_number': cust.get('CreditNoteNumber'),
            'invoice_date': cust.get('DateString'),
            'ref': cust.get('Reference'),
            'invoice_line_ids': []
        }

        # Determine journal
        journal_type = 'sale' if cust.get('Type') == 'ACCRECCREDIT' else 'purchase'
        dict_i['journal_id'] = self.env['account.journal'].search([('type', '=', journal_type)], limit=1).id

        # Determine tax state
        tax_states = {
            'Exclusive': 'exclusive',
            'Inclusive': 'inclusive',
            'NoTax': 'no_tax'
        }
        dict_i['tax_state'] = tax_states.get(cust.get('LineAmountTypes'))

        # Determine invoice state and move type
        dict_i['state'] = 'draft' if cust.get('Status') in ['AUTHORISED', 'PAID'] else 'cancel'
        dict_i['move_type'] = 'out_refund' if cust.get('Type') == 'ACCRECCREDIT' else 'in_refund'

        # Process line items
        invoice_type = dict_i['move_type']
        tax_state = dict_i['tax_state']

        line_items = cust.get('LineItems', [])
        if not isinstance(line_items, list):
            line_items = [line_items]

        for item in line_items:
            item_code = item.get('ItemCode')
            res_product = self.env['product.product'].search([('default_code', '=', item_code)]) if item_code else ''

            if not res_product and item_code:
                self.fetch_the_required_product(item_code)
                res_product = self.env['product.product'].search([('default_code', '=', item_code)])

            invoice_line_vals = self.create_credit_note_invoice_line(item, res_product, cust, invoice_type, tax_state)
            if invoice_line_vals:
                dict_i['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Create and post the credit note
        invoice_obj = self.env['account.move'].create(dict_i)
        if invoice_obj and invoice_obj.state == 'draft':
            invoice_obj.action_post()
            _logger.info("\nCredit Note Created Successfully...!!! CN = %s", cust.get('CreditNoteNumber'))

    def create_credit_note_invoice_line(self, i, res_product, cust, invoice_type, tax_state):
        dict_ol = {}

        dict_ol['product_id'] = res_product.id if res_product else None
        dict_ol['xero_invoice_line_id'] = i.get('LineItemID')
        dict_ol['discount'] = i.get('DiscountRate')
        dict_ol['quantity'] = i.get('Quantity', 0)
        dict_ol['price_unit'] = i.get('UnitAmount')
        dict_ol['name'] = i.get('Description', 'NA')

        def get_tax(type_use, price_include):
            return self.env['account.tax'].search([
                ('xero_tax_type_id', '=', i.get('TaxType')),
                ('type_tax_use', '=', type_use),
                ('price_include', '=', price_include),
                ('company_id', '=', self.env.company.id)
            ], limit=1)

        if i.get('TaxType'):
            tax_type_use = 'sale' if invoice_type == 'out_refund' else 'purchase'
            price_include = tax_state == 'inclusive'
            acc_tax = get_tax(tax_type_use, price_include)

            if not acc_tax:
                self.import_tax()
                acc_tax = get_tax(tax_type_use, price_include)

            dict_ol['tax_ids'] = [(6, 0, [acc_tax.id])] if acc_tax else [(6, 0, [])]
        else:
            dict_ol['tax_ids'] = [(6, 0, [])]

        if i.get('AccountCode'):
            acc_id_s = self.env['account.account'].search([
                ('code', '=', i.get('AccountCode')),
                ('company_ids', 'in', self.env.company.id)
            ], limit=1)

            if not acc_id_s:
                self.import_accounts()
                acc_id_s = self.env['account.account'].search([
                    ('code', '=', i.get('AccountCode')),
                    ('company_ids', 'in', self.env.company.id)
                ], limit=1)

            dict_ol['account_id'] = acc_id_s.id if acc_id_s else None

        elif not i.get('AccountCode') and not i.get('Quantity') and not i.get('UnitAmount'):
            if not self.revenue_default_account:
                raise ValidationError('Please Set the Default Account in Xero Configuration.')
            dict_ol.update({
                'account_id': self.revenue_default_account.id,
                'quantity': 1.0,
                'price_unit': 0.0
            })

        if i.get('ItemCode') and not i.get('AccountCode') and res_product:
            if invoice_type == 'out_refund':
                dict_ol[
                    'account_id'] = res_product.property_account_income_id.id or res_product.categ_id.property_account_income_categ_id.id
            else:
                dict_ol[
                    'account_id'] = res_product.property_account_expense_id.id or res_product.categ_id.property_account_expense_categ_id.id

        return dict_ol

    @api.model
    def check_if_product_present(self, cust):
        if cust.get('LineItems'):
            if cust.get('LineItems'):
                order_lines = cust.get('LineItems')
                if isinstance(order_lines, (dict,)):
                    i = cust.get('LineItems')
                    if i.get('ItemCode'):
                        return True
                    else:
                        return False
                else:
                    for i in cust.get('LineItems'):
                        if i.get('ItemCode'):
                            return True
                        else:
                            return False

    def import_sale_order(self, qo_number=False,date_from=None):
        """IMPORT SALE ORDER FROM XERO TO ODOO"""
        for i in range(10000):
            if self:
                res = self.so_main_function(i + 1, qo_number,date_from)
            else:
                company = self.env['res.users'].search([('id', '=', self._uid)]).company_id
                res = company.so_main_function(i + 1, qo_number)
            _logger.info("RESPONSE : %s", res)

            if not res:
                break;
        success_form = self.env.ref('xero_integration.import_successfull_view', False)
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

    @api.model
    def so_main_function(self, page_no, qo_number,date_from=None):
        _logger.info("SALE PAGE NO : %s", page_no)
        if date_from:
            date_from = datetime.datetime.strptime(str(date_from), '%Y-%m-%d').date()
        else:
            date_from = 0

        if qo_number:
            url = 'https://api.xero.com/api.xro/2.0/Quotes?QuoteNumber=%s' % (qo_number)
        elif date_from:
            url = 'https://api.xero.com/api.xro/2.0/Quotes?DateFrom=%s' % (date_from)
        else:
            url = 'https://api.xero.com/api.xro/2.0/Quotes?page=' + str(page_no)

        data = self.get_data(url)
        if data:
            recs = []

            parsed_dict = json.loads(data.text)
            if parsed_dict.get('Quotes'):
                record = parsed_dict.get('Quotes')
                if isinstance(record, (dict,)):
                    product_exist = self.check_if_product_present(record)
                    if product_exist:
                        self.create_imported_sale_order(record)
                    else:
                        if record.get('Quotes'):
                            _logger.info("SALES ORDER DOES NOT CONTAIN ANY PRODUCT. PO = %s", record.get('Quotes'))

                else:
                    for cust in parsed_dict.get('Quotes'):
                        product_exist = self.check_if_product_present(cust)
                        if product_exist:
                            self.create_imported_sale_order(cust)
                        else:
                            if cust.get('Quotes'):
                                _logger.info("SALES ORDER DOES NOT CONTAIN ANY PRODUCT. PO = %s", cust.get('Quotes'))

                # print("record:::::::::::::::::::",record)
                if date_from:
                    date_from = datetime.datetime.today().strftime('%Y-%m-%d')
                    return False
                return True
            else:
                if page_no == 1:
                    raise ValidationError('There is no any sale order present in XERO.')
                else:
                    date_from = datetime.datetime.today().strftime('%Y-%m-%d')
                    return False

        elif data.status_code == 401:
            raise ValidationError(
                'Time Out..!!\n Please check your connection or error in application or refresh token.')

    @api.model
    def create_imported_sale_order(self, cust):
        sale_order = self.env['sale.order'].search(
            [('xero_sale_id', '=', cust.get('QuoteID')), ('company_id', '=', self.env.company.id)])

        if not sale_order:
            res_partner = self.env['res.partner'].search(
                [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)], limit=1)

            if res_partner:
                self.create_customer_for_sale_order(cust, res_partner)
            else:
                self.fetch_the_required_customer(cust.get('Contact').get('ContactID'))
                res_partner = self.env['res.partner'].search(
                    [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)],
                    limit=1)

                if res_partner:
                    self.create_customer_for_sale_order(cust, res_partner)
        else:
            res_partner = self.env['res.partner'].search(
                [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)], limit=1)
            if res_partner:
                self.update_customer_for_sale_order(cust, res_partner, sale_order)
            else:
                self.fetch_the_required_customer(cust.get('Contact').get('ContactID'))
                res_partner = self.env['res.partner'].search(
                    [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)],
                    limit=1)
                if res_partner:
                    self.update_customer_for_sale_order(cust, res_partner, sale_order)

    @api.model
    def get_sale_order_state(self, status):
        return {
            'DRAFT': 'draft',
            'DELETED': 'cancel',
            'DECLINED': 'cancel',
            'SENT': 'sent',
            'ACCEPTED': 'sale',
            'INVOICED': 'sale'
        }.get(status, 'draft')  # Default to 'draft' if not found

    @api.model
    def create_customer_for_sale_order(self, cust, res_partner):
        dict_s = {
            'partner_id': res_partner.id if cust.get('QuoteID') else None,
            'xero_sale_id': cust.get('QuoteID'),
            'tax_state': self.get_tax_state(cust.get('LineAmountTypes')),
            'state': self.get_sale_order_state(cust.get('Status')),
            'name': cust.get('QuoteNumber'),
            'date_order': cust.get('DateString')[0:10] if cust.get('DateString') else None,
            'client_order_ref': cust.get('Reference')
        }

        dict_s = {k: v for k, v in dict_s.items() if v is not None}  # Remove None values

        so_obj = self.env['sale.order'].create(dict_s)
        _logger.info(
            "Sale Order %s successfully: SO = %s ",
            "Created" if so_obj else "Not Created",
            cust.get('QuoteNumber')
        )

        order_lines = cust.get('LineItems') or []
        if not isinstance(order_lines, list):
            order_lines = [order_lines]

        for i in order_lines:
            item_code = i.get('ItemCode')
            res_product = self.env['product.product'].search([('default_code', '=', item_code)])

            if not res_product and item_code:
                self.fetch_the_required_product(item_code)
                res_product = self.env['product.product'].search([('default_code', '=', item_code)])

            if res_product:
                self.create_sale_order_line(i, so_obj, res_product)
            else:
                _logger.info('[SO ORDER LINE] Item Code Not defined or Product not found for Item Code: %s', item_code)

    @api.model
    def update_customer_for_sale_order(self, cust, res_partner, sale_order):
        dict_s = {
            'partner_id': res_partner.id if cust.get('QuoteID') else None,
            'xero_sale_id': cust.get('QuoteID'),
            'state': self.get_sale_order_state(cust.get('Status')),
            'tax_state': self.get_tax_state(cust.get('LineAmountTypes')),
            'name': cust.get('QuoteNumber'),
            'date_order': cust.get('DateString')[0:10] if cust.get('DateString') else None,
            'notes': cust.get('DeliveryInstructions'),
            'client_order_ref': cust.get('Reference')
        }

        dict_s = {k: v for k, v in dict_s.items() if v is not None}  # Remove None values
        s_o = sale_order.write(dict_s)
        _logger.info(
            "Sale Order %s successfully: SO = %s ",
            "Updated" if s_o else "Not Updated",
            cust.get('QuoteNumber')
        )

        order_lines = cust.get('LineItems') or []
        if not isinstance(order_lines, list):
            order_lines = [order_lines]

        for i in order_lines:
            item_code = i.get('ItemCode')
            res_product = self.env['product.product'].search([('default_code', '=', item_code)])

            if not res_product and item_code:
                self.fetch_the_required_product(item_code)
                res_product = self.env['product.product'].search([('default_code', '=', item_code)])

            if res_product:
                self.update_sale_order_line(i, sale_order, res_product, cust)
            else:
                _logger.info('[SO ORDER LINE] Item Code Not defined or Product not found for Item Code: %s', item_code)

    @api.model
    def create_sale_order_line(self, i, so_obj, res_product):

        def get_tax_id(tax_type, tax_state):
            tax_domain = [('xero_tax_type_id', '=', tax_type), ('type_tax_use', '=', 'sale'),
                          ('company_id', '=', self.env.company.id)]
            tax_domain.append(('price_include', '=', tax_state == 'inclusive'))
            acc_tax = self.env['account.tax'].search(tax_domain, limit=1)
            if not acc_tax:
                self.import_tax()
                acc_tax = self.env['account.tax'].search(tax_domain, limit=1)
            return [(6, 0, [acc_tax.id])] if acc_tax else False

        dict_l = {
            'order_id': so_obj.id,
            'product_id': res_product.id,
            'product_uom_qty': i.get('Quantity', 1),
            'product_uom_id': 1,
            'price_unit': float(i.get('UnitAmount', 0.0)),
            'name': i.get('Description', 'NA')
        }

        if i.get('TaxType'):
            dict_l['tax_id'] = get_tax_id(i['TaxType'], so_obj.tax_state)

        if i.get('LineItemID'):
            dict_l['xero_sale_line_id'] = i['LineItemID']

        create_p = self.env['sale.order.line'].create(dict_l)
        if create_p:
            _logger.info(_('Sale line Created successfully'))
        else:
            _logger.info(_('Sale line not Created successfully'))

    @api.model
    def update_sale_order_line(self, i, sale_order, res_product, cust):
        def get_sale_tax(tax_type, tax_state):
            tax_domain = [('xero_tax_type_id', '=', tax_type), ('type_tax_use', '=', 'sale'),
                          ('company_id', '=', self.env.company.id)]
            if tax_state == 'inclusive':
                tax_domain.append(('price_include', '=', True))
            elif tax_state == 'exclusive':
                tax_domain.append(('price_include', '=', False))
            acc_tax = self.env['account.tax'].search(tax_domain, limit=1)
            if not acc_tax:
                self.import_tax()
                acc_tax = self.env['account.tax'].search(tax_domain, limit=1)
            return [(6, 0, [acc_tax.id])] if acc_tax else False

        so_order_line = self.env['sale.order.line'].search(
            [('product_id', '=', res_product.id),
             ('order_id', '=', sale_order.id), ('company_id', '=', self.env.company.id)], limit=1)

        quantity = i.get('Quantity', 1)
        ol_qb_id = i.get('LineItemID', 0)
        sp = float(i.get('UnitAmount', 0.0))
        description = i.get('Description', 'NA')
        taxes_id = get_sale_tax(i.get('TaxType'), sale_order.tax_state) if i.get('TaxType') else False
        if so_order_line:
            write_values = {
                'product_id': res_product.id,
                'name': description,
                'product_uom_qty': quantity,
                'xero_sale_line_id': ol_qb_id,
                'product_uom_id': 1,
                'price_unit': sp,
            }
            if taxes_id:
                write_values['tax_id'] = taxes_id

            res = so_order_line.write(write_values)
            _logger.info(_('Order line updated successfully')) if res else _logger.info(
                _('Order line not updated successfully'))
        else:
            dict_l = {
                'order_id': sale_order.id,
                'product_id': res_product.id,
                'product_uom_qty': quantity,
                'xero_sale_line_id': ol_qb_id,
                'product_uom_id': 1,
                'price_unit': sp,
                'name': description,
            }
            if taxes_id:
                dict_l['tax_id'] = taxes_id

            create_p = self.env['sale.order.line'].create(dict_l)
            _logger.info(_('Sale line Created Successfully')) if create_p else _logger.info(
                _('Sale line not Created Successfully'))

    def import_purchase_order(self,date_from=None):
        """IMPORT PURCHASE ORDER FROM XERO TO ODOO"""
        for i in range(10000):
            res = self.po_main_function(i + 1,date_from)
            _logger.info("RESPONSE : %s", res)

            if not res:
                break;
        success_form = self.env.ref('xero_integration.import_successfull_view', False)
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

    @api.model
    def po_main_function(self, page_no,date_from=None):
        _logger.info("PURCHASE PAGE NO : %s", page_no)
        if date_from:
            date_from = datetime.datetime.strptime(str(date_from), '%Y-%m-%d').date()
        else:
            date_from = 0

        if date_from:
            url = 'https://api.xero.com/api.xro/2.0/PurchaseOrders?DateFrom=%s' % (date_from)
        else:
            url = 'https://api.xero.com/api.xro/2.0/PurchaseOrders?page=' + str(page_no)

        data = self.get_data(url)
        if data:
            recs = []

            parsed_dict = json.loads(data.text)
            if parsed_dict.get('PurchaseOrders'):
                record = parsed_dict.get('PurchaseOrders')
                if isinstance(record, (dict,)):
                    product_exist = self.check_product_present_po(record)
                    if product_exist:
                        self.create_imported_purchase_order(record)
                        self._cr.commit()
                    else:
                        if record.get('PurchaseOrderNumber'):
                            _logger.info("PURCHASE ORDER DOES NOT CONTAIN ANY PRODUCT. PO = %s",
                                         record.get('PurchaseOrderNumber'))

                else:
                    for cust in parsed_dict.get('PurchaseOrders'):
                        product_exist = self.check_product_present_po(cust)
                        if product_exist:
                            self.create_imported_purchase_order(cust)
                            self._cr.commit()
                        else:
                            if cust.get('PurchaseOrderNumber'):
                                _logger.info("PURCHASE ORDER DOES NOT CONTAIN ANY PRODUCT. PO = %s",
                                             cust.get('PurchaseOrderNumber'))

                if date_from:
                    date_from = datetime.datetime.today().strftime('%Y-%m-%d')
                    return False
                return True
            else:
                if page_no == 1:
                    raise ValidationError('There is no any purchase order present in XERO.')
                else:
                    date_from = datetime.datetime.today().strftime('%Y-%m-%d')
                    return False

        elif data.status_code == 401:
            raise ValidationError(
                'Time Out..!!\n Please check your connection or error in application or refresh token.')

    @api.model
    def check_product_present_po(self, cust):
        if cust.get('LineItems'):
            order_lines = cust.get('LineItems')
            if isinstance(order_lines, (dict,)):
                i = cust.get('LineItems')
                if i.get('ItemCode'):
                    return True
                else:
                    return False
            else:
                for i in cust.get('LineItems'):
                    if i.get('ItemCode'):
                        continue
                    else:
                        return False
        return True

    @api.model
    def create_imported_purchase_order(self, cust):
        purchase_order = self.env['purchase.order'].search(
            [('xero_purchase_id', '=', cust.get('PurchaseOrderID')), ('company_id', '=', self.env.company.id)])

        if not purchase_order:
            res_partner = self.env['res.partner'].search(
                [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)], limit=1)

            if res_partner:
                self.create_customer_for_purchase_order(cust, res_partner)
            else:
                self.fetch_the_required_customer(cust.get('Contact').get('ContactID'))
                res_partner = self.env['res.partner'].search(
                    [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)],
                    limit=1)

                if res_partner:
                    self.create_customer_for_purchase_order(cust, res_partner)
        else:

            res_partner = self.env['res.partner'].search(
                [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)], limit=1)
            if res_partner:
                self.update_customer_for_purchase_order(cust, res_partner, purchase_order)
            else:
                self.fetch_the_required_customer(cust.get('Contact').get('ContactID'))
                res_partner = self.env['res.partner'].search(
                    [('xero_cust_id', '=', cust.get('Contact').get('ContactID')), ('company_id', '=', self.env.company.id)],
                    limit=1)
                if res_partner:
                    self.update_customer_for_purchase_order(cust, res_partner, purchase_order)

    @api.model
    def create_customer_for_purchase_order(self, cust, res_partner):
        dict_s = {
            'partner_id': res_partner.id,
            'xero_purchase_id': cust.get('PurchaseOrderID'),
            'name': cust.get('PurchaseOrderNumber'),
            'note': cust.get('DeliveryInstructions'),
            'partner_ref': cust.get('Reference'),
            'date_order': cust.get('DateString', '')[0:10] if cust.get('DateString') else False
        }

        line_amount_types = {
            "Exclusive": 'exclusive',
            "Inclusive": 'inclusive',
            "NoTax": 'no_tax'
        }
        dict_s['tax_state'] = line_amount_types.get(cust.get('LineAmountTypes'))

        status_mapping = {
            'DRAFT': 'draft',
            'DELETED': 'cancel',
            'AUTHORISED': 'draft',
            'BILLED': 'draft',
            'SUBMITTED': 'draft'
        }
        dict_s['state'] = status_mapping.get(cust.get('Status'))

        so_obj = self.env['purchase.order'].create(dict_s)
        if so_obj:
            if cust.get('Status') in ['AUTHORISED', 'BILLED', 'SUBMITTED']:
                so_obj.button_confirm()
            _logger.info("Purchase Order Created successfully  PO = %s ", cust.get('PurchaseOrderNumber'))
        else:
            _logger.info("Purchase Order Not Created successfully  PO = %s ", cust.get('PurchaseOrderNumber'))

        def process_line_item(i):
            res_product = self.env['product.product'].search([('default_code', '=', i.get('ItemCode'))])
            if not res_product and i.get('ItemCode'):
                self.fetch_the_required_product(i.get('ItemCode'))
                res_product = self.env['product.product'].search([('default_code', '=', i.get('ItemCode'))])
            if res_product:
                self.create_purchase_order_line(i, so_obj, res_product)
            else:
                _logger.info('[PO ORDER LINE] Item Code Not defined.')

        order_lines = cust.get('LineItems')
        if order_lines:
            if isinstance(order_lines, dict):
                process_line_item(order_lines)
            else:
                for i in order_lines:
                    process_line_item(i)

    @api.model
    def update_customer_for_purchase_order(self, cust, res_partner, purchase_order):
        dict_s = {
            'partner_id': res_partner.id if cust.get('PurchaseOrderID') else None,
            'xero_purchase_id': cust.get('PurchaseOrderID'),
            'state': 'draft',
            'tax_state': {
                'Exclusive': 'exclusive',
                'Inclusive': 'inclusive',
                'NoTax': 'no_tax'
            }.get(cust.get('LineAmountTypes'), None),
            'name': cust.get('PurchaseOrderNumber'),
            'date_order': cust.get('DateString')[:10] if cust.get('DateString') else None,
            'note': cust.get('DeliveryInstructions'),
            'partner_ref': cust.get('Reference')
        }
        dict_s = {k: v for k, v in dict_s.items() if v is not None}

        p_o = purchase_order.write(dict_s)
        if p_o:
            if purchase_order.state == 'draft' and cust.get('Status') in ['AUTHORISED', 'BILLED', 'SUBMITTED']:
                purchase_order.button_confirm()
            _logger.info("Purchase Order Updated successfully  PO = %s ", cust.get('PurchaseOrderNumber'))
        else:
            _logger.info("Purchase Order Not Updated successfully  PO = %s ", cust.get('PurchaseOrderNumber'))

        order_lines = cust.get('LineItems', [])
        if isinstance(order_lines, dict):
            order_lines = [order_lines]

        for i in order_lines:
            item_code = i.get('ItemCode')
            if not item_code:
                _logger.info('[PO ORDER LINE] Item Code Not defined.')
                continue

            res_product = self.env['product.product'].search([('default_code', '=', item_code)])
            if not res_product:
                self.fetch_the_required_product(item_code)
                res_product = self.env['product.product'].search([('default_code', '=', item_code)])

            if res_product:
                self.update_purchase_order_line(i, purchase_order, res_product, cust)
            else:
                _logger.info('[PO ORDER LINE] Product not found after fetching for Item Code: %s', item_code)

    @api.model
    def create_purchase_order_line(self, i, so_obj, res_product):
        """  CREATES PURCHASE ORDER LINES FOR THE FIRST TIME  """

        dict_l = {
            'order_id': so_obj.id,
            'product_id': res_product.id,
            'product_qty': i.get('Quantity', 0),
            'xero_purchase_line_id': i.get('LineItemID'),
            'date_planned': so_obj.date_order,
            'product_uom_id': 1,
            'price_unit': float(i.get('UnitAmount', 0.0)),
            'name': i.get('Description', 'NA')
        }

        tax_domain = [('xero_tax_type_id', '=', i.get('TaxType')), ('type_tax_use', '=', 'purchase'),
                      ('company_id', '=', self.id)]
        if so_obj.tax_state == 'inclusive':
            tax_domain.append(('price_include', '=', True))
        elif so_obj.tax_state in ('exclusive', 'no_tax'):
            tax_domain.append(('price_include', '=', False))

        acc_tax = self.env['account.tax'].search(tax_domain, limit=1)
        if not acc_tax:
            self.import_tax()
            acc_tax = self.env['account.tax'].search(tax_domain, limit=1)
        if acc_tax:
            dict_l['taxes_id'] = [(6, 0, [acc_tax.id])]

        create_p = self.env['purchase.order.line'].create(dict_l)
        _logger.info(_("Purchase line %s successfully"), "Created" if create_p else "not Created")

    @api.model
    def update_purchase_order_line(self, i, purchase_order, res_product, cust):
        p_order_line = self.env['purchase.order.line'].search(
            [('product_id', '=', res_product.id),
             ('order_id', '=', purchase_order.id),
             ('company_id', '=', self.env.company.id)], limit=1)

        date_planned = purchase_order.date_order
        if cust.get('DeliveryDateString'):
            try:
                xero_datetime = datetime.datetime.strptime(cust.get('DeliveryDateString'), '%Y-%m-%dT%H:%M:%S')
                date_planned = xero_datetime
            except ValueError:
                _logger.warning("Invalid DeliveryDateString format")

        def get_purchase_tax(i, tax_state):
            acc_tax = self.env['account.tax'].search([
                ('xero_tax_type_id', '=', i.get('TaxType')),
                ('type_tax_use', '=', 'purchase'),
                ('price_include', '=', tax_state == 'inclusive'),
                ('company_id', '=', self.env.company.id)], limit=1)
            if not acc_tax:
                self.import_tax()
                acc_tax = self.env['account.tax'].search([
                    ('xero_tax_type_id', '=', i.get('TaxType')),
                    ('type_tax_use', '=', 'purchase'),
                    ('price_include', '=', tax_state == 'inclusive'),
                    ('company_id', '=', self.env.company.id)], limit=1)
            return [(6, 0, [acc_tax.id])] if acc_tax else False

        quantity = i.get('Quantity', 0)
        taxes_id = get_purchase_tax(i, purchase_order.tax_state) if i.get('TaxType') else False
        ol_qb_id = i.get('LineItemID', False)
        sp = float(i.get('UnitAmount', 0.0))
        description = i.get('Description', 'NA')

        if p_order_line:
            p_order_line.update({
                'product_id': res_product.id,
                'name': description,
                'product_qty': quantity,
                'xero_purchase_line_id': ol_qb_id,
                'product_uom_id': 1,
                'price_unit': sp,
                'taxes_id': taxes_id or False,
                'date_planned': date_planned
            })
            _logger.info("Purchase line updated successfully")
        else:
            dict_l = {
                'order_id': purchase_order.id,
                'product_id': res_product.id,
                'product_qty': quantity,
                'xero_purchase_line_id': ol_qb_id,
                'product_uom_id': 1,
                'price_unit': sp,
                'name': description,
                'date_planned': date_planned,
                'taxes_id': taxes_id or False
            }

            create_p = self.env['purchase.order.line'].create(dict_l)
            if create_p:
                _logger.info("Purchase line Created Successfully")
            else:
                _logger.info("Purchase line not Created Successfully")

    def import_payments_cron(self):
        company = self.env.company
        import_payments_from = company.import_payments_from
        self.env['account.payment'].import_payments(import_payments_from, company)

    def import_invoice_cron(self):
        company = self.env['res.users'].search([('id', '=', self._uid)]).company_id
        company.import_invoice()

    def import_manual_journal_cron(self):
        company = self.env['res.users'].search([('id', '=', self._uid)]).company_id
        company.import_manual_journals()

    def write(self, values):
        res = super(ResCompany, self).write(values)
        return res

