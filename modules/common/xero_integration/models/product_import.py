
import json
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def import_products(self):
        url = 'https://api.xero.com/api.xro/2.0/items'
        data = self.get_data(url)
        res = self.create_products(data)
        if res:
            success_form = self.env.ref('xero_integration.connection_successfull_view', False)
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
    def fetch_the_required_product(self, prod_internal_code):
        _logger.info("FETCHING THE REQUIRED PRODUCT")

        url = 'https://api.xero.com/api.xro/2.0/items/' + str(prod_internal_code)
        data = self.get_data(url)
        self.create_products(data)

    @api.model
    def create_products(self, data):
        if data:
            parsed_dict = json.loads(data.text)
            if parsed_dict.get('Items'):
                record = parsed_dict.get('Items')
                if isinstance(record, (dict,)):
                    self.create_imported_products(record)
                else:
                    for item in parsed_dict.get('Items'):
                        self.create_imported_products(item)
                return True
            else:
                raise ValidationError('There is no any product present in XERO.')
        elif data.status_code == 401:
            raise ValidationError('Time Out..!!\n Please check your connection or error in application.')

    @api.model
    def create_imported_products(self, item):

        product_exists = self.env['product.product'].search(
            ['|', ('xero_product_id', '=', item.get('ItemID')), ('default_code', '=', item.get('Code'))])

        dict_create = {'xero_product_id': item.get('ItemID')}
        if item.get('Name'):
            dict_create.update({'name': item.get('Name')})
        else:
            _logger.info("Product Name is not defined : PRODUCT CODE = %s ", item.get('Code'))

        dict_create.update({'default_code': item.get('Code')})

        if item.get('SalesDetails', False):
            if item.get('SalesDetails').get('UnitPrice', False):
                dict_create.update(
                    {'list_price': float(item.get('SalesDetails').get('UnitPrice'))})
            if item.get('SalesDetails').get('TaxType', False):
                product_tax_s = self.env['account.tax'].search(
                    [('xero_tax_type_id', '=', item.get('SalesDetails').get('TaxType')), ('type_tax_use', '=', 'sale'),
                     ('price_include', '=', False), ('company_id', '=', self.id)])
                if product_tax_s:
                    dict_create.update(
                        {'taxes_id': [(6, 0, [product_tax_s.id])]})
                else:
                    self.import_tax()
                    product_tax_s1 = self.env['account.tax'].search(
                        [('xero_tax_type_id', '=', item.get('SalesDetails').get('TaxType')),
                         ('type_tax_use', '=', 'sale'), ('price_include', '=', False), ('company_id', '=', self.id)])
                    if product_tax_s1:
                        dict_create.update(
                            {'taxes_id': [(6, 0, [product_tax_s1.id])]})

            if item.get('SalesDetails').get('AccountCode', False):
                acc_id_s = self.env['account.account'].search(
                    [('code', '=', item.get('SalesDetails').get('AccountCode')), ('company_ids', 'in', self.id)])
                if acc_id_s:
                    dict_create.update({'property_account_income_id': acc_id_s.id})
                else:
                    self.import_accounts()
                    acc_id_s1 = self.env['account.account'].search(
                        [('code', '=', item.get('SalesDetails').get('AccountCode')), ('company_ids', 'in', self.id)])
                    if acc_id_s1:
                        dict_create.update({'property_account_income_id': acc_id_s1.id})

        if item.get('PurchaseDetails', False):
            if item.get('PurchaseDetails').get('UnitPrice', False):
                dict_create.update(
                    {'standard_price': float(item.get('PurchaseDetails').get('UnitPrice'))})
            if item.get('PurchaseDetails').get('TaxType', False):
                product_tax_p = self.env['account.tax'].search(
                    [('xero_tax_type_id', '=', item.get('PurchaseDetails').get('TaxType')),
                     ('type_tax_use', '=', 'purchase'), ('price_include', '=', False), ('company_ids', 'in', self.id)])

                if product_tax_p:
                    dict_create.update(
                        {'supplier_taxes_id': [(6, 0, [product_tax_p.id])]})
                else:
                    self.import_tax()
                    product_tax = self.env['account.tax'].search(
                        [('xero_tax_type_id', '=', item.get('PurchaseDetails').get('TaxType')),
                         ('type_tax_use', '=', 'purchase'), ('price_include', '=', False),
                         ('company_id', '=', self.id)])
                    if product_tax:
                        dict_create.update(
                            {'supplier_taxes_id': [(6, 0, [product_tax.id])]})

            if item.get('IsTrackedAsInventory'):
                if item.get('PurchaseDetails').get('COGSAccountCode', False):
                    acc_id_p = self.env['account.account'].search(
                        [('code', '=', item.get('PurchaseDetails').get('COGSAccountCode')),
                         ('company_ids', 'in', self.id)])
                    if acc_id_p:
                        dict_create.update({'property_account_expense_id': acc_id_p.id})
                    else:
                        self.import_accounts()
                        acc_id_p1 = self.env['account.account'].search(
                            [('code', '=', item.get('PurchaseDetails').get('COGSAccountCode')),
                             ('company_ids', 'in', self.id)])
                        if acc_id_p1:
                            dict_create.update({'property_account_expense_id': acc_id_p1.id})
            else:
                if item.get('PurchaseDetails').get('AccountCode', False):
                    acc_id_p = self.env['account.account'].search(
                        [('code', '=', item.get('PurchaseDetails').get('AccountCode')), ('company_ids', 'in', self.id)])
                    if acc_id_p:
                        dict_create.update({'property_account_expense_id': acc_id_p.id})
                    else:
                        self.import_accounts()
                        acc_id_p1 = self.env['account.account'].search(
                            [('code', '=', item.get('PurchaseDetails').get('AccountCode')),
                             ('company_ids', 'in', self.id)])
                        if acc_id_p1:
                            dict_create.update({'property_account_expense_id': acc_id_p1.id})

        if item.get(item.get('IsPurchased')):
            dict_create.update({'sale_ok': True})
        if item.get(item.get('IsSold')):
            dict_create.update({'purchase_ok': True})

        if item.get('Description'):
            dict_create.update({'description_sale': item.get('Description')})
        if item.get('PurchaseDescription'):
            dict_create.update({'description_purchase': item.get('PurchaseDescription')})

        if item.get('IsTrackedAsInventory'):
            if item.get('IsTrackedAsInventory'):
                dict_create.update({'type': 'product'})

        if dict_create and not product_exists:
            dict_create.update({'company_id': self.id})
            self.env['product.product'].create(dict_create)
            _logger.info("Product Created Sucessfully..!! PRODUCT CODE = %s ", item.get('Code'))

        else:
            product_exists.write(dict_create)
            _logger.info("\nProduct Updated Sucessfully..!! PRODUCT CODE = %s ", item.get('Code'))