from odoo import models,fields

class SaleOrder(models.Model):

    _inherit = 'sale.order'
    _description = 'Sale order inherit'

    room_number = fields.Char(string="Room Number")
    room_type = fields.Char(string="Room Type")
    check_in = fields.Date(string="Check In")
    check_out = fields.Date(string="Check Out")
    num_person = fields.Integer(string="Number of Persons")
    remarks = fields.Text(string="Remarks")

    def action_confirm(self):
        res = super().action_confirm()

        for order in self:
            print(f"SO: {order.name}, Check-in: {order.check_in}, Check-out: {order.check_out}")

            fsm_tasks = self.env['project.task'].search([
                ('sale_order_id', '=', order.id),
                ('is_fsm', '=', True),
            ])

            # Apply mapping and save to database
            if fsm_tasks:
                fsm_tasks.write({
                    'planned_date_begin': order.check_in,
                    'date_deadline': order.check_out,
                    'room_number':order.room_number,
                    'room_type':order.room_type,
                    'num_person':order.num_person,
                    'remarks':order.remarks,

                })

        return res