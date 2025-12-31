from odoo import models, fields
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _compute_override_values_sales(self):
        """ Force calculate values to empty for performance. """
        self.sale_order_count = 0
        if not self.env.company.sale_set_counts_zero:
            all_partners = self.with_context(active_test=False).search_fetch(
                [('id', 'child_of', self.ids)],
                ['parent_id'],
            )
            sale_order_groups = self.env['sale.order']._read_group(
                domain=expression.AND([self._get_sale_order_domain_count(), [('partner_id', 'in', all_partners.ids)]]),
                groupby=['partner_id'], aggregates=['__count']
            )
            self_ids = set(self._ids)

            self.sale_order_count = 0
            for partner, count in sale_order_groups:
                while partner:
                    if partner.id in self_ids:
                        partner.sale_order_count += count
                    partner = partner.parent_id

    default_sale_order_warehouse_id = fields.Many2one(
        "stock.warehouse", "Sale Order Default Warehouse",
        help="If set, this will be used as the Warehouse on new Sale Orders")

    sale_order_count = fields.Integer("# of Sales Order", readonly=True, compute="_compute_override_values_sales")
