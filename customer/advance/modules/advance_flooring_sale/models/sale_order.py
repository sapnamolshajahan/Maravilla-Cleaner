from odoo import models, fields, api, _
from datetime import date


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    is_firm = fields.Boolean(string="Firm")
    is_commercial = fields.Boolean(string="Commercial")
    proposal_no = fields.Char(string="Proposal Number")
    project_name = fields.Char(string="Project Name")
    date_only = fields.Date(string='Order Date',compute='_compute_date_only',store=True)
    commitment_date_only = fields.Date(
        string='Commitment Date',
        compute='_compute_commitment_date_only',
        inverse='_inverse_commitment_date_only',
        store=True
    )

    @api.depends('commitment_date')
    def _compute_commitment_date_only(self):
        for order in self:
            if order.commitment_date:
                order.commitment_date_only = order.commitment_date.date()

    def _inverse_commitment_date_only(self):
        for order in self:
            if order.commitment_date_only:
                order.commitment_date = fields.Datetime.to_datetime(order.commitment_date_only)

    def _compute_date_only(self):
        for order in self:
            if order.date_order:
                order.date_only = order.date_order.date()
            else:
                order.date_only = False


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_product_id_check_hold(self):
        if self.product_id:
            today = date.today()
            product_variants = self.product_id.product_variant_ids.ids
            hold_records = self.env['product.hold'].search([('product_id', 'in', product_variants),('hold_to_date', '>=', today),])
            if hold_records:
                messages = []
                for rec in hold_records:
                    msg = _("Customer: %s | Quantity: %s | Hold To Date: %s") % (
                        rec.customer_id.display_name or 'N/A',
                        rec.qty or 'N/A',
                        rec.hold_to_date or 'N/A'
                    )
                    messages.append(msg)

                final_message = _(
                    "The product '%s' has the following hold records:\n\n%s"
                ) % (self.product_id.display_name, "\n".join(messages))

                return {
                    'warning': {
                        'title': _("Product On Hold"),
                        'message': final_message,
                    }
                }