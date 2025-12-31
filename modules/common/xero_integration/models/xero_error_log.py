import json

from odoo import fields, models, _

class XeroErrorLog(models.Model):
    _name = 'xero.error.log'
    _description = 'Xero Error Log'
    _rec_name = 'transaction'
    _order = 'id desc'

    transaction = fields.Char('Transaction')
    record_id = fields.Char('Record ID')
    record_name = fields.Char('Record Name')
    xero_error_response = fields.Char('Error Response')
    xero_error_msg = fields.Char('Error Message')
    date = fields.Datetime('Date', default=lambda self: fields.Datetime.now())
    active = fields.Boolean('Active', default=True)
    state = fields.Selection(string='Status', selection=[('success', 'Success'), ('error', 'Error')], default='error')

    def success_log(self, record, name):
        self.create({
            'transaction': name,
            'record_id': record,
            'record_name': record.name,
            'state': 'success'
        })

    def error_log(self, record, name, error):
        if record:
            record_id = record.id
            record_name = record.name
        else:
            record_id = False
            record_name = name
        log = self.create({
            'transaction': name,
            'record_id': record_id,
            'record_name': record_name,
            'state': 'error',
            'xero_error_response': error
        })

        log_dict = json.loads(error)

        if log_dict.get('Elements'):
            errors = []

            for element in log_dict['Elements']:
                for err in element.get('ValidationErrors', []):
                    errors.append(err.get('Message', ''))

            log.xero_error_msg = '\n'.join(errors)
