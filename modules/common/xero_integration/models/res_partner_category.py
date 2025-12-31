import json
import logging

import requests

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ContactGroup(models.Model):
    _inherit = 'res.partner.category'

    xero_contact_group_id = fields.Char(string="Xero Contact Group Id", copy=False)

    @api.model
    def prepare_contact_group_export_dict(self):
        vals = {}
        if self.active:
            vals.update({
                'Status': 'ACTIVE',
            })
        if self.name:
            vals.update({
                'Name': self.name,
            })
        return vals

    @api.model
    def create_contact_group_in_xero(self):
        xero_config = self.env.company
        if xero_config.xero_oauth_token:
            token = xero_config.xero_oauth_token
            if not token:
                raise ValidationError("Please Check Your Connection or error in application or refresh token..!!")

        headers = self.env['xero.token'].get_head()

        if self._context.get('active_ids'):
            group = self.browse(self._context.get('active_ids'))
        else:
            group = self

        for a in group:
            if not a.xero_contact_group_id:
                vals = a.prepare_contact_group_export_dict()
                parsed_dict = json.dumps(vals)
                protected_url = 'https://api.xero.com/api.xro/2.0/ContactGroups'
                data = requests.request('POST', url=protected_url, data=parsed_dict, headers=headers)
                if data.status_code == 200:
                    self.env['xero.error.log'].success_log(record=a, name='ContactGroup Export')
                    response_data = json.loads(data.text)

                    if response_data.get('ContactGroups')[0].get('ContactGroupID'):
                        a.xero_contact_group_id = response_data.get('ContactGroups')[0].get('ContactGroupID')
                        _logger.info(_("(CREATE) - Exported successfully to XERO"))
                elif data.status_code == 401:
                    raise ValidationError(
                        "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
                else:
                    self.env['xero.error.log'].error_log(record=a, name='ContactGroup Export', error=data.text)
                    self._cr.commit()
            else:
                vals = a.prepare_contact_group_export_dict()
                parsed_dict = json.dumps(vals)
                protected_url_2 = 'https://api.xero.com/api.xro/2.0/ContactGroups/' + a.xero_contact_group_id
                data = requests.request('POST', url=protected_url_2, data=parsed_dict, headers=headers)
                if data.status_code == 200:
                    self.env['xero.error.log'].success_log(record=a, name='ContactGroup Export')
                    _logger.info(_("(UPDATE) - Exported successfully to XERO"))

                elif data.status_code == 401:
                    raise ValidationError(
                        "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
                else:
                    self.env['xero.error.log'].error_log(record=a, name='ContactGroup Export', error=data.text)
                    self._cr.commit()

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
