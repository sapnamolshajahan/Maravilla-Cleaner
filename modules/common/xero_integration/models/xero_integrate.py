from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class XeroImportType(models.Model):
    _name = 'xero.import.type'
    _description = 'Xero Import Types'

    name = fields.Char(string='Description')
    date_from_visible = fields.Boolean(string='Date From Visible')
    function_name = fields.Char(string='Function Name')


class XeroImport(models.TransientModel):
    _name = 'xero.import'
    _description = 'Xero Import Data Wizard'

    xero_import_type = fields.Many2one('xero.import.type', string='Import Type', required=True)
    date_from_visible = fields.Boolean(string='Date From Visible', related='xero_import_type.date_from_visible')
    date_from = fields.Date(string='Date From')

    def run_import(self):
        try:
            run_method = getattr(self.env['res.company'], self.xero_import_type.function_name)
            if self.date_from:
                run_method(date_from=self.date_from)
            else:
                run_method()
        except Exception as e:
            raise UserError('An error occurred in the called function {e}'.format(e=e))

        return {"type": "ir.actions.act_window_close"}


class XeroAuthenticate(models.TransientModel):
    _name = 'xero.authenticate'
    _description = 'Xero Authentication Wizard'

    name = fields.Char(string='Name')

    def run_authenticate(self):
        company = self.env.company
        if not company.xero_client_id:
            raise ValidationError("Please Enter Client ID")
        if not company.xero_client_secret:
            raise ValidationError("Please Enter Client Secret")

        requests_url = 'https://login.xero.com/identity/connect/authorize?' + 'response_type=code&' + 'client_id=' + \
                       company.xero_client_id + '&redirect_uri=' + company.xero_redirect_url + \
                       '&scope= openid profile email accounting.transactions accounting.settings accounting.settings.read accounting.contacts payroll.employees  offline_access'

        return {
            "type": "ir.actions.act_url",
            "url": requests_url,
            "target": "new"
        }


class XeroRefreshToken(models.TransientModel):
    _name = 'xero.refresh.token'
    _description = 'Xero Refresh Token Wizard'

    name = fields.Char(string='Name')

    def run_token_refresh(self):
        self.env['xero.token'].refresh_token()
        return {"type": "ir.actions.act_window_close"}



