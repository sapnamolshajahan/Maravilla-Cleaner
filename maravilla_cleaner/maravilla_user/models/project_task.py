from odoo import models,fields,api,exceptions
import logging,traceback

_logger = logging.getLogger(__name__)

DONE_STAGE_ID = 25

class ProjectTask(models.Model):
    _inherit = "project.task"

    room_number = fields.Char(string="Room Number")
    room_type = fields.Char(string="Room Type")
    num_person = fields.Integer(string="Number of Persons")
    remarks = fields.Text(string="Remarks")
    employee_ids = fields.Many2many("hr.employee",string="Assigned Employees")

    user_ids = fields.Many2many(
        domain="[('share', '=', True), ('active', '=', True)]"
    )

    @api.model
    def create(self, vals):
        _logger.info("Creating new task with auto-assignment")
        task = super().create(vals)
        if not self.env.context.get('assigning_employees'):
            task.with_context(assigning_employees=True).assign_available_employees()
        return task

    def write(self, vals):
        res = super().write(vals)
        # Reassign only if relevant fields change AND we have records AND not already assigning
        if any(field in vals for field in ['num_person', 'planned_date_begin', 'date_deadline']):
            if not self.env.context.get('assigning_employees') and self:
                _logger.info(f"Triggering employee assignment for tasks: {self.ids}")
                self.with_context(assigning_employees=True).assign_available_employees()
        return res

    def assign_available_employees(self):

        if not self:
            _logger.warning(f"Skipping assignment - no records: {self.ids}")
            return

        for task in self:
            try:
                _logger.info(f"Processing task {task.id}")

                if not task.planned_date_begin or not task.date_deadline:
                    _logger.warning(f"Task {task.id} has no scheduled dates — skipping")
                    continue

                required = task.num_person or 0
                if required <= 0:
                    _logger.info(f"Task {task.id} has personnel requirement 0 — skipping")
                    continue

                _logger.info(f"Task {task.id} requires {required} employees")

                # Get all available employees
                available_employees = self.get_available_employees(
                    task.planned_date_begin,
                    task.date_deadline
                )

                # Filter only portal-linked employees
                employees_with_portal_users = available_employees.filtered(
                    lambda emp: emp.user_id and emp.user_id.has_group('base.group_portal')
                )

                _logger.info(f"Available employees: {len(available_employees)}")
                _logger.info(
                    f"Portal-mapped employees: {len(employees_with_portal_users)} -> {employees_with_portal_users.ids}")

                # Raise proper validation
                if len(employees_with_portal_users) < required:
                    raise exceptions.ValidationError(
                        f"Task {task.display_name}: Need {required} employees, found only {len(employees_with_portal_users)}"
                    )

                # Pick required employees
                selected_employees = employees_with_portal_users[:required]
                selected_users = selected_employees.mapped('user_id')

                _logger.info(f"Assigning employees: {selected_employees.ids}")
                _logger.info(f"Assigning portal users: {selected_users.ids}")

                # Assign to task
                task.employee_ids = [(6, 0, selected_employees.ids)]
                task.user_ids = [(6, 0, selected_users.ids)]

                _logger.info(f"Task {task.id} assignment successful ✔")

            except exceptions.ValidationError as e:
                # Validation errors should show directly to user
                _logger.error(f"Validation Error in task {task.id}: {str(e)}")
                raise

            except Exception as e:
                _logger.critical(f"Unexpected error during assignment for task {task.id}: {str(e)}")
                _logger.critical(traceback.format_exc())
                # continue safely instead of crashing whole loop
                continue

    def get_available_employees(self, start, end):
        """More efficient query to find available employees"""
        # Find employees with overlapping tasks
        overlapping_tasks = self.env['project.task'].search([
            ('planned_date_begin', '<', end),
            ('date_deadline', '>', start),
            ('stage_id', '!=', 25)
        ])

        busy_employee_ids = overlapping_tasks.mapped('employee_ids.id')

        # Return employees not in busy list AND have portal users
        return self.env['hr.employee'].search([
            ('id', 'not in', busy_employee_ids),
            ('user_id', '!=', False),
            ('user_id.group_ids', 'in', self.env.ref('base.group_portal').id)
        ])

