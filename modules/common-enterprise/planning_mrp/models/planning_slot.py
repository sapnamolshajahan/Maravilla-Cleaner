# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import datetime


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    """
    The leave records will be readonly - all updates have to come from HR.
    Project tasks can have resource allocation or start | end datetime changes 
    """

    model_id = fields.Many2one('ir.model', string='Model')
    model_name = fields.Char(string='Model Name', related='model_id.name')
    res_id = fields.Integer(string='Record ID')
    division = fields.Many2one('account.analytic.account', string='Division')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    other_users = fields.Many2many('res.users', string='Other Employees',
                                   help='If set, an additional shift will be created per employee')
    district = fields.Many2one('account.analytic.account', string='District')

    # OVERRIDE - we just want end - start as allocated hours for individual
    @api.depends('start_datetime', 'end_datetime')
    def _compute_allocated_hours(self):
        for record in self:
            if record.start_datetime and record.end_datetime and record.end_datetime > record.start_datetime:
                hours = (record.end_datetime - record.start_datetime).seconds / 3600
                record.allocated_hours = hours
            else:
                record.allocated_hours = 0.0

    def check_values(self, values):
        update_dict = {}
        if values.get('start_datetime', None):
            update_dict['planned_date_begin'] = values['start_datetime']
        if values.get('end_datetime', None):
            update_dict['date_deadline'] = values['end_datetime']
        return update_dict

    def values_workorder(self, values):
        update_dict = {}
        if values.get('start_datetime', None):
            update_dict['date_start'] = values['start_datetime']
        if values.get('end_datetime', None):
            update_dict['date_finished'] = values['end_datetime']
        return update_dict

    def write(self, values):  # NOT an api_multi
        # to stop any funny issues with end datetime < start datetime
        if values.get('start_datetime', None) and values.get('end_datetime', None):
            start_datetime = values['start_datetime']
            end_datetime = values['end_datetime']
            if end_datetime <= start_datetime:
                end_datetime = start_datetime + relativedelta(hours=1)
                values['end_datetime'] = end_datetime
        if self.env.context.get('planning_enterprise_base', None):
            return super(PlanningSlot, self).write(values)
        if not self[0].model_id or self[0].model_name == 'Time Off':
            return super(PlanningSlot, self).write(values)

        for record in self:
            record_to_update = self.env[self.model_id.model].browse(record.res_id)

            if record.model_id.model == 'mrp.workorder':
                return super(PlanningSlot, self).write(values)

            """
            If other resources are committed to a planning slot, we create a planning slot per employee.
            Assuming the source slot is linked to a record, then the create will also link the extra employee to the
            same record.
            """
            if values.get('other_users', None):
                other_users = values['other_users']
                for k in range(0, len(other_users)):
                    other_user_id = other_users[k][1]
                    if other_user_id:
                        other_user = self.env['res.users'].browse(other_user_id)
                        resource = other_user.employee_id.resource_id.id
                        self.copy({'resource_id': resource, 'other_users': False})
                        user_id = other_user.employee_id.user_id
                        if user_id not in [x.user_id.id for x in record_to_update.user_ids]:
                            record_to_update.with_context(planning_enterprise_base=True).write(
                                {'user_ids': [(4, user_id.id)]})
                values.pop('other_users')

            if values.get('resource_id'):
                if isinstance(values['resource_id'], int):
                    resource = self.env['resource.resource'].browse(values['resource_id'])
                    user_id = resource.employee_id.user_id
                    if user_id and user_id not in [x.user_id.id for x in record_to_update.user_ids]:
                        record_to_update.with_context(planning_enterprise_base=True).write(
                            {'user_ids': [(4, user_id.id)]})
                else:
                    users_to_add = users_to_delete = False
                    for l in range(0, len(values['resource_id'])):
                        if not sub_list:
                            sub_list = values['resource_id'][l]
                        if sub_list[0] == 4:
                            users_to_add = sub_list[0]
                        else:
                            users_to_delete = sub_list[0]

                        if users_to_add:
                            resource = self.env['resource.resource'].browse(users_to_add)
                            user_id = resource.employee_id.user_id
                            if user_id not in [x.user_id.id for x in record_to_update.user_ids]:
                                record_to_update.with_context(planning_enterprise_base=True).write(
                                    {'user_ids': [(4, user_id.id)]})

                        elif users_to_delete:
                            resource = self.env['resource.resource'].browse(users_to_add)
                            user_id = resource.employee_id.user_id
                            if user_id in [x.user_id.id for x in record_to_update.user_ids]:
                                record_to_update.with_context(planning_enterprise_base=True).write(
                                    {'user_ids': [(3, user_id.id)]})


        return super(PlanningSlot, self).write(values)

    @api.model_create_multi
    def create(self, vals_list):
        for i in range(0, len(vals_list)):
            # to stop any funny issues with end datetime < start datetime
            if vals_list[i].get('start_datetime', None) and vals_list[i].get('end_datetime', None):
                start_datetime = vals_list[i]['start_datetime']
                end_datetime = vals_list[i]['end_datetime']
                if end_datetime <= start_datetime:
                    end_datetime = start_datetime + relativedelta(hours=1)
                    vals_list[i]['end_datetime'] - end_datetime
        res = super(PlanningSlot, self).create(vals_list)
        for i in range(0, len(vals_list)):
            user_list = []
            if vals_list[i].get('other_users', None):
                other_users = vals_list[i]['other_users']
                for k in range(0, len(other_users)):
                    other_user_id = other_users[k][1]
                    if other_user_id:
                        user_list.append(other_user_id)


            if vals_list[i].get('other_users', None):
                other_users = vals_list[i]['other_users']
                resource = False
                for k in range(0, len(other_users)):
                    other_user_id = other_users[k][1]
                    if other_user_id:
                        other_user = self.env['res.users'].browse(other_user_id)
                        resource = other_user.employee_id.resource_id.id
                    res[i].copy({'resource_id': resource, 'other_users': False})
                    res[i].with_context(planning_enterprise_base=True).write({'other_users': False})

        return res
