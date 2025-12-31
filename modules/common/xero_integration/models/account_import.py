import json
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

ACCOUNT_TYPE_XERO = {'CURRENT': 'Current Asset account',
                     'CURRLIAB': 'Current Liability account',
                     'DEPRECIATN': 'Depreciation account',
                     'DIRECTCOSTS': 'Direct Costs account',
                     'EQUITY': 'Equity account',
                     'EXPENSE': 'Expense account',
                     'FIXED': 'Fixed Asset account',
                     'INVENTORY': 'Inventory Asset account',
                     'LIABILITY': 'Liability account',
                     'NONCURRENT': 'Non-current Asset account',
                     'OTHERINCOME': 'Other Income account',
                     'OVERHEADS': 'Overhead account',
                     'PREPAYMENT': 'Prepayment account',
                     'REVENUE': 'Revenue account',
                     'SALES': 'Sale account',
                     'TERMLIAB': 'Non-current Liability account',
                     }

ACCOUNT_TYPE_ODOO = {'CURRENT': 'asset_current',
                     'CURRLIAB': 'liability_current',
                     'DEPRECIATION': 'depreciation',
                     'DIRECTCOSTS': 'expense_direct_cost',
                     'EQUITY': 'equity',
                     'EXPENSE': 'expense',
                     'FIXED': 'asset_fixed',
                     'INVENTORY': 'asset_current',
                     'LIABILITY': 'liability_current',
                     'NONCURRENT': 'asset_fixed',
                     'OTHERINCOME': 'income_other',
                     'OVERHEADS': 'expense',
                     'PREPAYMENT': 'asset_prepayments',
                     'REVENUE': 'income',
                     'SALES': 'income',
                     'TERMLIAB': 'liability_non_current',
                     }


class ResCompany(models.Model):
    _inherit = "res.company"

    def import_accounts(self):
        url = 'https://api.xero.com/api.xro/2.0/Accounts'
        if not self:
            self = self.env.company
        data = self.get_data(url)
        if data:
            _logger.info("DATA RECEIVED FROM API IS {} ".format(data.text))
            self.create_account_in_odoo(data)
            self._cr.commit()

        elif data.status_code == 401:
            raise ValidationError('Time Out..!!\n Please check your connection or error in application.')

    @api.model
    def create_account_in_odoo(self, data):
        """Data fetched from xero is available in XML form this function converts the data from xml to dict and makes it readable"""
        if data:
            recs = []

        parsed_dict = json.loads(data.text)

        if parsed_dict.get('Accounts'):
            record = parsed_dict.get('Accounts')
            if isinstance(record, (dict,)):
                self.create_imported_accounts(record)
            else:
                for acc in parsed_dict.get('Accounts'):
                    self.create_imported_accounts(acc)
        else:
            raise ValidationError('There is no any account present in XERO.')

    @api.model
    def create_imported_accounts(self, acc):
        """Get the data and create a dictionary for account creation"""

        account_acc = self.env['account.account'].search(
            ['|', ('xero_account_id', '=', acc.get('AccountID')), ('code', '=', acc.get('Code'))])
        account_account = self.env['account.account'].search(
            [('id', 'in', account_acc.ids), ('company_ids', 'in', self.env.company.id)])

        dict_e = {}
        if acc.get('Code'):
            dict_e['code'] = acc.get('Code')
        if acc.get('Name'):
            dict_e['name'] = acc.get('Name')

        if acc.get('TaxType'):
            tax_type = self.env['xero.tax.type'].search([('xero_tax_type', '=', acc.get('TaxType'))])
            if tax_type:
                dict_e['xero_tax_type_for_accounts'] = tax_type.id
            else:
                self.env['xero.tax.type'].create({'xero_tax_type': acc.get('TaxType')})
                tax_type = self.env['xero.tax.type'].search([('xero_tax_type', '=', acc.get('TaxType'))])
                if tax_type:
                    dict_e['xero_tax_type_for_accounts'] = tax_type.id

        if acc.get('EnablePaymentsToAccount'):
            dict_e['enable_payments_to_account'] = True
        if acc.get('AccountID'):
            dict_e['xero_account_id'] = acc.get('AccountID')
        if acc.get('Description'):
            dict_e['xero_description'] = acc.get('Description')
        if acc.get('Type'):

            if acc.get('Type') in ACCOUNT_TYPE_ODOO:
                dict_e['account_type'] = ACCOUNT_TYPE_ODOO[acc.get('Type')]
            else:
                raise UserError('Account Type not found in Odoo')

            if acc.get('Type') in ACCOUNT_TYPE_XERO:
                acc_type_xero = self.env['xero.account.account']
                user_type_xero = acc_type_xero.search(
                    [('xero_account_type_name', '=', ACCOUNT_TYPE_XERO.get(acc.get('Type')))])
                dict_e['xero_account_type'] = user_type_xero.id

        if not account_account:

            '''If Account is not present we create it'''
            if 'code' in dict_e and dict_e.get('code'):
                account = account_account.create(dict_e)
                if not account:
                    _logger.info(_("Account Not Created..!!"))
                    raise ValidationError(
                        'Account could not be updated \n Please check Account ' + dict_e['code'] + ' in Xero.')
            else:
                _logger.error("code key is not there in data dict for create, skipping the record.")
        elif 'code' in dict_e and dict_e.get('code'):
            if 'user_type_id' in dict_e:
                del dict_e['user_type_id']
            if 'name' in dict_e:
                del dict_e['name']
            account_account.write(dict_e)
        else:
            _logger.error("code key is not there in data dict for update, skipping the record.")
