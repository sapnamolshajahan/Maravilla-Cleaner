# -*- coding: utf-8 -*-
from odoo import models, fields,api,_
from datetime import date, datetime, time



class HRLeave(models.Model):
    _inherit = 'hr.leave'

    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        super_res = super(HRLeave, self)._get_durations(check_leave_type=check_leave_type,
                                                        resource_calendar=resource_calendar)
        if isinstance(super_res, dict):
            base = dict(super_res)
        else:
            base = {rec.id: super_res for rec in self}

        for rec in self:
            if rec.request_unit_hours and rec.request_hour_from and rec.request_hour_to and \
                    (rec.request_hour_to > rec.request_hour_from):
                hours = 0.0
                if isinstance(rec.date_from, datetime) and isinstance(rec.date_to, datetime):
                    delta = rec.date_to - rec.date_from
                    hours = delta.total_seconds() / 3600.0
                base[rec.id] = (0, hours)

        return base

    def _get_leaves_on_public_holiday(self):
        if self.request_unit_hours and self.request_hour_from or self.request_hour_to and \
                (self.request_hour_to > self.request_hour_from):
            return False
        return super(HRLeave, self)._get_leaves_on_public_holiday()

    def get_planning_slot(self):
        for record in self:
            model = self.env['ir.model'].search([('model', '=', self._name)])
            planning_slot = self.env['planning.slot'].search([('model_id', '=', model.id),
                                                              ('res_id', '=', record.id)])
            if planning_slot:
                record.planning_slot_id = planning_slot.id
            else:
                record.planning_slot_id = False

    planning_slot_id = fields.Many2one('planning.slot', string='Planning Slot',
                                       compute='get_planning_slot', store=True)

    def create_planning_slot(self, record, update_dict):
        role_id = self.env['planning.role'].search([('usage', '=', 'leave')],
                                                   limit=1)

        if update_dict.get('start_datetime'):
            date_from = update_dict['start_datetime']
        else:
            if record.date_from and isinstance(record.date_from, date):
                mytime = time(8, 00, 00)
                date_from = datetime.combine(record.date_from, mytime)
            else:
                date_from = record.date_from

        if update_dict.get('end_datetime'):
            date_to = update_dict['end_datetime']
        else:
            if record.date_to and isinstance(record.date_to, date):
                mytime = time(17, 00, 00)
                date_to = datetime.combine(record.date_to, mytime)
            else:
                date_to = record.date_to

        model = self.env['ir.model'].search([('model', '=', record._name)])
        self.env['planning.slot'].with_context(planning_enterprise_base=True).sudo().create({
            'start_datetime': date_from,
            'end_datetime': date_to,
            'resource_id': record.employee_id.resource_id.id,
            'employee_id': record.employee_id.id,
            'role_id': role_id.id if role_id else False,
            'name': record.holiday_status_id.name + ' for ' + record.employee_id.name,
            'division': record.employee_id.user_id.division.id,
            'district': record.employee_id.user_id.district.id,
            'model_id': model.id,
            'res_id': record.id,

        })

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HRLeave, self).create(vals_list)
        for record in res:
            if record.state in ('cancel', 'refuse'):
                continue
            self.create_planning_slot(record, {})
        return res

    def write(self, values):
        if self.env.context.get('planning_enterprise_base', None):
            return super(HRLeave, self).write(values)

        if isinstance(values, dict):
            if values.get('state', None):
                if values['state'] == 'refuse' and self.planning_slot_id:
                    self.planning_slot_id.sudo().unlink()
                    return super(HRLeave, self).write(values)
                if values['state'] == 'draft':
                    return super(HRLeave, self).write(values)

            update_dict = {}
            if values.get('date_from', None):
                update_dict['start_datetime'] = values['date_from']
            else:
                return super(HRLeave, self).write(values)   # not a complete record
            if values.get('date_to', None):
                update_dict['end_datetime'] = values['date_to']
            if not self.planning_slot_id:
                self.create_planning_slot(self, update_dict)
            else:
                self.planning_slot_id.with_context(planning_enterprise_base=True).sudo().write(update_dict)

        else:
            for i in range(0, len(values)):
                update_dict = {}
                if values[i].get('state', None):
                    if values[i]['state'] == 'refuse' and self[i].planning_slot_id:
                        self[i].planning_slot_id.sudo().unlink()
                        return super(HRLeave, self).write(values)
                    if values[i]['state'] == 'draft':
                        return super(HRLeave, self).write(values)
                if values[i].get('date_from', None):
                    update_dict['start_datetime'] = values['date_from']
                else:
                    continue
                if values[i].get('date_to', None):
                    update_dict['end_datetime'] = values['date_to']
                if not self[i].planning_slot_id:
                    self.create_planning_slot(self[i], update_dict)
                else:
                    self[i].planning_slot_id.with_context(planning_enterprise_base=True).sudo().write(update_dict)

        return super(HRLeave, self).write(values)

