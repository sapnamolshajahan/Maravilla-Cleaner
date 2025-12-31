from odoo import models, fields, api
from datetime import date, timedelta


class FireDrills(models.Model):
    _name = 'fire.drills'
    _description = 'Fire Drills'
    _rec_name = 'name'

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default='New')
    date = fields.Date(string="Date", required=True)
    location_id = fields.Many2one('res.company', string="Location", default=lambda self: self.env.company)
    fire_warden_ids = fields.Many2many('hr.employee', string="Fire Wardens")
    time = fields.Datetime(string="Drill Time")
    time_to_assemble_point = fields.Datetime(string="Time to Assemble Point")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('fire.drills.sequence') or 'New'
        return super(FireDrills, self).create(vals_list)

    @api.model
    def _check_next_fire_drill_due(self):
        config_records = self.env['next.fire.drill'].search([])
        if not config_records:
            return
        # Get the latest drill record
        last_drill = self.search([], order="date desc", limit=1)
        if not last_drill or not last_drill.date:
            return
        # Calculate how many days have passed since the last drill
        today = date.today()
        days_since_last = (today - last_drill.date).days
        # Loop through config records and check which one matches the period
        for config in config_records:
            if days_since_last == config.period_days:
                employee = config.responsible_id
                if employee and employee.work_email:
                    template = self.env.ref('hr_fire_drill.email_template_fire_drill_reminder',
                                            raise_if_not_found=False)
                    if template:
                        template.send_mail(employee.id, force_send=True)


class FireDrillConfig(models.Model):
    _name = 'next.fire.drill'
    _description = 'Next Fire Drill'
    _rec_name = 'period_days'

    period_days = fields.Integer(string="Period Between Fire Drills (Days)", required=True)
    responsible_id = fields.Many2one('hr.employee', string="Responsible Employee", required=True)