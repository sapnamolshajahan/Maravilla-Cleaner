from odoo import models,fields,api
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):

    _inherit = 'res.users'
    _description = 'extend function to create employee for portal user'

    x_employee_id = fields.Many2one('hr.employee', string='Employee')


    @api.model
    def _signup_create_user(self, values):
        """Create a portal user"""

        portal_group = self.env.ref('base.group_portal')

        user = self.create({
            'name': values.get("name"),
            'email': values.get("email"),
            'login': values.get("login"),
            'password': values.get("password"),
            'group_ids': [(6, 0, [portal_group.id])]  # Set groups directly
        })


        # self.create_technician_user(user)

        return user.id

    # def create_technician_user(self, user):
    #     """Create employee for a newly created portal user"""
    #
    #     # Step 1: Create Employee
    #     employee = self.env['hr.employee'].sudo().create({
    #         'name': user.name,
    #         'work_email': user.email,
    #         'user_id': user.id,
    #     })
    #
    #     # Step 2: Link employee inside user
    #     user.sudo().write({
    #         'x_employee_id': employee.id
    #     })
    #
    #     return user

    @api.model
    def create(self, vals):
        user = super().create(vals)
        user.process_employee_group_logic()
        return user

    def write(self, vals):
        res = super().write(vals)
        self.process_employee_group_logic()
        return res

    def process_employee_group_logic(self):

        group_portal = self.env.ref("base.group_portal")
        group_employee = self.env.ref("maravilla_user.group_is_employee")  # << change module_name

        for user in self:


            if group_employee not in user.group_ids:
                return


            allowed_groups = [group_portal.id, group_employee.id]
            for grp in user.group_ids:
                if grp.id not in allowed_groups:
                    user.write({"group_ids": [(3, grp.id)]})  # remove


            if group_portal not in user.group_ids:
                user.write({"group_ids": [(4, group_portal.id)]})


            if not self.env["hr.employee"].sudo().search([("user_id", "=", user.id)], limit=1):

                employee = self.env["hr.employee"].sudo().create({
                    "name": user.name,
                    "work_email": user.email,
                    "user_id": user.id,
                })
                user.write({"x_employee_id": employee.id})

