# -*- coding: utf-8 -*-

import datetime
import logging
from odoo import fields, models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AuditLogging(models.Model):
    _name = "audit.logging"
    _order = 'id desc'

    # The audit values are a denormalised scraping of the information at the
    # time of update. It's a bad idea to use related items as the data they point
    # to may have been updated from when they were first created.

    ###########################################################################
    # Fields
    ###########################################################################
    create_date = fields.Datetime(string="When", required=True, readonly=True)
    login = fields.Char(string="Who", required=True, readonly=True)
    record_id = fields.Integer(string="Record Id", required=True, readonly=True)

    # Model references
    model = fields.Char(string="Model", required=True, readonly=True)

    # Field references
    field = fields.Char(string="Field", required=True, readonly=True)
    field_id = fields.Many2one(comodel_name='ir.model.fields', string="Field ID", readonly=True)

    old_value = fields.Char(string="Original Value", readonly=True)
    new_value = fields.Char(string="Updated Value", readonly=True)
    method = fields.Char(string="Operation type", readonly=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company.id)

    @staticmethod
    def _old_value(record, key):
        """
        Return old value of record, cleanly.
        """
        if hasattr(record, key):
            if isinstance(record[key], models.Model):
                key_record = record[key]

                if len(key_record) > 1:
                    key_list = []
                    for i in range(0, len(key_record)):
                        this_key = key_record[i]
                        if hasattr(this_key, "id"):
                            key_list.append(this_key.id)
                    return key_list

                elif hasattr(key_record, "id"):
                    return [key_record.id]

            return str(record[key])
        return None

    @staticmethod
    def filtered_values(model, values):
        u"""
        :return: dictionary of values with excluded specified in model values (_excluded_values)
        """
        for value in model._excluded_values:
            if value in values:
                values.pop(value)
        return values

    @api.model
    def _get_model_obj(self, model_name):
        return self.env['ir.model'].search([('model', '=', model_name)], limit=1)

    @api.model
    def _get_field_obj(self, model_name, key=None):
        field_obj = self.env['ir.model.fields']

        if key:
            field_val = field_obj.search([('model', '=', model_name), ('name', '=', key)], limit=1)
        else:
            field_val = field_obj.search([('model', '=', model_name), ('name', 'in', ('name', 'display_name'))],
                                         limit=1)

        if not field_val and model_name == 'res.users':
            field_val = field_obj.search([('model', '=', 'res.users'), ('name', '=', 'groups_id')])

        return field_val

    @api.model
    def _field_change_log(self, method, model, record, values):
        u"""
        Will log changes on field's values level
        we add some extra items into values so parent/child structure is always available for reporting
        For example, if a bank account is changed the partner_id does not, so the report does not show which partner the change relates to
        wrapped in big try, except to handle unknown instances
        """
        model_name = record._name
        model_obj = self._get_model_obj(model_name)
        values = dict(values) if values else {}

        fields = self.env['ir.model.fields'].search([('model_id', '=', model_obj.id)])
        for field in fields:

            if not hasattr(field, field.name):
                continue

            if field.relation == 'res.partner' and field.ttype == 'many2one' and field.name not in values:
                field_name = field.name
                values[field_name] = record[field_name].id

            if field.relation == 'account.financial.budget' and field.ttype == 'many2one' and not values.get(field):
                field_name = field.name
                values[field_name] = record[field_name].id

            if field.relation == 'dfa.rule' and field.ttype == 'many2one' and not values.get(field):
                field_name = field.name
                values[field_name] = record[field_name].id

            if field.relation == 'product.template' and field.ttype == 'many2one' and not values.get(field):
                field_name = field.name
                values[field_name] = record[field_name].id

        for key, value in values.items():
            new_value = ''
            try:
                # special constraint as we do not write password etc just security changes
                if model._name == 'res.users' and key[:8] not in ('in_group', 'sel_grou'):
                    continue
                if model._name == 'res.users' and key[:8] == 'in_group':
                    if value:
                        value = key[9:11]
                        old_value = False
                    else:
                        old_value = key[9:11]
                    key = 'groups_id'
                    field = record._fields.get(key)
                elif model._name == 'res.users' and key[:8] == 'sel_grou':
                    if value:
                        old_value = False
                    else:
                        old_value = key[11:13]
                    key = 'groups_id'
                    field = record._fields.get(key)
                else:
                    field = record._fields.get(key)
                    old_value = self._old_value(record, key)

                if not field:
                    continue

                if field.type == "binary" or field.type == "one2many":
                    continue

                if old_value and old_value != 'False':
                    if isinstance(old_value, list):
                        old_value_to_use = False
                        for i in range(0, len(old_value)):
                            if old_value[i] and isinstance(old_value[i], int):
                                if old_value_to_use:
                                    old_value_to_use = old_value_to_use + '; ' + self.env[field.comodel_name].browse(
                                        int(old_value[i])).display_name
                                else:
                                    old_value_to_use = self.env[field.comodel_name].browse(
                                        int(old_value[i])).display_name
                        old_value = old_value_to_use

                if field.type == 'many2many' and value and isinstance(value, list):
                    new_recs_dict = {}
                    new_rec_list = []
                    new_value = False
                    if value[0][0] in (0, 1):
                        new_recs_dict = value[0][2]
                        if not new_recs_dict:
                            value = ''
                    elif value[0][0] in (2, 3):
                        value = ''
                    elif value[0][0] == 4:
                        new_rec_list = [0][1]
                        if not new_rec_list:
                            value = ''
                    elif value[0][0] == 5:
                        value = ''
                    elif value[0][0] == 6:
                        new_rec_list = value[0][2]
                        if not new_rec_list:
                            value = ''

                    if new_recs_dict:
                        value = 'New lookup being created'
                    elif new_rec_list:
                        for i in range(0, len(new_rec_list)):
                            if not new_value:
                                new_value = str(self.env[field.comodel_name].browse(int(new_rec_list[i])).display_name)
                            else:
                                new_value = str(new_value) + '; ' + str(
                                    self.env[field.comodel_name].browse(int(new_rec_list[i])).display_name)
                        value = new_value

                elif field.type == 'many2one':
                    if isinstance(value, int):
                        value = self.env[field.comodel_name].browse(int(value)).display_name

                field_obj = self._get_field_obj(model_name, key)

                if not value:
                    value = 'False'
                if not old_value:
                    old_value = 'False'

                if (value or old_value) and value != old_value:
                    log_data = {
                        "login": model.env.user.login,
                        "record_id": record.id,
                        "method": method,
                        "model": model._name,
                        "field": field and field.string or key or '',
                        "field_id": field_obj and field_obj.id or False,
                        "old_value": str(old_value),
                        "new_value": str(value)
                    }
                    self.create(log_data)

            except:
                pass

    @api.model
    def _record_change_log(self, method, model, record, values=None):
        u"""
        Will log status of record change - if it's deleted or created.
        wrapped in big try, except to handle unknown instances
        """
        model_name = record._name
        values_raw = values or {}

        # If values is a list with 1 dict, extract it
        if isinstance(values_raw, list):
            if values_raw and isinstance(values_raw[0], dict):
                values = values_raw[0]
            else:
                values = {}
        elif isinstance(values_raw, dict):
            values = values_raw
        else:
            values = {}

        # Scrub values in dictionary
        if values:
            scrubbed = dict(values)
            for key, value in values.items():
                try:
                    if isinstance(value, datetime.datetime) or isinstance(value, datetime.date):
                        scrubbed[key] = str(value)

                    # get rid of binary
                    field = record._fields.get(key)
                    if field and field.type and (field.type == "binary" or field.type == 'one2many'):
                        continue
                    if not field:
                        continue

                    field_obj = self._get_field_obj(model_name, key)

                    if field.type == 'many2many' and value and isinstance(value, list):
                        new_recs_dict = {}
                        new_rec_list = []
                        new_value = False
                        if value[0][0] in (0, 1):
                            new_recs_dict = value[0][2]
                            if not new_recs_dict:
                                value = ''
                        elif value[0][0] in (2, 3):
                            value = ''
                        elif value[0][0] == 4:
                            new_rec_list = [0][1]
                            if not new_rec_list:
                                value = ''
                        elif value[0][0] == 5:
                            value = ''
                        elif value[0][0] == 6:
                            new_rec_list = value[0][2]
                            if not new_rec_list:
                                value = ''

                        if new_recs_dict:
                            value = 'New lookup being created'
                        elif new_rec_list:
                            for i in range(0, len(new_rec_list)):
                                if not new_value:
                                    new_value = str(
                                        self.env[field.comodel_name].browse(int(new_rec_list[i])).display_name)
                                else:
                                    new_value = str(new_value) + '; ' + str(
                                        self.env[field.comodel_name].browse(int(new_rec_list[i])).display_name)
                            value = new_value

                    elif field.type == 'many2one':
                        if isinstance(value, int):
                            value = self.env[field.comodel_name].browse(int(value)).display_name

                    if value:
                        if method == 'create':
                            old_value = ''
                            new_value = value
                        else:
                            old_value = value
                            new_value = ''

                        log_data = {
                            "login": model.env.user.login,
                            "record_id": record.id,
                            "method": method,
                            "model": model._name,
                            "field": field and field.string or key or '',
                            "field_id": field_obj and field_obj.id or False,
                            "old_value": old_value,
                            "new_value": new_value,
                        }
                        self.create(log_data)

                except:
                    pass

    @api.model
    def _log_operation(self, method, model, values=None):
        u"""
        Method-router to different log level accordingly to event happened
        :param method: (string) either "create', 'update' or 'delete' for now
        :param model: model with which event happened
        :param values: new values of existing record, None in case of unlinking
        """
        _logger.debug("{} for name={}, ids={}".format(method, model._name, model.ids))
        if method in ["delete", "create"]:
            for record in model:
                self._record_change_log(method, model, record, values)

        else:
            for record in model:
                self._field_change_log(method, model, record, values)

    def write_with_log(self, clazz, model, values):
        self._log_operation('update', model, values)
        return super(clazz, model).write(values)

    def create_with_log(self, clazz, model, values):
        # to have a record we have to create first, and then log
        res = super(clazz, model).create(values)
        values = AuditLogging.filtered_values(model, values)
        self._log_operation('create', res, values)
        return res

    def unlink_with_log(self, clazz, model):
        values = model.read(self)

        if values:
            self._log_operation('delete', model, values[0])
            return super(clazz, model).unlink()

    def unlink(self):
        raise UserError("Audit records cannot be removed")


class AuditLoggingGroup(models.Model):
    _name = 'audit.logging.group'

    name = fields.Char(string='Grouping Name', required=True)
    model_id = fields.Many2one(comodel_name='ir.model', required=True,
                               domain="[('audit_logging', '=', True)]",
                               ondelete='cascade',
                               help="For audit reporting, results for this grouping name will be grouped by the field linked to this model")
    field_id = fields.Many2one(comodel_name='ir.model.fields', string='Field to Use',
                               domain="[('model_id', '=', model_id)]",
                               help='Must be either the ID field or a Many2one to another model')
