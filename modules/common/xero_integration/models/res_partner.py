import json
import logging

import requests

from odoo import models, fields, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Customer(models.Model):
    _inherit = 'res.partner'

    xero_cust_id = fields.Char('Xero Customer Id', copy=False)

    def get_xero_partner_ref(self, partner):
        xero_config = self.env.company

        if partner:
            if partner.xero_cust_id or (partner.parent_id and partner.parent_id.xero_cust_id):
                return partner.xero_cust_id or partner.parent_id.xero_cust_id
            else:
                self.create_main_customer_in_xero(partner, xero_config)
                if partner.xero_cust_id or (partner.parent_id and partner.parent_id.xero_cust_id):
                    return partner.xero_cust_id or partner.parent_id.xero_cust_id

    def prepare_address(self, addresstype, addr):
        add_dict = {'AddressType': addresstype}
        if addr.street:
            add_dict.update({'AddressLine1': addr.street})
        if addr.street2:
            add_dict.update({'AddressLine2': addr.street2})
        if addr.city:
            add_dict.update({'City': addr.city})
        if addr.zip:
            add_dict.update({'PostalCode': addr.zip})
        if addr.state_id:
            add_dict.update({'Region': addr.state_id.name})
        else:
            add_dict.update({'Region': ''})
        if addr.country_id:
            country_id = self.env['res.country'].search([('id', '=', addr.country_id.id)])
            if country_id:
                add_dict.update({'Country': country_id.name})
        return add_dict

    def prepare_from_partner(self, addresstype, street1, street2, city, state, postcode, country):
        add_dict = {'AddressType': addresstype}
        add_dict.update({'AddressLine1': street1})
        add_dict.update({'AddressLine2': street2})
        add_dict.update({'City': city})
        add_dict.update({'PostalCode': postcode})
        add_dict.update({'Region': state})
        add_dict.update({'Country': country})
        return add_dict

    def split_name(self, contact_name):
        x = contact_name.split()
        if len(x) == 2:
            fname = x[0]
            lname = x[1]
        elif len(x) == 1:
            fname = x[0]
            lname = ''
        elif len(x) > 2:
            fname = contact_name
            lname = ''
        return fname, lname

    def prepare_customer_export_dict(self):

        if not self:
            return

        con_list = []
        dict1 = {}
        phone_dict = {}
        final_dict = {}
        final_list = []
        mobile_dict = {}

        if self.name:
            dict1['Name'] = self.name
        if self.email:
            dict1['EmailAddress'] = self.email
            _logger.info("\nEmail Address : %s", self.email)

        if self.id:
            dict1['ContactNumber'] = self.id
            billing_addr = self.child_ids.filtered(lambda a: a.type == 'invoice')

            if billing_addr:
                bill_add_dict = self.prepare_address('POBOX', billing_addr[0])
            else:
                bill_add_dict = self.prepare_from_partner('POBOX', self.street, self.street2, self.city,
                                                          self.state_id.name,
                                                          self.zip, self.country_id.name)

            delivery_addr = self.child_ids.filtered(lambda a: a.type == 'delivery')
            if delivery_addr:
                del_add_dict = self.prepare_address('STREET', delivery_addr[0])
            else:
                del_add_dict = self.prepare_from_partner('POBOX', self.street, self.street2, self.city,
                                                         self.state_id.name,
                                                         self.zip, self.country_id.name)

            if not bill_add_dict['AddressLine1']:
                if self.street:
                    bill_add_dict.update({'AddressLine1': self.street})

            list_address = [del_add_dict, bill_add_dict]
            dict1.update({"Addresses": list_address})

            if self.phone:
                phone_dict.update({'PhoneType': "DEFAULT"})
                phone_dict.update({'PhoneNumber': self.phone})
            if self.mobile:
                mobile_dict.update({'PhoneType': "MOBILE"})
                mobile_dict.update({'PhoneNumber': self.mobile})
            list_phone = [phone_dict, mobile_dict]
            dict1.update({'Phones': list_phone})

            contacts = self.child_ids.filtered(lambda a: a.type == 'contact')
            counter = 1
            for con in contacts:
                if counter > 5:
                    break
                counter += 1
                fname, lname = self.split_name(con.name)
                if con.email:
                    email = con.email
                else:
                    email = ''

                con_dict = {
                    'FirstName': fname,
                    'LastName': lname,
                    'EmailAddress': email
                }

                con_list.append(con_dict)
            if con_list:
                dict1.update({'ContactPersons': con_list})

            bills = {}
            if self.property_supplier_payment_term_id and self.property_supplier_payment_term_id.line_ids:
                line_ids = self.property_supplier_payment_term_id.line_ids[0]
                if line_ids.delay_type == 'days_after':
                    terms_type = 'DAYSAFTERBILLDATE'
                if line_ids.delay_type == 'days_after_end_of_month':
                    terms_type = 'DAYSAFTERBILLMONTH'
                if line_ids.delay_type == 'days_end_of_month_on_the':
                    terms_type = 'OFCURRENTMONTH'
                if line_ids.delay_type == 'days_after_end_of_next_month':
                    terms_type = 'OFFOLLOWINGMONTH'
                bills = {
                    "Day": line_ids.days_next_month,
                    "Type": terms_type
                }
            sales = {}
            if self.property_payment_term_id:
                line_ids = self.property_payment_term_id.line_ids[0]
                if line_ids.delay_type == 'days_after':
                    sale_terms_type = 'DAYSAFTERBILLDATE'
                if line_ids.delay_type == 'days_after_end_of_month':
                    sale_terms_type = 'DAYSAFTERBILLMONTH'
                if line_ids.delay_type == 'days_end_of_month_on_the':
                    sale_terms_type = 'OFCURRENTMONTH'
                if line_ids.delay_type == 'days_after_end_of_next_month':
                    sale_terms_type = 'OFFOLLOWINGMONTH'
                sales = {
                    "Day": line_ids.days_next_month,
                    "Type": sale_terms_type
                }

            if self.property_supplier_payment_term_id or self.property_payment_term_id:
                dict1.update({
                    "PaymentTerms": {
                        "Bills": bills,
                        "Sales": sales
                    }
                })

            final_list.append(dict1)
            final_dict.update({'Contacts': final_list})
        return final_dict

    def create_customer_in_xero(self):
        xero_config = self.env.company
        if self._context.get('active_ids'):
            partner = self.browse(self._context.get('active_ids'))
        else:
            partner = self

        for con in partner:
            self.create_main_customer_in_xero(con, xero_config)
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

    def create_main_customer_in_xero(self, con, xero_config):
        if con:
            vals = con.prepare_customer_export_dict()
            parsed_dict = json.dumps(vals)
            token = ''

            if xero_config.xero_oauth_token:
                token = xero_config.xero_oauth_token

            if not token:
                raise ValidationError('Token not found,Authentication Unsuccessful Please check your connection!!')

            headers = self.env['xero.token'].get_head()

            protected_url = 'https://api.xero.com/api.xro/2.0/Contacts'
            data = requests.request('POST', url=protected_url, data=parsed_dict, headers=headers)
            if data.status_code == 200:
                self.env['xero.error.log'].success_log(record=con, name='Contact Export')

                response_data = json.loads(data.text)
                if response_data.get('Contacts'):
                    con.xero_cust_id = response_data.get('Contacts')[0].get('ContactID')
                    _logger.info("\nExported Contact : %s %s", con, con.name)
                    child_ids_all = self.search(
                        [('parent_id', '=', con.id), ('company_id', '=', xero_config.id)])
                    if child_ids_all:
                        for child in child_ids_all:
                            child.xero_cust_id = ''

                    child_ids = self.search([('parent_id', '=', con.id), ('company_id', '=', xero_config.id)], limit=5)
                    if child_ids:
                        for child in child_ids:
                            child.xero_cust_id = response_data.get('Contacts')[0].get('ContactID')
                            _logger.info("\nExported Sub-Contact : %s %s", child, child.name)

            elif data.status_code == 400:
                self.env['xero.error.log'].error_log(record=con, name='Contact Export', error=data.text)
                self._cr.commit()

                response_data = json.loads(data.text)
                if response_data:
                    if response_data.get('Elements'):
                        for element in response_data.get('Elements'):
                            if element.get('ValidationErrors'):
                                for err in element.get('ValidationErrors'):
                                    raise ValidationError('(Contacts) Xero Exception : ' + err.get('Message'))
                    elif response_data.get('Message'):
                        raise ValidationError(
                            '(Contacts) Xero Exception : ' + response_data.get('Message'))
                    else:
                        raise ValidationError(
                            '(Contacts) Xero Exception : please check xero logs in odoo for more details')

            elif data.status_code == 401:
                raise ValidationError(
                    "Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
