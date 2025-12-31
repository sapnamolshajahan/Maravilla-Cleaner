# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ###########################################################################
    # Default and compute methods
    ###########################################################################
    @api.model
    def get_selection_name(self, model, selection_field_name, selected_option):
        for item in model._fields[selection_field_name].selection:
            if item[0] == selected_option:
                return item[1]

    def _compute_bg_task_state(self):
        for so in self:
            if so.bg_task_id:
                self.env.cr.execute("SELECT state FROM queue_job WHERE uuid = %s", (so.bg_task_id,))
                res = self.env.cr.fetchall()
                if res:
                    val = res[0][0]
                    so.bg_task_state = self.get_selection_name(self.env['queue.job'], 'state', val)
                else:
                    so.bg_task_state = None

            else:
                so.bg_task_state = None

    ###########################################################################
    # Fields
    ###########################################################################

    queued_state = fields.Selection(
        selection=[('queued', 'Queued for Processing'), ('processed', 'Done')],
        string='Queued State',
        copy=False
    )

    # don't make many2one as it causes deadlocks
    bg_task_id = fields.Char(string='Task ID', readonly=True, copy=False)
    bg_task_state = fields.Char(string='Task State', compute='_compute_bg_task_state')

    ###########################################################################
    # Methods
    ###########################################################################
    def action_confirm_queued(self):
        self.ensure_one()
        self.check_credit_limit()
        #  Double check but view should not allow button to be visible
        if self.queued_state and self.picking_ids and self.state != 'draft':
            raise UserError("Sale Order already confirmed")

        threshold = self.env.company.auto_background_sale_threshold
        if threshold and len(self.order_line) > threshold:
            # Bypass write method and chatter creation
            query = "UPDATE sale_order SET state = 'sale', queued_state = 'queued' WHERE id = %s"
            self.env.cr.execute(query, (self.id,))

            task = self.with_delay(
                channel=self.light_job_channel(),
                description="Sale Order Background Confirm ({})".format(self.name)
            )._run_so_confirm(
                so_id=self.id,
                uid=self.env.user.id,
            )
            self.bg_task_id = task.uuid
            self.message_post(body="Queued for SO Confirm")

        else:
            self.action_confirm()

    def action_reset_queued_processing(self):
        if self.queued_state == 'queued':
            self.write({'state': 'draft', 'queued_state': False, 'bg_task_id': False})

        return True

    def _run_so_confirm(self, so_id, uid):
        """Sale Order Confirm Background Job"""
        so = self.with_user(uid).browse(int(so_id))

        if so.queued_state == 'queued':
            if so.state == 'sale':
                self.env.cr.execute("UPDATE sale_order SET state = 'draft' WHERE id = %s", (so.id,))
                so.invalidate_recordset()
                so.with_context(skip_credit_check=True).action_confirm()

            so.queued_state = 'processed'

        return True
