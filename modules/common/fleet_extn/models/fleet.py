# -*- coding: utf-8 -*-

from odoo import fields, models, api


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    employee_id = fields.Many2one('hr.employee', 'Driver', help='Driver of the vehicle')
    purchase_order_line_id = fields.One2many(comodel_name="purchase.order.line", inverse_name="fleet_id",
                                             string="Purchase Order Lines")
    stock_move_id = fields.One2many(comodel_name="stock.move", inverse_name="fleet_id", string="Stock Moves")
    registration_expiry_date = fields.Date(string='Registration Expiry Date')
    cert_of_compliance_date = fields.Date(string='Certificate of Compliance Expiry Date')
    payload_weight = fields.Integer(string='Payload Weight')
    tare_weight = fields.Integer(string='Tare Weight')
    iso_code = fields.Char(string='ISO Code')
    notes = fields.Text('Notes')

    def write(self, vals):
        for vehicle in self:
            changes = []
            if 'employee_id' in vals and vehicle.employee_id.id != vals['employee_id']:
                value = self.env['hr.employee'].browse(vals['employee_id']).name
                olddriver = vehicle.employee_id.name or 'None'
                changes.append("Driver: from '%s' to '%s'" % (olddriver, value))
            if len(changes) > 0:
                self.message_post(body=", ".join(changes))

            return super(FleetVehicle, self).write(vals)
