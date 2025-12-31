from odoo import models, fields, api


class FieldService(models.Model):
    _inherit = "project.task"

    reference = fields.Char(string='Reference')
    work_order = fields.Char(string='Work Order')
    purchase_order = fields.Char(string='Purchase Order')

    customer_reference = fields.Char(
        string="Customer Reference",
        compute="_compute_customer_reference",
        store=True
    )

    @api.depends('purchase_order', 'work_order', 'reference')
    def _compute_customer_reference(self):
        for task in self:
            if task.purchase_order:
                task.customer_reference = task.purchase_order
            elif task.work_order:
                task.customer_reference = task.work_order
            else:
                task.customer_reference = task.reference

    @api.model
    def create(self, vals):
        task = super().create(vals)

        # Auto-populate Reference from Sales Order
        if task.sale_line_id and task.sale_line_id.order_id:
            so = task.sale_line_id.order_id
            if so.client_order_ref:
                task.reference = so.client_order_ref

        return task

