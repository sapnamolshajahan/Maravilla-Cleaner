from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Account(models.Model):
    _inherit = 'account.account'

    xero_account_id = fields.Char(string="Xero Account Id", copy=False)
    enable_payments_to_account = fields.Boolean(string="Enable Payments", default=False, copy=False)
    xero_account_type = fields.Many2one('xero.account.account', string="Xero Account Type")
    xero_description = fields.Text(string="Description")
    xero_tax_type_for_accounts = fields.Many2one('xero.tax.type', string="Tax Type")

    @api.model
    def prepare_account_export_dict(self):
        """Create Dictionary to export to XERO"""
        vals = {}
        if self.code:
            vals.update({'Code': self.code,'TaxType': 'NONE'})
        if self.name:
            vals.update({'Name': self.name})
        if self.enable_payments_to_account:
            vals.update({'EnablePaymentsToAccount': 'true'})
        else:
            vals.update({'EnablePaymentsToAccount': 'false'})
        if self.xero_description:
            vals.update({'Description': self.xero_description})
        if self.xero_tax_type_for_accounts:
            vals.update({'TaxType': self.xero_tax_type_for_accounts.xero_tax_type})
        if self.xero_account_type:
            account_type = {'Current Asset account': 'CURRENT',
                            'Current Liability account': 'CURRLIAB',
                            'Depreciation account': 'DEPRECIATN',
                            'Direct Costs account': 'DIRECTCOSTS',
                            'Equity account': 'EQUITY',
                            'Expense account': 'EXPENSE',
                            'Fixed Asset account': 'FIXED',
                            'Inventory Asset account': 'INVENTORY',
                            'Liability account': 'LIABILITY',
                            'Non-current Asset account': 'NONCURRENT',
                            'Other Income account': 'OTHERINCOME',
                            'Overhead account': 'OVERHEADS',
                            'Prepayment account': 'PREPAYMENT',
                            'Revenue account': 'REVENUE',
                            'Sale account': 'SALES',
                            'Non-current Liability account': 'TERMLIAB',
                            }

            type_name = self.env['xero.account.account'].search([('id', '=', self.xero_account_type.id)])
            if type_name.xero_account_type_name in account_type:
                vals.update({
                    'Type': account_type.get(type_name.xero_account_type_name)
                })
        return vals

    @api.model
    def create_account_in_xero(self):
        xero_config = self.env.company
        if self._context.get('active_ids'):
            account = self.browse(self._context.get('active_ids'))
        else:
            account = self

        for a in account:
            self.create_account_main(a, xero_config)

    @api.model
    def create_account_ref_in_xero(self, account_id):
        """export accounts to XERO"""
        xero_config = self.env.company
        if account_id:
            account = account_id
        else:
            account = self
        if not account.xero_account_type:
            raise ValidationError('Please Add Xero Account Type and Tax Type for Account No ' + account.code)
        if account:
            self.create_account_main(account, xero_config)

    @api.model
    def create_account_main(self, a, xero_config):
        token = xero_config.xero_oauth_token
        headers = self.env['xero.token'].get_head()
        if not token or not headers:
            raise UserError('Missing token or header for call to Xero')

        if not a.xero_account_id:
            vals = a.prepare_account_export_dict()
            parsed_dict = json.dumps(vals)
            protected_url = 'https://api.xero.com/api.xro/2.0/Accounts'
            data = requests.request('PUT', url=protected_url, data=parsed_dict, headers=headers)
            if data.status_code == 200:
                self.env['xero.error.log'].success_log(record=a, name='Account Export')
                response_data = json.loads(data.text)
                if response_data.get('Accounts'):
                    if response_data.get('Accounts')[0].get('AccountID'):
                        a.update({'xero_account_id': response_data.get('Accounts')[0].get('AccountID')})
                        self._cr.commit()
                        _logger.info(_(" (CREATE) - Exported successfully to XERO"))
            elif data.status_code == 400:
                self.env['xero.error.log'].error_log(record=a, name='Account Export', error=data.text)
                self._cr.commit()
            elif data.status_code == 401:
                raise ValidationError(
                    "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")

        elif a.xero_account_id:
            vals = a.prepare_account_export_dict()
            parsed_dict = json.dumps(vals)
            protected_url = 'https://api.xero.com/api.xro/2.0/Accounts/' + a.xero_account_id
            data = requests.request('POST', url=protected_url, headers=headers, data=parsed_dict)
            if data.status_code == 200:
                self.env['xero.error.log'].success_log(record=a, name='Account Export')
            elif data.status_code == 401:
                raise ValidationError(
                    "Time Out..!!\nPlease Check Your Connection or error in application or refresh token.")
            else:
                self.env['xero.error.log'].error_log(record=a, name='Account Export', error=data.text)
                self._cr.commit()


class XeroAccountType(models.Model):
    _name = 'xero.account.account'
    _description = 'xero account account'
    _rec_name = 'xero_account_type_name'

    xero_account_type_name = fields.Char(string='Account Type', readonly=True, copy=False)


class XeroAccountTaxType(models.Model):
    _name = 'xero.tax.type'
    _description = 'xero tax type'
    _rec_name = 'xero_tax_type'

    xero_tax_type = fields.Char(string='Account Tax Type', readonly=True, copy=False)


class AnalyticAccountInherit(models.Model):
    _inherit = 'account.analytic.account'

    xero_tracking_opt_id = fields.Char(string="Xero Tracking Id", copy=False)
    is_active = fields.Boolean(string="Active", default=True)

    def create_analytic_account_in_xero(self, account_id=None):
        if account_id is None:
            if self._context.get('active_ids'):
                account = self.browse(self._context.get('active_ids'))
            else:
                account = self
        else:
            account = self.env['account.analytic.account'].browse(account_id)

        # TODO need to think about what replaces category in Odoo
        # for t in account:
        #     vals = {}
        #     if t.is_active:
        #         status = "ACTIVE"
        #     else:
        #         status = "ARCHIVED"
        #
        #     if not t.xero_tracking_opt_id:
        #         if t.group_id:
        #             groupTrackingId = None
        #             obj = self.env['account.analytic.group'].search([('id', '=', t.group_id.id)])
        #             if not obj.xero_tracking_id:
        #                 groupTrackingId = obj.create_analytic_account_group_in_xero(t.group_id)
        #
        #             if not groupTrackingId:
        #                 groupTrackingId = obj.xero_tracking_id
        #
        #             vals.update({'Name': t.name, 'Status': status})
        #             parsed_dict = json.dumps(vals)
        #
        #             url = 'https://api.xero.com/api.xro/2.0/TrackingCategories/{}/Options'.format(groupTrackingId)
        #             data = obj.put_data(url, parsed_dict)
        #
        #             if data.status_code == 200:
        #                 parsed_data = json.loads(data.text)
        #                 if parsed_data:
        #                     if parsed_data.get('Options'):
        #                         t.xero_tracking_opt_id = parsed_data.get(
        #                             'Options')[0].get('TrackingOptionID')
        #                         self._cr.commit()
        #                         _logger.info(_("(CREATE) Exported successfully to XERO"))
        #
        #             elif data.status_code == 401:
        #                 raise ValidationError('Please Refresh Token First...')
        #         else:
        #             raise ValidationError(_('Please Assign group for %s' % t.name))
        #     else:
        #         if t.group_id:
        #             obj = self.env['account.analytic.group'].search([('id', '=', t.group_id.id)])
        #             vals.update({'Name': t.name, 'Status': status})
        #             parsed_dict = json.dumps(vals)
        #             url = 'https://api.xero.com/api.xro/2.0/TrackingCategories/{}/Options/{}'.format(
        #                 obj.xero_tracking_id, t.xero_tracking_opt_id)
        #             data = obj.put_data(url, parsed_dict, post=1)
        #
        #             if data.status_code == 200:
        #                 _logger.info(_('{} Analytic Account Updated Successfully '.format(t.name)))
        #             elif data.status_code == 400:
        #                 parsed_error = json.loads(data.text)
        #                 if parsed_error.get('ErrorNumber') == 10:
        #                     Error = parsed_error.get('Elements')
        #                     msg = Error[0].get('ValidationErrors')
        #                     msg = msg[0].get('Message')
        #
        #                     _logger.info(_("\n\n\n Error \n %s\n\n" % msg))
        #                     raise ValidationError(_('%s' % msg))

