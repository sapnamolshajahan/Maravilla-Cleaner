from odoo import _, api, fields, models
from odoo.exceptions import UserError

class PrezzyRedemptionWizard(models.TransientModel):
    _name = "prezzy.redemption.wizard"

    partner_id = fields.Many2one('res.partner', string="Contact", default=lambda s: s._get_partner_id())
    current_point_total = fields.Integer("Current Loyalty Points", default=lambda s: s._get_current_points())
    amount_to_redeem = fields.Integer("Amount to redeem", default=2000)
    card_value_to_issue = fields.Float("Card Value to be Issued", default=200.0)
    notes = fields.Char("Additional Notes")

    def _get_partner_id(self):
        return self.env.context.get("active_id")

    def _get_current_points(self):
        partner_id = self.env.context.get("active_id")
        partner = self.env['res.partner'].search([('id', '=', partner_id)])
        return partner.loyalty_pts

    def redeem_card(self):
        if self.amount_to_redeem > self.current_point_total:
            raise UserError("Redemption amount cannot exceed current points.")
        if self.amount_to_redeem <= 0:
            raise UserError("Please enter a valid amount.")
        if self.amount_to_redeem > 2000:
            raise UserError("Only 2000 points are required for redemption.")

        loyalty_setting = self.env['all.loyalty.setting'].search(
            [('active', '=', True), ('issue_date', '<=', fields.Date.today()),
             ('expiry_date', '>=', fields.Date.today())])

        # Active loyalty setting is required in order to create history
        if loyalty_setting:
            self.env['prezzy.redemption'].sudo().create({
                'deduction_date': fields.Date.today(),
                'partner_id': self.partner_id.id,
                'deduction_amount': self.amount_to_redeem,
                'card_value': self.card_value_to_issue,
                'notes': self.notes
            })

            self.env['all.loyalty.history'].sudo().create({
                'partner_id': self.partner_id.id,
                'loyalty_config_id': loyalty_setting.id,
                'date': fields.Date.today(),
                'transaction_type': 'debit',
                'generated_from': 'prezzy',
                'points': self.amount_to_redeem,
                'state': 'done',
            })
