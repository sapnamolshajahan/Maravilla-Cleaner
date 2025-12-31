import json
import logging

from odoo import api, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def import_tax(self):
        url = 'https://api.xero.com/api.xro/2.0/TaxRates'
        data = self.get_data(url)
        if data:
            parsed_dict = json.loads(data.text)

            if parsed_dict.get('TaxRates'):

                xero_id = self.env.company

                record = parsed_dict.get('TaxRates')
                if isinstance(record, (dict,)):
                    if xero_id.xero_country_name == 'United States':
                        if record.get('TaxType') != 'AVALARA':
                            self.create_imported_tax(record)
                    else:
                        self.create_imported_tax(record)
                else:
                    for acc in parsed_dict.get('TaxRates'):
                        if xero_id.xero_country_name == 'United States':
                            if acc.get('TaxType') != 'AVALARA':
                                self.create_imported_tax(acc)
                        else:
                            self.create_imported_tax(acc)

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
            else:
                raise ValidationError('There is no any tax present in XERO.')

        elif data.status_code == 401:
            raise ValidationError('Time Out..!!\n Please check your connection or error in application.')

    @api.model
    def create_imported_tax(self, acc):
        _logger.info("Process Tax Rate : %s ", acc.get('Name'))
        account_tax = self.env['account.tax'].search(
            [('xero_tax_type_id', '=', acc.get('TaxType')), ('price_include', '=', False),
             ('type_tax_use', '=', 'sale'), ('company_id', '=', self.env.company.id)]) or self.env['account.tax'].search(
            [('xero_tax_type_id', '=', acc.get('TaxType')), ('price_include', '=', False),
             ('type_tax_use', '=', 'purchase'), ('company_id', '=', self.env.company.id)]) or self.env['account.tax'].search(
            [('xero_tax_type_id', '=', acc.get('TaxType')), ('price_include', '=', True),
             ('type_tax_use', '=', 'sale'), ('company_id', '=', self.env.company.id)]) or self.env['account.tax'].search(
            [('xero_tax_type_id', '=', acc.get('TaxType')), ('price_include', '=', True),
             ('type_tax_use', '=', 'purchase'), ('company_id', '=', self.env.company.id)])

        dict_t = {}
        if acc.get('TaxType'):
            dict_t['xero_tax_type_id'] = acc.get('TaxType')
        if acc.get('ReportTaxType'):
            dict_t['xero_record_taxtype'] = acc.get('ReportTaxType')
        # if acc.get('Status'):
        #     dict_t['xero_tax_status'] = acc.get('Status')
        if acc.get('Name'):
            dict_t['name'] = acc.get('Name')
        if acc.get('EffectiveRate') or acc.get('DisplayTaxRate'):
            dict_t['amount'] = acc.get('EffectiveRate') or acc.get('DisplayTaxRate')
        else:
            dict_t['amount'] = 0.0

        if acc.get('Status') == 'ACTIVE':
            if not account_tax:
                '''If tax is not present we create it'''
                dict_t['amount_type'] = 'percent'
                list_tax = []

                account_tax_name = self.env['account.tax'].search(
                    [('name', '=', acc.get('Name')), ('company_id', '=', self.env.company.id)])
                if not account_tax_name:
                    dict_t.update({'name': acc.get('Name')})
                    dict_t.update({'type_tax_use': 'sale'})
                    _logger.info(_(' Creating Sale Tax : {}'.format(dict_t)))
                    account_tax_create_s = self.env['account.tax'].create(dict_t)

                    if account_tax_create_s:
                        dict_t['name'] = acc.get('Name') + '(Inc)'
                        dict_t.update({'price_include': True})
                        _logger.info(_(' Creating Inc Sale Tax : {}'.format(dict_t)))
                        self.env['account.tax'].create(dict_t)

                    dict_t.update({'name': acc.get('Name')})
                    dict_t.update({'type_tax_use': 'purchase'})
                    dict_t.update({'price_include': False})
                    _logger.info(_(' Creating Purchase Tax : {}'.format(dict_t)))
                    account_tax_create = self.env['account.tax'].create(dict_t)
                    if account_tax_create:
                        dict_t.update({'price_include': True})
                        dict_t['name'] = acc.get('Name') + '(Inc)'
                        _logger.info(_(' Creating Inc Purchase Tax : {}'.format(dict_t)))
                        self.env['account.tax'].create(dict_t)

                else:
                    account_tax_name.write(dict_t)

            else:
                _logger.info(_("\n\nUpdating tax {} ".format(acc.get('Name'))))
                dict_t['amount_type'] = 'percent'

                _logger.info(_('\nFinal Tax Update Dict : {}'.format(dict_t)))
                account_tax_create = account_tax.write(dict_t)

                if account_tax_create:
                    _logger.info(_("Tax Updated"))
