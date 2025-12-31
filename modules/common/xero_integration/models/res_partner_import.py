
import json
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def create_contact(self, parent_id, con_id, new_dict):
        firstname = ''
        lastname = ''
        contact_name = ''
        temp_dict = {}

        if isinstance(new_dict, list):
            for val in new_dict:
                if val.get('FirstName'):
                    firstname = val.get('FirstName')
                else:
                    firstname = ''
                if val.get('LastName'):
                    lastname = val.get('LastName')
                else:
                    lastname = ''
                temp_dict.update({'name': firstname + ' ' + lastname})
                if val.get('EmailAddress', False):
                    temp_dict.update({'email': val.get('EmailAddress')})
                if isinstance(parent_id, int):
                    temp_dict.update({'parent_id': parent_id})
                else:
                    temp_dict.update({'parent_id': parent_id[0].id})
                temp_dict.update({'type': 'contact'})
                temp_dict.update({'xero_cust_id': con_id})

                if 'message_follower_ids' in temp_dict:
                    del temp_dict['message_follower_ids']

                if val.get('FirstName') or val.get('LastName'):
                    if val.get('EmailAddress') not in self.skip_emails:
                        con_search = self.env['res.partner'].search(
                            [('parent_id', '=', parent_id), ('type', '=', 'contact'),
                             ('email', '=', val.get('EmailAddress')), ('company_id', '=', self.id)], limit=1)
                        if not con_search:
                            self.env['res.partner'].create(temp_dict)
                            self._cr.commit()
                        else:
                            con_search.write(temp_dict)

    def import_customers(self):
        for i in range(10000):
            res = self.customer_main_function(i + 1)
            _logger.info("RESPONSE : %s", res)

            if not res:
                break
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
    def customer_main_function(self, page_no):
        _logger.info("CUSTOMER PAGE NO : %s", page_no)

        url = 'https://api.xero.com/api.xro/2.0/Contacts?page=' + str(page_no)
        res = self.create_customers(url, page_no)
        if res:
            return True
        else:
            return False

    @api.model
    def fetch_the_required_customer(self, customer_id):
        url = 'https://api.xero.com/api.xro/2.0/Contacts/' + str(customer_id)
        page_no = 0
        self.create_customers(url, page_no)

    @api.model
    def create_customers(self, url, page_no):
        if not self.skip_emails:
            self.skip_emails = ''

        data = self.get_data(url)
        if data:
            parsed_dict = json.loads(data.text)

            if parsed_dict.get('Contacts', False):
                record = parsed_dict.get('Contacts')
                if isinstance(record, (dict,)):
                    self.create_imported_customers(record)
                else:
                    for item in parsed_dict.get('Contacts'):
                        self.create_imported_customers(item)
                return True
            else:
                if page_no == 1:
                    raise ValidationError('There is no contact present in XERO.')
                else:
                    return False
        elif data.status_code == 401:
            raise ValidationError(
                'Time Out..!!\n Please check your connection or error in application or refresh token.')

    def calc_payment_terms(self, payment_type, day):
        if payment_type == 'DAYSAFTERBILLDATE':
            option = 'day_after_invoice_date'
            term_name = str(day) + ' day(s) after the bill date'

        if payment_type == 'DAYSAFTERBILLMONTH':
            option = 'after_invoice_month'
            term_name = str(day) + ' day(s) after the end of the bill month'

        if payment_type == 'OFCURRENTMONTH':
            option = 'day_current_month'
            term_name = str(day) + ' of the current month'

        if payment_type == 'OFFOLLOWINGMONTH':
            option = 'day_following_month'
            term_name = str(day) + ' of the following month'

        payment_terms = self.env['account.payment.term'].search([('name', '=', term_name)])
        if not payment_terms:
            term_dict = {'name': term_name, 'line_ids': [(0, 0, {'value': 'balance',
                                                                 'days': day,
                                                                 'option': option})]}

            payment_terms = self.env['account.payment.term'].create(term_dict)

        return payment_terms

    def calc_address(self, address, item):
        street1 = ''
        street2 = ''
        country = ''
        state = ''

        if address.get('AddressLine1'):
            street1 = address.get('AddressLine1')
        if address.get('AddressLine2'):
            street2 = address.get('AddressLine2')
        if address.get('AddressLine3'):
            street2 = street2 + '\n' + address.get('AddressLine3')
        if address.get('AddressLine4'):
            street2 = street2 + '\n' + address.get('AddressLine4')

        if address.get('Country'):
            if len(address.get('Country')) == 2:
                country = self.env['res.country'].search([('code', '=ilike', address.get('Country'))], limit=1)
            else:
                country = self.env['res.country'].search([('name', 'ilike', address.get('Country'))], limit=1)

            if not country:
                raise UserError('Country Not Found : ' + address.get('Country') + '\nContact Name : ' + item.get('Name'))

        if address.get('Region'):
            state = self.env['res.country.state'].search([('name', '=ilike', address.get('Region'))])
            if not state:
                if country:
                    state = self.env['res.country.state'].search(
                        [('code', '=', address.get('Region')), ('country_id', '=', country.id)])
                    if not state:
                        raise UserError('State Not Found : ' + address.get('Region') + '\nContact Name : ' + item.get('Name'))

        return street1, street2, country, state

    @api.model
    def create_imported_customers(self, item):
        if item.get('AccountNumber'):

            customer = self.env['res.partner'].search(
                ['|', ('xero_cust_id', '=', item.get('ContactID')),
                 ('ref', '=', item.get('AccountNumber'))])
            customer_exists = self.env['res.partner'].search([('id', 'in', customer.ids), ('company_id', '=', self.env.company.id)])
        else:

            customer_exists = self.env['res.partner'].search(
                [('company_id', '=', self.env.company.id), ('xero_cust_id', '=', item.get('ContactID')), ])

        dict_customer = {}

        _logger.info("Xero Customer Name : %s", item.get('Name'))
        _logger.info("Xero Customer ContactID : %s", item.get('ContactID'))

        if not item.get('IsSupplier', None) and not (item.get('IsCustomer', None)):
            dict_customer.update({'company_type': 'person'})
            dict_customer.update({'is_company': True})

        if item.get('EmailAddress', False):
            if item.get('EmailAddress'):
                dict_customer.update({'email': item.get('EmailAddress')})
            else:
                dict_customer.update({'email': ''})
        if item.get('AccountNumber', False):
            dict_customer.update({'ref': item.get('AccountNumber')})
        if item.get('PaymentTerms'):
            if item.get('PaymentTerms').get('Bills'):
                payment_type = item.get('PaymentTerms').get('Bills').get('Type')
                day = item.get('PaymentTerms').get('Bills').get('Day')

                payment_terms = self.calc_payment_terms(payment_type, day)
                if payment_terms:
                    dict_customer['property_supplier_payment_term_id'] = payment_terms.id

            if item.get('PaymentTerms').get('Sales'):
                receipt_type = item.get('PaymentTerms').get('Sales').get('Type')
                day = item.get('PaymentTerms').get('Sales').get('Day')
                customer_payment_terms = self.calc_payment_terms(receipt_type, day)
                if customer_payment_terms:
                    dict_customer['property_payment_term_id'] = customer_payment_terms.id

        if item.get('Name'):
            dict_customer.update({'name': item.get('Name')})
            dict_customer.update({'xero_cust_id': item.get('ContactID')})

        if item.get('Addresses'):
            for address in item.get('Addresses'):
                if address.get('AddressType', False) and address.get('AddressType') == 'POBOX':
                    street1, street2, country, state = self.calc_address(address, item)
                    dict_customer.update({
                        'street': street1,
                        'street2': street2,
                        'city': address.get('City'),
                        'zip': address.get('PostalCode'),
                        'country_id': country.id if country else False,
                        'state_id': state.id if state else False,
                    })

        if item.get('Phones', False):
            for phones in item.get('Phones'):
                if phones.get('PhoneType', False):
                    if phones.get('PhoneType') == 'DEFAULT' and phones.get('PhoneNumber',
                                                                           False):
                        phone_str = phones.get('PhoneNumber')
                        dict_customer.update({'phone': phone_str})
                    if phones.get('PhoneType') == 'MOBILE' and phones.get('PhoneNumber',
                                                                          False):
                        phone_str = phones.get('PhoneNumber')
                        dict_customer.update({'mobile': phone_str})
        dict_customer.update({'company_id': int(self.env.company.id)})

        if not customer_exists:
            create_cust = self.env['res.partner'].create(dict_customer)
        else:
            customer_exists[0].write(dict_customer)

        if item.get('ContactPersons'):
            new_dict = item.get('ContactPersons')
            if not customer_exists:
                self.create_contact(create_cust.id, item.get('ContactID'), new_dict)
            else:
                self.create_contact(customer_exists[0].id, item.get('ContactID'), new_dict)

    def import_contact_groups(self):
        url = 'https://api.xero.com/api.xro/2.0/ContactGroups'
        data = self.get_data(url)
        if data:
            parsed_dict = json.loads(data.text)

            if parsed_dict.get('ContactGroups'):
                record = parsed_dict.get('ContactGroups')
                if isinstance(record, (dict,)):
                    self.create_imported_contact_groups(record)
                else:
                    for grp in parsed_dict.get('ContactGroups'):
                        self.create_imported_contact_groups(grp)
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
                raise ValidationError('There is no any contact group present in XERO.')

        elif data.status_code == 401:
            raise ValidationError('Time Out..!!\n Please check your connection or error in application.')

    @api.model
    def create_imported_contact_groups(self, grp):
        group = self.env['res.partner.category'].search(
            [('xero_contact_group_id', '=', grp.get('ContactGroupID'))])

        dict_g = {}
        if grp.get('ContactGroupID'):
            dict_g['xero_contact_group_id'] = grp.get('ContactGroupID')

        if grp.get('Name'):
            dict_g['name'] = grp.get('Name')

        if not group:
            grp_create = group.create(dict_g)
            if grp_create:
                _logger.info(_("Group Created Sucessfully..!!"))
            else:
                _logger.info(_("Group Not Created..!!"))
                raise ValidationError('Error occurred could not create group.')
        else:
            grp_write = group.write(dict_g)
            if grp_write:
                _logger.info(_("Group Updated Sucessfully..!!"))
            else:
                _logger.info(_("Group Not Updated..!!"))
                raise ValidationError('Error occurred could not update group.')

