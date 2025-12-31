import logging
import requests
import json
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class XeroInvoice(models.Model):
    _inherit = 'account.move'

    tax_state = fields.Selection(selection=[
        ('inclusive', 'Tax Inclusive'),
        ('exclusive', 'Tax Exclusive'),
        ('no_tax', 'No Tax')],
        string='Tax Status', default='no_tax')
    xero_cust_id = fields.Char(string="Xero Customer Id")
    xero_invoice_id = fields.Char(string="Xero Invoice Id", copy=False)
    xero_invoice_number = fields.Char(string="Xero Invoice Number", copy=False)

    @api.onchange('tax_state')
    def onchange_tax_status(self):
        for line_id in self.invoice_line_ids:
            if self.tax_state == 'inclusive':
                line_id.inclusive = True
            elif self.tax_state == 'exclusive':
                line_id.inclusive = False

    @api.model_create_multi
    def create(self, values):
        moves = super(XeroInvoice, self).create(values)
        for move in moves:
            if move.line_ids:
                tax_lines = move.line_ids.filtered(lambda x: x.tax_ids)
                if tax_lines and tax_lines[0].inclusive:
                    move.tax_state = 'exclusive'
                elif tax_lines:
                    move.tax_state = 'inclusive'

        return moves

    def get_head(self):
        xero_config = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id
        xero_token = self.env['xero.token'].search([('company_id', '=', self.env.company.id)], limit=1)
        client_id = xero_config.xero_client_id
        client_secret = xero_config.xero_client_secret

        data = client_id + ":" + client_secret
        encodedBytes = base64.b64encode(data.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")
        headers = {
            'Authorization': "Bearer " + str(xero_token.xero_oauth_token),
            'Xero-tenant-id': xero_config.xero_tenant_id,
            'Accept': 'application/json'

        }
        if not client_id or not client_secret or not xero_token or not xero_token.xero_oauth_token:
            raise UserError('Missing Data - {header}'.format(header=headers))
        return headers

    @api.model
    def exportInvoice(self, payment_export=None, cron=None):
        """export account invoice to QBO"""
        headers = self.get_head()
        xero_config = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id

        if self._context.get('active_ids') and not payment_export:
            invoice = self.browse(self._context.get('active_ids'))
        else:
            invoice = self

        for t in invoice:
            if (t.move_type == 'out_refund') or (t.move_type == 'in_refund'):
                self.exportCreditNote(payment_export=payment_export, cron=cron)
            elif (t.move_type == 'out_invoice') or (t.move_type == 'in_invoice'):
                if not t.xero_invoice_id:
                    if t.state == 'posted':
                        values = t.prepare_invoice_export_dict()
                        vals = self.remove_note_section(values)
                        parsed_dict = json.dumps(vals)
                        _logger.info("\n\nInvoice parsed_dict :   {} ".format(parsed_dict))
                        url = 'https://api.xero.com/api.xro/2.0/Invoices?unitdp=4'
                        data = requests.request('PUT', url=url, data=parsed_dict, headers=headers)

                        _logger.info("Response 1 From Server :{} {} {}".format(data, data.status_code, data.text))

                        if data.status_code == 200:
                            response_data = json.loads(data.text)
                            self.env['xero.error.log'].success_log(record=t, name='Invoices Export')

                            if response_data.get('Invoices'):
                                t.xero_invoice_number = response_data.get('Invoices')[0].get('InvoiceNumber')
                                t.xero_invoice_id = response_data.get('Invoices')[0].get('InvoiceID')
                                self._cr.commit()
                                _logger.info(_("Exported successfully to XERO"))

                        elif data.status_code == 400:
                            try:
                                error_msg = data.text + ' ' + vals
                            except:
                                error_msg = data.text
                            self.env['xero.error.log'].error_log(record=t, name='Invoices Export', error=error_msg)
                            self._cr.commit()
                            self.show_error_message(data)

                        else:
                            raise UserError(
                                f"exportInvoice - error posting to Xero.  Code: {data.status_code}")

                    else:
                        if not cron:
                            raise ValidationError(_("Only Posted state Invoice is exported to Xero."))
                else:
                    if not cron:
                        raise ValidationError(
                            _("%s Invoice is already exported to Xero. Please, export a different invoice." % t.name))

            elif t.move_type == 'entry':  # Manual Journal Entry
                if not t.xero_invoice_id:
                    # print('\n\nNot Exported Yet\n\n')
                    if t.state == 'posted':
                        # print('\n\nIs Posted\n\n')
                        values = t.prepare_manual_journal_export_dict()
                        parsed_dict = json.dumps(values)

                        _logger.info("\n\nPrepared Dictionary :   {} ".format(parsed_dict))

                        url = 'https://api.xero.com/api.xro/2.0/ManualJournals?unitdp=4'
                        data = requests.request('PUT', url=url, data=parsed_dict, headers=headers)
                        _logger.info("Response 2 From Server :{} {}".format(data.status_code, data.text))

                        if data.status_code == 200:
                            self.env['xero.error.log'].success_log(record=t, name='ManualJournals Export')
                            response_data = json.loads(data.text)

                            if response_data.get('ManualJournals'):
                                # t.xero_invoice_number = response_data.get('ManualJournals')[0].get('ManualJournalID')
                                t.xero_invoice_id = response_data.get('ManualJournals')[0].get('ManualJournalID')
                                self._cr.commit()
                                _logger.info(_("Exported successfully to XERO"))

                        elif data.status_code == 400:
                            self.env['xero.error.log'].error_log(record=t, name='ManualJournals Export',
                                                                 error=data.text)
                            self._cr.commit()
                            self.show_error_message(data)

                        elif data.status_code == 401 and not cron:
                            raise ValidationError(
                                "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")

                    else:
                        if not cron:
                            raise ValidationError(_("Only Posted state Invoice is exported to Xero."))
                else:
                    if not cron:
                        raise ValidationError(
                            _("%s Manual Journal is already exported to Xero. Please, export a different Manual Journal." % t.name))

        success_form = self.env.ref('xero_integration.export_successfull_view', False)
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
    def exportCreditNote(self, payment_export=None, cron=None):
        xero_config = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id
        if self._context.get('active_ids') and not payment_export:
            invoice = self.browse(self._context.get('active_ids')).filtered(
                lambda x: x.move_type in ['in_refund', 'out_refund'])
        else:
            invoice = self

        for t in invoice:
            if not t.xero_invoice_id:
                if t.state == 'posted':
                    values = t.prepare_credit_note_export_dict()
                    vals = self.remove_note_section(values)
                    parsed_dict = json.dumps(vals)
                    _logger.info(_("PARSED DICT : %s %s" % (parsed_dict, type(parsed_dict))))
                    url = 'https://api.xero.com/api.xro/2.0/CreditNotes?unitdp=4'
                    data = self.post_data(url, parsed_dict)
                    _logger.info('Response From Server : {}'.format(data.text))

                    if data.status_code == 200:
                        self.env['xero.error.log'].success_log(record=t, name='CreditNote Export')

                        parsed_data = json.loads(data.text)
                        if parsed_data:
                            if parsed_data.get('CreditNotes'):
                                t.xero_invoice_number = parsed_data.get('CreditNotes')[0].get('CreditNoteNumber')
                                t.xero_invoice_id = parsed_data.get(
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
                else:
                    raise ValidationError(_("Only Posted state Credit Notes is exported to Xero."))
            else:
                raise ValidationError(_(
                    "%s Credit Notes is already exported to Xero. Please, export a different credit note." % t.name))

        success_form = self.env.ref('xero_integration.export_successfull_view', False)
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
    def prepare_credit_note_export_dict(self):
        company = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id

        if self.partner_id:
            cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)
        else:
            cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)

        vals = {}
        lst_line = []
        origin_credit_note = ''
        type = ''
        status = ''
        tax_state = ''
        if self.move_type == 'in_invoice':
            type = 'ACCPAY'
        elif self.move_type == 'out_invoice':
            type = 'ACCREC'
        elif self.move_type == 'in_refund':
            type = 'ACCPAYCREDIT'
        elif self.move_type == 'out_refund':
            type = 'ACCRECCREDIT'
            if self.invoice_origin:
                origin_credit_note = self.invoice_origin

        if self.tax_state:
            if self.tax_state == 'inclusive':
                tax_state = 'Inclusive'
            elif self.tax_state == 'exclusive':
                tax_state = 'Exclusive'
            elif self.tax_state == 'no_tax':
                tax_state = 'NoTax'

        if self.state:
            if self.state == 'posted':
                status = 'AUTHORISED'

            if company.invoice_status:
                if company.invoice_status == 'draft':
                    status = 'DRAFT'
                if company.invoice_status == 'authorised':
                    status = 'AUTHORISED'

        if len(self.invoice_line_ids) == 1:
            single_line = self.invoice_line_ids

            qty = abs(single_line.quantity)
            price = single_line.price_unit if single_line.quantity > 0 else 0 - single_line.price_unit

            if single_line.account_id:
                if single_line.account_id.xero_account_id:
                    account_code = single_line.account_id.code
                else:
                    self.env['account.account'].create_account_ref_in_xero(single_line.account_id)
                    if single_line.account_id.xero_account_id:
                        account_code = single_line.account_id.code

            if ((
                    single_line.move_id.move_type == 'out_refund' and single_line.product_id and not company.export_invoice_without_product) or (
                    single_line.move_id.move_type == 'in_refund' and single_line.product_id and not company.export_bill_without_product)):
                if single_line.product_id.xero_product_id:
                    _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
                elif not single_line.product_id.xero_product_id:
                    self.env['product.product'].get_xero_product_ref(single_line.product_id)

                if single_line.tax_ids:
                    line_tax = self.env['account.tax'].search(
                        [('id', '=', single_line.tax_ids.id), ('company_id', '=', company.id)])
                    if line_tax:
                        tax = line_tax.xero_tax_type_id
                        if not tax:
                            self.env['account.tax'].get_xero_tax_ref(line_tax)
                            line_tax = self.env['account.tax'].search(
                                [('id', '=', single_line.tax_ids.id), ('company_id', '=', company.id)])
                            tax = line_tax.xero_tax_type_id

                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "CreditNoteNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_credit_note_export_line_dict(single_line)],
                            "Status": status
                        })
                else:
                    vals.update({
                        "Contact": {
                            "ContactID": cust_id
                        },
                        "Type": type,
                        "LineAmountTypes": tax_state,
                        "DueDate": str(self.invoice_date_due),
                        "Date": str(self.invoice_date),
                        "CreditNoteNumber": self.xero_invoice_number if (
                                self.xero_invoice_number and self.xero_invoice_id) else self.name,
                        "LineItems": [self.prepare_credit_note_export_line_dict(single_line)],
                        "Status": status
                    })
            else:
                if single_line.tax_ids:
                    line_tax = self.env['account.tax'].search(
                        [('id', '=', single_line.tax_ids.id), ('company_id', '=', company.id)])
                    if line_tax:
                        tax = line_tax.xero_tax_type_id
                        if not tax:
                            self.env['account.tax'].get_xero_tax_ref(line_tax)
                            line_tax = self.env['account.tax'].search(
                                [('id', '=', single_line.tax_ids.id), ('company_id', '=', company.id)])
                            tax = line_tax.xero_tax_type_id

                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "CreditNoteNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_credit_note_export_line_dict(single_line)],
                            "Status": status
                        })
                else:
                    vals.update({
                        "Contact": {
                            "ContactID": cust_id
                        },
                        "Type": type,
                        "DueDate": str(self.invoice_date_due),
                        "Date": str(self.invoice_date),
                        "CreditNoteNumber": self.xero_invoice_number if (
                                self.xero_invoice_number and self.xero_invoice_id) else self.name,
                        "LineItems": [self.prepare_credit_note_export_line_dict(single_line)],
                        "Status": status
                    })
        else:

            for line in self.invoice_line_ids.filtered(lambda x: not x.is_anglo_saxon_line and x.product_id):
                if ((
                        line.move_id.move_type == 'out_refund' and line.product_id and not company.export_invoice_without_product) or (
                        line.move_id.move_type == 'in_refund' and line.product_id and not company.export_bill_without_product)):
                    if line.product_id.xero_product_id:
                        _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
                    elif not line.product_id.xero_product_id:
                        self.env['product.product'].get_xero_product_ref(line.product_id)

                line_vals = self.prepare_credit_note_export_line_dict(line)
                lst_line.append(line_vals)
            vals.update({
                "Type": type,
                "LineAmountTypes": tax_state,
                "Contact": {"ContactID": cust_id},
                "DueDate": str(self.invoice_date_due),
                "Date": str(self.invoice_date),
                "CreditNoteNumber": self.xero_invoice_number if (
                        self.xero_invoice_number and self.xero_invoice_id) else self.name,
                "Status": status,
                "LineItems": lst_line,
            })

        if origin_credit_note:
            vals.update({'Reference': origin_credit_note})

        if self.currency_id:
            currency_code = self.currency_id.name
            vals.update({"CurrencyCode": currency_code})

        return vals

    @api.model
    def prepare_credit_note_export_line_dict(self, line):
        """This one used in the xero module for both bills and credit notes"""
        company = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id
        line_vals = {}
        account_code = None

        if self.partner_id:
            line_tax = self.env['account.tax'].search(
                [('id', '=', line.tax_ids[0].id), ('company_id', '=', company.id)])

            qty = abs(line.quantity)
            price = line.price_unit if line.quantity > 0 else 0 - line.price_unit

            if line.account_id:
                if line.account_id.xero_account_id:
                    account_code = line.account_id.code
                else:
                    self.env['account.account'].create_account_ref_in_xero(line.account_id)
                    if line.account_id.xero_account_id:
                        account_code = line.account_id.code

            if ((
                        line.move_id.move_type == 'in_invoice' or line.move_id.move_type == 'in_refund') and line.product_id and not company.export_bill_without_product) or (
                    line.move_id.move_type == 'out_refund' and line.product_id and not company.export_invoice_without_product):
                if line.tax_ids:
                    if line_tax:
                        tax = line_tax.xero_tax_type_id
                        if line_tax.price_include:
                            price = line.price_total / line.quantity if line.quantity else 1
                        else:
                            price = line.price_subtotal / line.quantity if line.quantity else 1
                        if line.quantity < 0:
                            price = 0 - abs(price)
                        if not tax:
                            self.env['account.tax'].get_xero_tax_ref(line_tax)
                            line_tax = self.env['account.tax'].search(
                                [('id', '=', line.tax_ids.id), ('company_id', '=', company.id)])
                            tax = line_tax.xero_tax_type_id

                        line_vals = {
                            'Description': line.name,
                            'UnitAmount': price,
                            'ItemCode': line.product_id.default_code,
                            'AccountCode': account_code,
                            'Quantity': qty,
                            'TaxType': tax
                        }
                else:
                    price = line.price_subtotal / line.quantity
                    if line.quantity < 0:
                        price = 0 - abs(price)
                    line_vals = {
                        'Description': line.name,
                        'UnitAmount': price,
                        'ItemCode': line.product_id.default_code,
                        'AccountCode': account_code,
                        'Quantity': qty,
                    }
            else:
                if line.tax_ids:
                    if line_tax:
                        tax = line_tax.xero_tax_type_id
                        if line_tax.price_include:
                            price = line.price_total / line.quantity if line.quantity else 1
                        else:
                            price = line.price_subtotal / line.quantity if line.quantity else 1
                        if line.quantity < 0:
                            price = 0 - abs(price)
                        if not tax:
                            self.env['account.tax'].get_xero_tax_ref(line_tax)
                            line_tax = self.env['account.tax'].search(
                                [('id', '=', line.tax_ids.id), ('company_id', '=', company.id)])
                            tax = line_tax.xero_tax_type_id

                        line_vals = {
                            'Description': line.name,
                            'UnitAmount': price,
                            'AccountCode': account_code,
                            'Quantity': qty,
                            'TaxType': tax
                        }
                else:
                    price = line.price_subtotal / line.quantity
                    if line.quantity < 0:
                        price = 0 - abs(price)
                    line_vals = {
                        'Description': line.name,
                        'UnitAmount': price,
                        'AccountCode': account_code,
                        'Quantity': qty,
                    }

        # Include analytic tags if any
        line_dict = self.xero_tracking_tag_insert(line=line, line_dict=line_vals)

        return line_dict

    @api.model
    def xero_tracking_tag_insert(self, line, line_dict):
        """Include analytic account as tracking categories for Xero."""
        if line.analytic_account_id and line.analytic_account_id.group_id:
            xero_tracking = self.env['account.analytic.account'].search([('name', '=', line.analytic_account_id.name)])
            tracking_ids = list(set([x.xero_tracking_opt_id for x in xero_tracking if x.group_id.xero_tracking_id]))
            if len(tracking_ids) > 1:
                raise UserError('Issue with analytic account Xero tracking - more than 1 tracking reference')
            elif not xero_tracking:
                raise UserError('No xero tracking reference found')
            if xero_tracking and tracking_ids:
                line_dict['Tracking'] = [{
                    'TrackingCategoryID': line.analytic_account_id.group_id.xero_tracking_id,
                    'TrackingOptionID': tracking_ids[0],
                    'Name': line.analytic_account_id.group_id.name,
                    'Option': line.analytic_account_id.name
                }]

        return line_dict

    def prepare_manual_journal_export_dict(self):

        vals = {}
        if self.state == 'posted':
            status = 'POSTED'

        narration = None
        if self.ref:
            narration = self.ref
        else:
            narration = self.name

        lineamounttype = 'NoTax'

        if self.date:
            date = str(self.date)

        #  Preparing Lines for export Journal
        journal_line_ids = []
        if self.line_ids:
            for line in self.line_ids:
                line_dict = {}

                if line.credit > 0:
                    line_amount = -float(line.credit)
                elif line.debit > 0:
                    line_amount = float(line.debit)

                if line.account_id:
                    if line.account_id.xero_account_id:
                        account_code = line.account_id.code
                    else:
                        self.env['account.account'].create_account_ref_in_xero(line.account_id)
                        if line.account_id.xero_account_id:
                            account_code = line.account_id.code

                line_dict.update({
                    "Description": line.name,
                    "LineAmount": line_amount,
                    "AccountCode": account_code,
                })

                Tracking_list = []
                Tracking_dict = {}

                if line.analytic_account_id:
                    line_dict = self.xero_tracking_tag_insert(line, line_dict)


                journal_line_ids.append(line_dict)

        vals.update({"JournalLines": journal_line_ids})
        vals.update({
            "Date": date,
            "Status": status,
            "Narration": narration,
            "LineAmountTypes": lineamounttype,
            "ShowOnCashBasisReports": "false"
        })

        # print('\n\n\n Prepeared Dictionary : ', vals, '\n\n\n\n')
        return vals

    @api.model
    def prepare_invoice_export_dict(self):
        company = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id
        if self.move_type == 'in_invoice':
            vals = self.prepare_vendorbill_export_dict()
            return vals
        else:

            if self.partner_id:
                cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)
            else:
                cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)

            vals = {}
            lst_line = []
            origin_reference = ''
            if self.move_type == 'in_invoice':
                type = 'ACCPAY'
            elif self.move_type == 'out_invoice':
                type = 'ACCREC'
            elif self.move_type == 'in_refund':
                type = 'ACCPAYCREDIT'
            elif self.move_type == 'out_refund':
                type = 'ACCRECCREDIT'

            # if self.origin:
            if self.invoice_origin:
                origin_reference = self.invoice_origin
                # vals.update({'Reference': self.origin})

            if self.tax_state:
                if self.tax_state == 'inclusive':
                    tax_state = 'Inclusive'
                elif self.tax_state == 'exclusive':
                    tax_state = 'Exclusive'
                elif self.tax_state == 'no_tax':
                    tax_state = 'NoTax'

            if self.state:
                if self.state == 'posted':
                    status = 'AUTHORISED'

                if company.invoice_status:
                    if company.invoice_status == 'draft':
                        status = 'DRAFT'
                    if company.invoice_status == 'authorised':
                        status = 'AUTHORISED'

            if len(self.invoice_line_ids) == 1:
                single_line = self.invoice_line_ids

                qty = single_line.quantity
                price = single_line.price_unit

                if single_line.discount:
                    discount = single_line.discount
                else:
                    discount = 0.0

                if single_line.account_id:
                    if single_line.account_id.xero_account_id:
                        account_code = single_line.account_id.code
                    else:
                        self.env['account.account'].create_account_ref_in_xero(single_line.account_id)
                        if single_line.account_id.xero_account_id:
                            account_code = single_line.account_id.code

                if single_line.product_id and not company.export_invoice_without_product:
                    if single_line.product_id.xero_product_id:
                        _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
                    elif not single_line.product_id.xero_product_id:
                        self.env['product.product'].get_xero_product_ref(single_line.product_id)

                    if single_line.tax_ids:
                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "Reference": origin_reference,
                            "InvoiceNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_invoice_export_line_dict(line=single_line)],
                            "Status": status
                        })


                    else:
                        vals.update({
                            # "Type": "ACCREC",
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "Reference": origin_reference,
                            "InvoiceNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_invoice_export_line_dict(line=single_line)],
                            "Status": status
                        })
                else:
                    if single_line.tax_ids:
                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "Reference": origin_reference,
                            "InvoiceNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_invoice_export_line_dict(line=single_line)],
                            "Status": status
                        })
                    else:
                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "Reference": origin_reference,
                            "InvoiceNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_invoice_export_line_dict(line=single_line)],
                            "Status": status
                        })
            else:

                for line in self.invoice_line_ids.filtered(lambda x: not x.is_anglo_saxon_line and x.product_id):

                    if line.product_id and not company.export_invoice_without_product:
                        if line.product_id.xero_product_id:
                            _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
                        elif not line.product_id.xero_product_id:
                            self.env['product.product'].get_xero_product_ref(line.product_id)

                    line_vals = self.prepare_invoice_export_line_dict(line)
                    lst_line.append(line_vals)
                vals.update({
                    "Type": type,
                    "LineAmountTypes": tax_state,
                    "Contact": {"ContactID": cust_id},
                    "DueDate": str(self.invoice_date_due),
                    "Date": str(self.invoice_date),
                    "Reference": origin_reference,
                    "InvoiceNumber": self.xero_invoice_number if (
                            self.xero_invoice_number and self.xero_invoice_id) else self.name,
                    "Status": status,
                    "LineItems": lst_line,
                })

            if self.currency_id:
                currency_code = self.currency_id.name
                vals.update({"CurrencyCode": currency_code})

            return vals

    @api.model
    def prepare_invoice_export_dict(self):
        company = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id
        if self.move_type == 'in_invoice':
            vals = self.prepare_vendorbill_export_dict()
            return vals
        else:

            if self.partner_id:
                cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)
            else:
                cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)

            vals = {}
            lst_line = []
            origin_reference = ''
            if self.move_type == 'in_invoice':
                type = 'ACCPAY'
            elif self.move_type == 'out_invoice':
                type = 'ACCREC'
            elif self.move_type == 'in_refund':
                type = 'ACCPAYCREDIT'
            elif self.move_type == 'out_refund':
                type = 'ACCRECCREDIT'

            # if self.origin:
            if self.invoice_origin:
                origin_reference = self.invoice_origin
                # vals.update({'Reference': self.origin})

            if self.tax_state:
                if self.tax_state == 'inclusive':
                    tax_state = 'Inclusive'
                elif self.tax_state == 'exclusive':
                    tax_state = 'Exclusive'
                elif self.tax_state == 'no_tax':
                    tax_state = 'NoTax'

            if self.state:
                if self.state == 'posted':
                    status = 'AUTHORISED'

                if company.invoice_status:
                    if company.invoice_status == 'draft':
                        status = 'DRAFT'
                    if company.invoice_status == 'authorised':
                        status = 'AUTHORISED'

            if len(self.invoice_line_ids) == 1:
                single_line = self.invoice_line_ids

                qty = single_line.quantity
                price = single_line.price_unit

                if single_line.discount:
                    discount = single_line.discount
                else:
                    discount = 0.0

                if single_line.account_id:
                    if single_line.account_id.xero_account_id:
                        account_code = single_line.account_id.code
                    else:
                        self.env['account.account'].create_account_ref_in_xero(single_line.account_id)
                        if single_line.account_id.xero_account_id:
                            account_code = single_line.account_id.code

                if single_line.product_id and not company.export_invoice_without_product:
                    if single_line.product_id.xero_product_id:
                        _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
                    elif not single_line.product_id.xero_product_id:
                        self.env['product.product'].get_xero_product_ref(single_line.product_id)

                    if single_line.tax_ids:
                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "Reference": origin_reference,
                            "InvoiceNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_invoice_export_line_dict(line=single_line)],
                            "Status": status
                        })


                    else:
                        vals.update({
                            # "Type": "ACCREC",
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "Reference": origin_reference,
                            "InvoiceNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_invoice_export_line_dict(line=single_line)],
                            "Status": status
                        })
                else:
                    if single_line.tax_ids:
                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "Reference": origin_reference,
                            "InvoiceNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_invoice_export_line_dict(line=single_line)],
                            "Status": status
                        })
                    else:
                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "Reference": origin_reference,
                            "InvoiceNumber": self.xero_invoice_number if (
                                    self.xero_invoice_number and self.xero_invoice_id) else self.name,
                            "LineItems": [self.prepare_invoice_export_line_dict(line=single_line)],
                            "Status": status
                        })
            else:

                for line in self.invoice_line_ids.filtered(lambda x: not x.is_anglo_saxon_line and x.product_id):

                    if line.product_id and not company.export_invoice_without_product:
                        if line.product_id.xero_product_id:
                            _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
                        elif not line.product_id.xero_product_id:
                            self.env['product.product'].get_xero_product_ref(line.product_id)

                    line_vals = self.prepare_invoice_export_line_dict(line)
                    lst_line.append(line_vals)
                vals.update({
                    "Type": type,
                    "LineAmountTypes": tax_state,
                    "Contact": {"ContactID": cust_id},
                    "DueDate": str(self.invoice_date_due),
                    "Date": str(self.invoice_date),
                    "Reference": origin_reference,
                    "InvoiceNumber": self.xero_invoice_number if (
                            self.xero_invoice_number and self.xero_invoice_id) else self.name,
                    "Status": status,
                    "LineItems": lst_line,
                })

            if self.currency_id:
                currency_code = self.currency_id.name
                vals.update({"CurrencyCode": currency_code})

            return vals

    @api.model
    def prepare_vendorbill_export_dict(self):
        company = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id

        if self.partner_id:
            cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)
        else:
            cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)

        vals = {}
        lst_line = []
        if self.move_type == 'in_invoice':
            type = 'ACCPAY'
        elif self.move_type == 'out_invoice':
            type = 'ACCREC'
        elif self.move_type == 'in_refund':
            type = 'ACCPAYCREDIT'
        elif self.move_type == 'out_refund':
            type = 'ACCRECCREDIT'

        # if self.origin:
        #     reference = self.origin
        # else:
        if (self.xero_invoice_number and self.xero_invoice_id):
            reference = self.xero_invoice_number
        else:
            reference = self.ref if self.ref else self.name

        # for some reason Xero is objecting the same ref even if different supplier
        set_unique_ref = self.ref
        counter = 1
        while set_unique_ref:
            same_ref = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('ref', '=', set_unique_ref)])
            if same_ref:
                set_unique_ref = set_unique_ref + ' ' + ' ' * counter
                counter += 1
            else:
                reference = set_unique_ref
                set_unique_ref = False

        if self.tax_state:
            if self.tax_state == 'inclusive':
                tax_state = 'Inclusive'
            elif self.tax_state == 'exclusive':
                tax_state = 'Exclusive'
            elif self.tax_state == 'no_tax':
                tax_state = 'NoTax'

        if self.state:
            if self.state == 'posted':
                status = 'AUTHORISED'

            if company.invoice_status:
                if company.invoice_status == 'draft':
                    status = 'DRAFT'
                if company.invoice_status == 'authorised':
                    status = 'AUTHORISED'

        if len(self.invoice_line_ids) == 1:
            single_line = self.invoice_line_ids

            qty = abs(single_line.quantity)
            price = single_line.price_unit if single_line.quantity > 0 else 0 - single_line.price_unit

            if single_line.account_id:
                if single_line.account_id.xero_account_id:
                    account_code = single_line.account_id.code
                else:
                    self.env['account.account'].create_account_ref_in_xero(single_line.account_id)
                    if single_line.account_id.xero_account_id:
                        account_code = single_line.account_id.code

            if single_line.product_id and not company.export_bill_without_product:
                if single_line.product_id.xero_product_id:
                    _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
                elif not single_line.product_id.xero_product_id:
                    self.env['product.product'].get_xero_product_ref(single_line.product_id)

                if single_line.tax_ids:
                    line_tax = self.env['account.tax'].search(
                        [('id', '=', single_line.tax_ids.id), ('company_id', '=', company.id)])
                    if line_tax:
                        tax = line_tax.xero_tax_type_id
                        if not tax:
                            self.env['account.tax'].get_xero_tax_ref(line_tax)
                            line_tax = self.env['account.tax'].search(
                                [('id', '=', single_line.tax_ids.id), ('company_id', '=', company.id)])
                            tax = line_tax.xero_tax_type_id

                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "InvoiceNumber": reference,
                            "LineItems": [self.prepare_credit_note_export_line_dict(single_line)],
                            "Status": status
                        })
                else:
                    vals.update({
                        "Contact": {
                            "ContactID": cust_id
                        },
                        "Type": type,
                        "LineAmountTypes": tax_state,
                        "DueDate": str(self.invoice_date_due),
                        "Date": str(self.invoice_date),
                        "InvoiceNumber": reference,
                        "LineItems": [self.prepare_credit_note_export_line_dict(single_line)],
                        "Status": status
                    })
            else:
                if single_line.tax_ids:
                    line_tax = self.env['account.tax'].search(
                        [('id', '=', single_line.tax_ids.id), ('company_id', '=', company.id)])
                    if line_tax:
                        tax = line_tax.xero_tax_type_id
                        if not tax:
                            self.env['account.tax'].get_xero_tax_ref(line_tax)
                            line_tax = self.env['account.tax'].search(
                                [('id', '=', single_line.tax_ids.id), ('company_id', '=', company.id)])
                            tax = line_tax.xero_tax_type_id

                        vals.update({
                            "Contact": {
                                "ContactID": cust_id
                            },
                            "Type": type,
                            "LineAmountTypes": tax_state,
                            "DueDate": str(self.invoice_date_due),
                            "Date": str(self.invoice_date),
                            "InvoiceNumber": reference,
                            "LineItems": [self.prepare_credit_note_export_line_dict(single_line)],
                            "Status": status
                        })
                else:
                    vals.update({
                        "Contact": {
                            "ContactID": cust_id
                        },
                        "Type": type,
                        "DueDate": str(self.invoice_date_due),
                        "Date": str(self.invoice_date),
                        "InvoiceNumber": reference,
                        "LineItems": [self.prepare_credit_note_export_line_dict(single_line)],
                        "Status": status
                    })
        else:

            for line in self.invoice_line_ids.filtered(lambda x: not x.is_anglo_saxon_line and x.product_id):
                if line.product_id and not company.export_bill_without_product:
                    if line.product_id.xero_product_id:
                        _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
                    elif not line.product_id.xero_product_id:
                        self.env['product.product'].get_xero_product_ref(line.product_id)

                line_vals = self.prepare_credit_note_export_line_dict(line)
                lst_line.append(line_vals)
            vals.update({
                "Type": type,
                "LineAmountTypes": tax_state,
                "Contact": {"ContactID": cust_id},
                "DueDate": str(self.invoice_date_due),
                "Date": str(self.invoice_date),
                "InvoiceNumber": reference,
                "Status": status,
                "LineItems": lst_line,
            })
        if self.currency_id:
            currency_code = self.currency_id.name
            vals.update({"CurrencyCode": currency_code})

        return vals

    @api.model
    def prepare_invoice_export_line_dict(self, line):

        company = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id
        line_vals = {}
        account_code = None
        if self.partner_id:

            qty = abs(line.quantity)
            price = line.price_unit if line.quantity > 0 else 0 - line.price_unit

            if line.discount:
                discount = line.discount
            else:
                discount = 0.0

            if line.account_id:
                if line.account_id.xero_account_id:
                    account_code = line.account_id.code
                else:
                    self.env['account.account'].create_account_ref_in_xero(line.account_id)
                    if line.account_id.xero_account_id:
                        account_code = line.account_id.code

            if line.product_id and not company.export_invoice_without_product:
                if line.tax_ids:
                    tax = line.tax_ids[0].xero_tax_type_id
                    if not tax:
                        return {'xero tax code not found'}

                    if line.tax_ids[0].price_include:
                        price = line.price_total / line.quantity if line.quantity else 1
                    else:
                        price = line.price_subtotal / line.quantity if line.quantity else 1

                    if line.quantity < 0:
                        price = 0 - abs(price)

                    line_vals = {
                        'Description': line.name,
                        'UnitAmount': price,
                        'ItemCode': line.product_id.default_code,
                        'AccountCode': account_code,
                        'Quantity': qty,
                        'DiscountRate': discount,
                        'TaxType': tax
                    }
                else:
                    if line.quantity < 0:
                        price = 0 - abs(price)
                    line_vals = {
                        'Description': line.name,
                        'UnitAmount': price,
                        'ItemCode': line.product_id.default_code,
                        'AccountCode': account_code,
                        'Quantity': qty,
                        'DiscountRate': discount,
                    }
            else:
                if line.tax_ids:
                    tax = line.tax_ids[0].xero_tax_type_id
                    if not tax:
                        return {'xero tax code not found'}

                    if line.tax_ids[0].price_include:
                        price = line.price_total / line.quantity if line.quantity else 1
                    else:
                        price = line.price_subtotal / line.quantity if line.quantity else 1

                if line.quantity < 0:
                    price = 0 - abs(price)
                    line_vals = {
                        'Description': line.name,
                        'UnitAmount': price,
                        'AccountCode': account_code,
                        'Quantity': qty,
                        'DiscountRate': discount,
                        'TaxType': tax
                    }
                else:
                    if line.quantity < 0:
                        price = 0 - abs(price)

                    line_vals = {
                        'Description': line.name,
                        'UnitAmount': price,
                        'AccountCode': account_code,
                        'DiscountRate': discount,
                        'Quantity': qty,
                    }
        return line_vals
