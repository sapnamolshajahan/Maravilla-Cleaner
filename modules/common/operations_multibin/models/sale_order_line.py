from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    """
    Some modules prevent pickings to be be auto confirmed / assigned so this will cater for all scenarios except
    internal transfers. See action_assign fo catering for internal transfers
    """

    # TODO Deprecated function inherited
    # def _action_launch_procurement_rule(self):
    #     res = super(SaleOrderLine, self)._action_launch_procurement_rule()
    #     orders = list(set(x.order_id for x in self))
    #     for order in orders:
    #         pickings = order.picking_ids.filtered(lambda x: x.state in ['waiting', 'assigned', 'confirmed'])
    #         if pickings:
    #             pickings.sequence_moves()
    #     return res
