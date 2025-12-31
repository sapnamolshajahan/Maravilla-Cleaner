# -*- coding: utf-8 -*-
import binascii
import logging
import tempfile
import xlrd

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('ref', 'move_type', 'partner_id', 'journal_id', 'invoice_date', 'state')
    def _check_duplicate_supplier_reference(self):
        return


class XeroImport(models.TransientModel):
    _name = "xero.import"
    _description = 'Xero Import AR or AP'

    import_file = fields.Binary("Import File", required=True)
    move_type = fields.Selection(string='Move Type',
                                 selection=[('receivable', 'Receivable'), ('payable', 'Payable')],
                                 required=True)
    debit_account = fields.Many2one('account.account', string='Debit Account', required=True)
    credit_account = fields.Many2one('account.account', string='Credit Account', required=True)
    default_text = fields.Char(string='Default text', default='Migrated record')
    create_partner = fields.Boolean(string='Create Partner',
                                    help='If set, any non-matching records will have a partner created')

    def build_line(self, line, partner_id, account, debit, credit, invoice_date, actual_due_date,
                   payment_term=False, display_invoice_line=False):
        dict = {
            'product_id': False,
            'quantity': 1,
            'name': self.default_text,
            'partner_id': partner_id.id,
            'debit': debit,
            'credit': credit,
            'account_id': account.id,
            'display_type': payment_term if payment_term else 'product',
            'date':invoice_date,
            'date_maturity': actual_due_date,
            'tax_ids': False,
        }
        if display_invoice_line:
            dict['quantity'] = 1
            dict['price_unit'] = debit if debit else credit
            dict['price_subtotal'] = debit if debit else credit
        invoice_line_dict = dict
        return invoice_line_dict

    def build_move(self, line, move_type, debit_line, credit_line, partner_id, invoice_date, actual_due_date,
                   invoice_number):

        debit_amount = debit_line['debit']
        move_dict = {
            'move_type': move_type,
            'partner_id': partner_id.id,
            'payment_reference': 'Migrated invoice',
            'invoice_date': invoice_date,
            'invoice_date_due': actual_due_date,
            'amount_total': debit_amount,
            'amount_total_signed': 0 - debit_amount if move_type in ('in_invoice', 'out_refund') else debit_amount,
            'ref': line[2],
            'name': invoice_number if invoice_number else False,
            'invoice_partner_display_name': partner_id.name,
            'invoice_payment_term_id': partner_id.property_payment_term_id.id,
            'state': 'draft'

        }
        account_move = self.env['account.move'].with_context(check_move_validity=False,skip_invoice_sync=True).create(move_dict)
        debit_line['move_id'] = account_move.id
        debit_aml = self.env['account.move.line'].with_context(check_move_validity=False,skip_invoice_sync=True).create(debit_line)
        credit_line['move_id'] = account_move.id
        credit_aml = self.env['account.move.line'].with_context(check_move_validity=False,skip_invoice_sync=True).create(credit_line)
        debit_aml.write({'debit': debit_line['debit']})
        credit_aml.write({'credit': credit_line['credit']})
        account_move._post()

        return

    def process_line(self, line, partner, invoice_date, amount, invoice_number):
        partner_id = self.env['res.partner'].search([('name', '=', partner)], limit=1)
        if not partner_id:
            if not self.create_partner:
                raise UserError('Partner {partner} not found'.format(partner=partner))
            else:
                partner_id = self.env['res.partner'].sudo().create({
                    'name': partner,
                    'is_company': True
                })
        actual_due_date = invoice_date
        due_date = line[1]
        try:
            actual_due_date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() +
                                                   int(float(due_date)) - 2)
        except:
            pass

        if self.move_type == 'receivable':
            if amount < 0.0:
                move_type = 'out_refund'
                debit_line = self.build_line(line, partner_id, self.credit_account, abs(amount), 0.0,
                                             invoice_date, actual_due_date, False, True)
                credit_line = self.build_line(line, partner_id, self.debit_account, 0.0, abs(amount),
                                              invoice_date, actual_due_date, 'payment_term', False)
                self.build_move(line, move_type, debit_line, credit_line, partner_id, invoice_date,
                                       actual_due_date, invoice_number)
            else:
                move_type = 'out_invoice'
                credit_line = self.build_line(line, partner_id, self.credit_account,  0.0, abs(amount),
                                              invoice_date, actual_due_date, False, True)
                debit_line = self.build_line(line, partner_id, self.debit_account, abs(amount), 0.0,
                                             invoice_date, actual_due_date, 'payment_term', False)
                self.build_move(line, move_type, debit_line, credit_line, partner_id, invoice_date,
                                       actual_due_date, invoice_number)

        else:
            if amount < 0.0:
                move_type = 'in_refund'
                debit_line = self.build_line(line, partner_id, self.credit_account, abs(amount), 0.0,
                                             invoice_date, actual_due_date, 'payment_term', False)
                credit_line = self.build_line(line, partner_id, self.debit_account, 0.0, abs(amount),
                                              invoice_date, actual_due_date, False, True)
                self.build_move(line, move_type, debit_line, credit_line, partner_id, invoice_date,
                                       actual_due_date, invoice_number)
            else:
                move_type = 'in_invoice'
                credit_line = self.build_line(line, partner_id, self.credit_account, 0.0, abs(amount),
                                              invoice_date, actual_due_date, 'payment_term', False)
                debit_line = self.build_line(line, partner_id, self.debit_account, abs(amount), 0.0,
                                             invoice_date, actual_due_date, False, True)
                self.build_move(line, move_type, debit_line, credit_line, partner_id, invoice_date,
                                       actual_due_date, invoice_number)

    def button_import_file(self):
        try:
            import_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            import_file.write(binascii.a2b_base64(self.import_file))
            import_file.seek(0)
            wb = xlrd.open_workbook(import_file.name)
            sheet = wb.sheet_by_index(0)

        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Please check the file is correct, it cannot be processed!"))

        partner = False
        for row_no, row in enumerate(sheet.get_rows()):
            if row_no <= 0:
                continue
            else:
                line = tuple(map(lambda r: isinstance(r.value, bytes) and r.value.encode('utf-8') or str(r.value), row))
                invoice_date = line[0]
                row_date = False
                try:
                    row_date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() +
                                                    int(float(invoice_date)) - 2)
                except:
                    pass
                if self.move_type == 'payable':
                    invoice_amount = line[9]
                    invoice_number = False
                else:
                    invoice_amount = line[10]
                    invoice_number = line[2]

                if row_date and isinstance(row_date, date) and invoice_amount:
                    if not partner:
                        raise UserError('Transaction line but no partner - see {date} for {invoice_amount}'.
                                        format(date=date, invoice_amount=invoice_amount))
                    amount = float(invoice_amount)
                    self.process_line(line, partner, row_date, amount, invoice_number)
                    self.env.cr.commit()
                    self.env.invalidate_all()
                elif len(line[0]):
                    partner = line[0]

        return {'type': 'ir.actions.act_window_close'}
