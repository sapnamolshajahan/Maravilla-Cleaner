import json
import logging

import requests

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Tax(models.Model):
    _inherit = 'account.tax'

    CanApplyToEquity = fields.Boolean(string="Can Apply To Equity", default=False)
    CanApplyToLiabilities = fields.Boolean(string="Can Apply To Liabilities", default=False)
    CanApplyToRevenue = fields.Boolean(string="Can Apply To Revenue ", default=False)
    CanApplyToExpenses = fields.Boolean(string="Can Apply To Expenses", default=False)
    CanApplyToAssets = fields.Boolean(string="Can Apply To Assets", default=False)

    xero_tax_type_id = fields.Char(string="Xero TaxType", copy=False)
    xero_record_taxtype = fields.Char(string="Xero RecordTaxType", copy=False)

    @api.model
    def get_xero_tax_ref(self, tax):
        xero_config = self.env.company

        if tax.xero_tax_type_id:
            return tax
        else:
            self.create_main_tax_in_xero(tax, xero_config)
            if tax.xero_tax_type_id:
                return tax

    @api.model
    def prepare_tax_export_dict(self):
        vals = {}
        ApplyToEquity = ApplyToLiabilities = ApplyToExpenses = ApplyToRevenue = ApplyToAssets = 'false'
        company = self.env.company
        if self.name:
            if self.CanApplyToEquity:
                ApplyToEquity = 'true'

            if self.CanApplyToLiabilities:
                ApplyToLiabilities = 'true'

            if self.CanApplyToRevenue:
                ApplyToRevenue = 'true'

            if self.CanApplyToExpenses:
                ApplyToExpenses = 'true'

            if self.CanApplyToAssets:
                ApplyToAssets = 'true'

            component_list = []
            for i in self.children_tax_ids:
                tax = self.env['account.tax'].search([('id', '=', i.id), ('company_id', '=', company.id)])
                if tax:
                    tax_name = tax.name
                    tax_amount = tax.amount

                    component_dict = {
                        "Name": tax_name,
                        "Rate": tax_amount,
                        "IsCompound": "false",
                        "IsNonRecoverable": "false"
                    }
                    component_list.append(component_dict)

            if self.amount_type:
                if self.amount_type == 'percent':
                    vals.update({
                        "Name": self.name,
                        "TaxComponents": [
                            {
                                "Name": self.name,
                                "Rate": self.amount,
                                "IsCompound": "false",
                                "IsNonRecoverable": "false"
                            }
                        ],
                        "CanApplyToEquity": ApplyToEquity,
                        "CanApplyToLiabilities": ApplyToLiabilities,
                        "CanApplyToRevenue": ApplyToRevenue,
                        "CanApplyToExpenses": ApplyToExpenses,
                        "CanApplyToAssets": ApplyToAssets,
                    })
                elif self.amount_type == 'group':
                    vals.update({
                        "Name": self.name,
                        "TaxComponents": component_list,
                        "CanApplyToEquity": ApplyToEquity,
                        "CanApplyToLiabilities": ApplyToLiabilities,
                        "CanApplyToRevenue": ApplyToRevenue,
                        "CanApplyToExpenses": ApplyToExpenses,
                        "CanApplyToAssets": ApplyToAssets,
                    })
        return vals

    @api.model
    def create_tax_in_xero(self):
        xero_config = self.env.company
        if self._context.get('active_ids'):
            tax = self.browse(self._context.get('active_ids'))
        else:
            tax = self

        for t in tax:
            self.create_main_tax_in_xero(t, xero_config)
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
    def create_main_tax_in_xero(self, t, xero_config):
        vals = t.prepare_tax_export_dict()
        if (xero_config.xero_country_name == 'United Kingdom') or \
                (xero_config.xero_country_name == 'New Zealand') or \
                (xero_config.xero_country_name == 'Australia'):
            if t.xero_record_taxtype:
                if t.xero_record_taxtype == 'REVERSECHARGES':
                    raise ValidationError(
                        'The Tax with this ReportTaxType is not yet available for create and update via the API. '
                        'They are returned on GET requests only')
                if t.xero_record_taxtype == 'NONE':
                    raise ValidationError(
                        ' The Tax with this ReportTaxType is used for system tax rates and only returned on GET requests')
                if t.xero_record_taxtype == 'GSTONIMPORTS':
                    raise ValidationError(
                        ' The Tax with this ReportTaxType is used for system tax rates and only returned on GET requests')

                vals.update({
                    "ReportTaxType": t.xero_record_taxtype
                })
            else:
                if t.type_tax_use:
                    if t.type_tax_use == 'sale':
                        vals.update({
                            "ReportTaxType": 'OUTPUT'
                        })
                    elif t.type_tax_use == 'purchase':
                        vals.update({
                            "ReportTaxType": 'INPUT'
                        })

        parsed_dict = json.dumps(vals)

        if xero_config.xero_oauth_token:
            token = xero_config.xero_oauth_token
            if not token:
                raise ValidationError(
                    "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")

        headers = self.env['xero.token'].get_head()

        protected_url = 'https://api.xero.com/api.xro/2.0/TaxRates'

        data = requests.request('POST', url=protected_url, data=parsed_dict, headers=headers)

        if data.status_code == 200:
            self.env['xero.error.log'].success_log(record=t, name='Tax Export')
            response_data = json.loads(data.text)
            if response_data.get('TaxRates'):
                t.xero_record_taxtype = response_data.get('TaxRates')[0].get('ReportTaxType')
                t.xero_tax_type_id = response_data.get('TaxRates')[0].get('TaxType')
                self._cr.commit()
            _logger.info(_("Exported successfully to XERO"))
        elif data.status_code == 400:
            self.env['xero.error.log'].error_log(record=t, name='Tax Export', error=data.text)
            self._cr.commit()

            response_data = json.loads(data.text)
            if response_data:
                if response_data.get('Elements'):
                    for element in response_data.get('Elements'):
                        if element.get('ValidationErrors'):
                            for err in element.get('ValidationErrors'):
                                raise ValidationError('(Tax) Xero Exception : ' + err.get('Message'))
                elif response_data.get('Message'):
                    raise ValidationError(
                        '(Tax) Xero Exception : ' + response_data.get('Message'))
                else:
                    raise ValidationError(
                        '(Tax) Xero Exception : please check xero logs in odoo for more details')

        elif data.status_code == 401:
            raise ValidationError(
                "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
