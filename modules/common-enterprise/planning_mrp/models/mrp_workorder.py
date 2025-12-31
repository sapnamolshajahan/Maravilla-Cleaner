# -*- coding: utf-8 -*-
from odoo import models, fields,api,_
from dateutil.relativedelta import relativedelta


class MRPWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    def get_planning_slot(self):
        for record in self:
            model = self.env['ir.model'].search([('model', '=', self._name)])
            planning_slot = self.env['planning.slot'].search([('model_id', '=', model.id),
                                                              ('res_id', '=', record.id)], limit=1)
            if planning_slot:
                record.planning_slot_id = planning_slot.id
            else:
                record.planning_slot_id = False

    planning_slot_id = fields.Many2one('planning.slot', string='Planning Slot',
                                       compute='get_planning_slot', store=True)


    def create_planning_slot(self, record, update_dict):
        role_id = self.env['planning.role'].search([('usage', '=', 'workorder')],
                                                   limit=1)

        if update_dict.get('date_start'):
            date_from = update_dict['date_start']
        else:
            date_from = fields.Date.context_today(self) + relativedelta(days=1, hours=12)

        if update_dict.get('date_finished'):
            date_to = update_dict['date_finished']
        else:
            date_to = fields.Date.context_today(self) + relativedelta(days=1, hours=13)


        model = self.env['ir.model'].search([('model', '=', record._name)])
        self.env['planning.slot'].with_context(planning_enterprise_base=True).sudo().create({
            'start_datetime': date_from,
            'end_datetime': date_to,
            'employee_id': False,
            'role_id': role_id.id if role_id else False,
            'name': record.production_id.name,
            'model_id': model.id,
            'res_id': record.id,

        })

    @api.model_create_multi
    def create(self, vals_list):
        res = super(MRPWorkOrder, self).create(vals_list)
        for record in res:
            self.create_planning_slot(record, {})
        return res

    def write(self, values):
        if self.env.context.get('planning_enterprise_base', None):
            return super(MRPWorkOrder, self).write(values)

        if not self:
            return super(MRPWorkOrder, self).write(values)

        if isinstance(values, dict):
            update_dict = {}
            if values.get('date_start', None):
                update_dict['start_datetime'] = values['date_start']
            if values.get('date_finished', None):
                update_dict['end_datetime'] = values['date_finished']
            if update_dict:
                if not self.planning_slot_id:
                    self.create_planning_slot(self[0], update_dict)
                else:
                    self.planning_slot_id.with_context(planning_enterprise_base=True).sudo().write(update_dict)

        else:
            for i in range(0, len(values)):
                update_dict = {}
                if values[i].get('date_start', None):
                    update_dict['start_datetime'] = values['date_start']
                if values[i].get('date_finished', None):
                    update_dict['end_datetime'] = values['date_finished']
                if update_dict:
                    if not self[i].planning_slot_id:
                        self.create_planning_slot(self[i], update_dict)
                    else:
                        self[i].planning_slot_id.with_context(planning_enterprise_base=True).sudo().write(update_dict)

        return super(MRPWorkOrder, self).write(values)

