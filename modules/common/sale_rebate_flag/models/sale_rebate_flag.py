from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_eligible_for_rebates = fields.Boolean(string="Eligible for Rebates", help="Indicates whether the Customer is eligible for rebates or not.")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_rebate = fields.Boolean(string="Rebate", help="Indicates whether the Customer has a Rebate or not.")

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.has_rebate = self.partner_id.is_eligible_for_rebates

        return
