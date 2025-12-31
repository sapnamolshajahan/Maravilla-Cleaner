from odoo import models, fields, api


class PurchaseOrderFECLine(models.Model):
    _name = 'purchase.order.fec.line'
    _inherit = 'account.forward.exchange.allocation'
    _description = 'Purchase Order FEC Line'

    purchase_order = fields.Many2one("purchase.order", "Purchase Order", required=True, ondelete='cascade')
    purchase_state = fields.Selection(related="purchase_order.state", string="State", readonly=True)
    purchase_total = fields.Monetary("Total Untaxed", related="purchase_order.amount_untaxed", readonly=True,
                                     currency_field='fec_currency')

    def purchase_order_fec_line_created_hook(self, new_records):
        return True

    def purchase_order_fec_line_updated_hook(self, vals):
        return True

    def purchase_order_fec_line_deleted_hook(self):
        return True

    @api.model_create_multi
    def create(self, vals_list):
        records = super(PurchaseOrderFECLine, self).create(vals_list)
        self.purchase_order_fec_line_created_hook(records)
        return records

    def write(self, vals):
        self.purchase_order_fec_line_updated_hook(vals)
        return super(PurchaseOrderFECLine, self).write(vals)

    def unlink(self):
        self.purchase_order_fec_line_deleted_hook()
        return super(PurchaseOrderFECLine, self).unlink()