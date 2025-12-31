# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

LOCKED_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'done', 'cancel'}
}


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ################################################################################
    # Fields
    ################################################################################
    contact_partner = fields.Many2one("res.partner", string="Contact", help="Person for Interest")
    partner_invoice_id = fields.Many2one(
        comodel_name='res.partner',
        string="Invoice Address",
        compute='_compute_partner_invoice_id',
        store=True, readonly=False, required=True, precompute=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('parent_id', '=', partner_id)]")

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id and self.partner_id.default_sale_order_warehouse_id:
            self.warehouse_id = self.partner_id.default_sale_order_warehouse_id.id


    def action_sale_order_set_invoiced(self):
        if len(self) > 1:
            raise UserError('Only use this function order by order')
        self.write({'invoice_status': 'invoiced'})

    def action_confirm(self):
        for so in self:
            so_lines_sorted = so.order_line.sorted(lambda r: (r.sequence, r.id))
            seq_nr = 10
            for so_line in so_lines_sorted:
                so_line.sequence = seq_nr
                seq_nr += 10

        return super(SaleOrder, self).action_confirm()

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrder, self).create(vals_list)
        for order in res:
            order.action_recalculate_stock()
        return res

    def action_recalculate_stock(self):
        for so in self:
            company = self.env.company
            if company.sale_line_exclude_in_avail_stock:
                warehouse_ids = self.env["stock.warehouse"].search([("exclude_in_avail_stock", "=", False)])
            else:
                warehouse_ids = self.env["stock.warehouse"].search([])

            if warehouse_ids:
                for line in so.order_line:
                    line.stock_available, line.stock_available_all = line.calculate_stock_values(line, warehouse_ids)

    """
    In standard Odoo, the qty_to_invoice is based on the invoicing rule (on order or after delivery) but we want the opportunity
    to create an invoice ignoring the invoicing rule as long as there are invoicable lines
    """

    def _get_invoiceable_lines(self, final=False):
        if not self.env.context.get('advance_invoice', None):
            return super(SaleOrder, self)._get_invoiceable_lines(final=final)
        elif not self.env.company.advance_invoice_rule:
            return super(SaleOrder, self)._get_invoiceable_lines(final=final)
        elif self.state == 'draft':
            raise UserError('You must confirm the SO before invoicing')
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            elif line.product_id.type == 'service' and line.qty_invoiced < line.product_uom_qty:
                invoiceable_line_ids.append(line.id)
                line.write({'qty_to_invoice': line.product_uom_qty - line.qty_invoiced})
            elif line.display_type != 'line_note' and float_is_zero(line.qty_delivered - line.qty_invoiced,
                                                                    precision_digits=precision):
                invoiceable_line_ids.append(line.id)

            elif line.qty_delivered - line.qty_invoiced > 0 or (line.qty_delivered - line.qty_invoiced < 0 and final) or \
                    line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)
                line.write({'qty_to_invoice': line.qty_delivered - line.qty_invoiced})

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)

    def action_set_prices(self):
        for line in self.order_line:
            line.price_changed = True
            line.discount_original = line.discount
            line.price_unit_original = line.price_unit

    # for some reason the status is not consistent, so this will run nightly to clean up
    def calc_invoice_status(self):
        sale_orders = self.env['sale.order'].search(
            [('invoice_status', '!=', 'invoiced'), ('state', 'not in', ('draft', 'cancel'))])
        for order in sale_orders:
            fully_invoiced = True
            for line in order.order_line:
                if line.product_id and line.qty_invoiced < line.product_uom_qty:
                    fully_invoiced = False

            if fully_invoiced:
                order.write({'invoice_status': 'invoiced'})

    def action_sort_lines(self):
        self.ensure_one()

        wizard_model = self.env["sale.order.sort"]
        wizard = wizard_model.create({"sale_order": self.id
                                      })

        for line in self.order_line:
            self.env['sale.order.line.sort'].create({
                'sale_order_sort': wizard.id,
                'sequence': line.sequence,
                'alt_seq': line.sequence,
                'sale_order_line': line.id
            })

        return {
            "name": "Sale Line Sort",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "form",
            "target": "new"
        }

    def action_force_warehouse(self):
        """
        Force the warehouse on sale lines to match the sale warehouse.
        :return:
        """
        for rec in self:
            if rec.state not in ("draft", "sent"):
                raise UserError("Cannot alter non-draft Sale Order")

            for line in rec.order_line:
                line.warehouse_id = rec.warehouse_id
                line.stock_available_all, line.stock_available = line._get_stock_available()
