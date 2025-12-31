import json
import logging

import requests

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    xero_product_id = fields.Char('Xero ItemID', copy=False)

    def remove_html_tags(self, description):
        """Remove html tags from a string"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', description)

    @api.model
    def get_xero_product_ref(self, product):
        if product.xero_product_id:
            return product.xero_product_id
        else:
            self.create_single_product_in_xero(product)
            if product.xero_product_id:
                return product.xero_product_id

    def purchase_dict_non_tracked(self, price, code):
        purchase_dict = {
            "UnitPrice": price,
            "AccountCode": code,
        }
        return purchase_dict

    def purchase_dict_tracked(self, price, code):
        purchase_dict = {
            "UnitPrice": price,
            "COGSAccountCode": code,
        }
        return purchase_dict

    @api.model
    def prepare_product_export_dict(self):
        vals = {}

        xero_config = self.env.company

        if self.description_sale:
            description = self.remove_html_tags(self.description_sale)
        else:
            description = 'NA'

        if self.type == 'consu':
            qty = self.qty_available
        else:
            qty = 0

        if self.description_purchase:
            description_p = self.remove_html_tags(self.description_purchase)
        else:
            description_p = 'NA'

        if self.standard_price:
            standard_price = self.standard_price
        else:
            standard_price = 0

        if self.list_price:
            list_price = self.list_price
        else:
            list_price = 0

        expense_account = self.property_account_expense_id or self.categ_id.property_account_expense_categ_id

        if not expense_account.xero_account_id:
            self.env['account.account'].create_account_ref_in_xero(expense_account)

        if self.type == 'consu' and not xero_config.non_tracked_item:
            purchase_dict = self.purchase_dict_tracked(standard_price, expense_account.code)
        else:
            purchase_dict = self.purchase_dict_non_tracked(standard_price, expense_account.code)

        income_account = self.property_account_income_id or self.categ_id.property_account_income_categ_id
        if not income_account.xero_account_id:
            self.env['account.account'].create_account_ref_in_xero(income_account)

        sales_dict = {
            "UnitPrice": list_price,
            "AccountCode": self.property_account_income_id.code,
        }

        if self.default_code:
            vals.update({
                "Code": self.default_code,
                "Name": self.name[:50],
                "Description": description,
                "PurchaseDescription": description_p,
                "PurchaseDetails": {
                    "UnitPrice": standard_price},
                "SalesDetails": {
                    "UnitPrice": list_price}
            })
        else:
            raise ValidationError('Please enter Internal Reference for ' + self.name)

        if self.name:
            vals.update({
                "Code": self.default_code,
                "Name": self.name[:50],
                "Description": description,
                "PurchaseDescription": description_p,
                "PurchaseDetails": purchase_dict,
                "SalesDetails": sales_dict,
            })

            if self.type == 'consu':
                if not xero_config.non_tracked_item:
                    vals.update({
                        'InventoryAssetAccountCode': self.categ_id.xero_inventory_account.code,
                        'IsTrackedAsInventory': True,
                    })

        return vals

    @api.model
    def create_product_in_xero(self):
        xero_config = self.env.company
        if self._context.get('active_ids'):
            product = self.browse(self._context.get('active_ids'))
        else:
            product = self

        for p in product:
            self.create_main_product_in_xero(p, xero_config)
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
    def create_single_product_in_xero(self, product):
        xero_config = self.env['res.users'].search([('id', '=', self._uid)], limit=1).company_id
        self.create_main_product_in_xero(product, xero_config)

    @api.model
    def create_main_product_in_xero(self, p, xero_config):
        vals = p.prepare_product_export_dict()
        parsed_dict = json.dumps(vals)
        if xero_config.xero_oauth_token:
            token = xero_config.xero_oauth_token
        headers = self.env['xero.token'].get_head()

        if token:
            protected_url = 'https://api.xero.com/api.xro/2.0/Items'

            data = requests.request('POST', url=protected_url, headers=headers, data=parsed_dict)
            _logger.info("\n\nPRODUCT DATA : %s %s % s", p, data, data.text)

            if data.status_code == 200:
                self.env['xero.error.log'].success_log(record=p, name='Product Export')

                response_data = json.loads(data.text)
                if response_data.get('Items'):
                    if response_data.get('Items')[0].get('ItemID'):
                        p.xero_product_id = response_data.get('Items')[0].get('ItemID')
                        self._cr.commit()
                        _logger.info("Exported Product successfully to XERO : %s ", p)

            elif data.status_code == 400:
                self.env['xero.error.log'].error_log(record=p, name='Product Export', error=data.text)
                self._cr.commit()

                response_data = json.loads(data.text)
                if response_data:
                    if response_data.get('Elements'):
                        for element in response_data.get('Elements'):
                            if element.get('ValidationErrors'):
                                for err in element.get('ValidationErrors'):
                                    raise ValidationError('(Products) Xero Exception : ' + err.get('Message'))
                    elif response_data.get('Message'):
                        raise ValidationError(
                            '(Products) Xero Exception : ' + response_data.get('Message'))
                    else:
                        raise ValidationError(
                            '(Products) Xero Exception : please check xero logs in odoo for more details')
            elif data.status_code == 401:
                raise ValidationError(
                    "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
        else:
            raise ValidationError("Please Check Your Connection or error in application or refresh token..!!")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    xero_product_id = fields.Char('Xero ItemID', related='product_variant_ids.xero_product_id', copy=False)


class ProductCategory(models.Model):
    _inherit = "product.category"

    xero_inventory_account = fields.Many2one('account.account', string="XERO Inventory Account", copy=False)
