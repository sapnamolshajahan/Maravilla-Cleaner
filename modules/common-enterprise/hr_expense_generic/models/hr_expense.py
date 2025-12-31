from odoo.exceptions import ValidationError, UserError

from odoo import api, fields, Command, models, _


class HRExpense(models.Model):
    _inherit = "hr.expense"

    def _default_payment_mode(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee and employee.default_payment_mode:
            return employee.default_payment_mode
        return self.env.company.default_payment_mode

    payment_mode = fields.Selection(
        selection=[
            ('own_account', "Employee (to reimburse)"),
            ('company_account', "Company")
        ],
        string="Paid By",
        tracking=True,
        required=True,
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'payment_mode' in res:
            res['payment_mode'] = self._default_payment_mode()
        return res

    def action_submit_expenses(self):
        for record in self:
            attachments = self.env['ir.attachment'].search(
                [('res_model', '=', 'hr.expense'), ('res_id', '=', record.id)])
            if not attachments:
                raise ValidationError(_("At least One attachment required to Save this Expense!"))
        return super(HRExpense, self).action_submit_expenses()

    def _fill_document_with_results(self, ocr_results):
        old_name = self.name
        result = super()._fill_document_with_results(ocr_results)
        self.name = old_name
        return result


class HREmployee(models.Model):
    _inherit = "hr.employee"

    default_payment_mode = fields.Selection(
        [('own_account', 'Employee (to reimburse)'),
         ('company_account', 'Company')],
        string="Default Payment Mode"
    )
