import datetime

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_active = fields.Boolean(company_dependent=True, help='To add loyalty point to the customer', default=True)

    prezzy_card_history = fields.One2many(
        comodel_name='prezzy.redemption',
        inverse_name='partner_id'
    )
    allow_prezzy_redemption = fields.Boolean(compute='_compute_allow_prezzy_redemption')

    def _compute_allow_prezzy_redemption(self):
        for partner in self:
            company = partner.company_id
            if company:
                partner.allow_prezzy_redemption = company.allow_prezzy_redemption
            else:
                partner.allow_prezzy_redemption = False

    def action_issue_prezzy_card(self):
        return {
            'name': 'Prezzy Redemption Wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            "view_type": "form",
            'res_model': 'prezzy.redemption.wizard',
            'target': 'new',
            'view_id': self.env.ref
            ('sale_pos_ecomm_loyalty.action_issue_prezzy_card').id,
            'context': {'active_id': self.id},
        }

    def has_unpaid_invoices_last_month(self):
        today = datetime.date.today()
        first_day_of_this_month = today.replace(day=1)

        on_account_pos_order_ids = self.env['pos.order'].search([
            ('partner_id', 'in', self.ids),
            ('payment_ids.payment_method_id.name', 'in', ['On Account']),
            ('date_order', '>', today - datetime.timedelta(days=100)),
        ])
        invoices = on_account_pos_order_ids.account_move
        domain = [
            ('partner_id', 'in', self.ids),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'not in', ('in_payment', 'paid')),
            ('amount_total', '>', 0),
            ('invoice_date_due', '<', first_day_of_this_month),
        ]
        pos_unpaid_invoices = invoices.filtered_domain(domain)

        if pos_unpaid_invoices:
            return True

        domain = [
            ('partner_id', 'in', self.ids),
            ('sale_orders', '!=', False),
            ('move_type', 'in', ('out_invoice', 'entry')),
            ('payment_state', 'not in', ('in_payment', 'paid')),
            ('amount_total', '>', 0),
            ('invoice_date_due', '<', first_day_of_this_month),
        ]
        sale_order_unpaid_invoices = self.env['account.move'].search(domain, limit=1)
        if sale_order_unpaid_invoices:
            return True

        return False
