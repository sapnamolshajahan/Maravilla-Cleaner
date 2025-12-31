# -*- encoding: utf-8 -*-
from datetime import datetime, time

from dateutil.relativedelta import relativedelta
from pytz import timezone, UTC

from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends('state', 'order_line.qty_received_manual', 'order_line.qty_received')
    def _fully_received(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state != 'purchase':
                order.fully_received = False
                continue

            if any(
                    not float_is_zero(line.product_qty - line.qty_received, precision_digits=precision)
                    for line in order.order_line.filtered(lambda l: not l.display_type)
            ):
                order.fully_received = False

            else:
                order.fully_received = True

    ###########################################################################
    # Fields
    ###########################################################################
    alternate_shipping_address = fields.Text(string="Alt. Shipping Addr.")
    delivery_notes = fields.Text(string="Delivery Notes", help="Delivery instructions or notes")
    date_planned_line_update = fields.Datetime("Lines Planned date",
                                               help="Use this field to update the planned date on all lines.  "
                                                    "Click the \"Set date\" button after keying this value. ")

    fully_received = fields.Boolean(string='Fully Received', compute='_fully_received', store=True)
    hide_drop_ship_fields = fields.Boolean(related='company_id.hide_drop_ship_fields')
    hide_alt_address_fields = fields.Boolean(related='company_id.hide_alt_address_fields')
    hide_delivery_notes_fields = fields.Boolean(related='company_id.hide_delivery_notes_fields')
    partner_address_id = fields.Many2one(comodel_name='res.partner',
                                         string='Vendor Address',
                                         domain="[('parent_id','=',partner_id)]",
                                         help="This is the supplier's address to use for the purchase order.")
    delivery_address_desc = fields.Text(string="Delivery Address")

    ###########################################################################
    # Model methods
    ###########################################################################

    @api.onchange("partner_id")
    def onchange_purchase_partner(self):
        """
        Populate/Clear purchase.order:incoterm_id
        """

        if self.partner_id:
            company_id = self.env.company.id
            contact_id = self.env["res.partner"].search([("parent_id", "=", self.partner_id.id),
                                                         ("is_company", "=", False),
                                                         ("company_id", "=", company_id),
                                                         ("type", "=", "delivery")],
                                                        limit=1)
            if contact_id:
                delivery_address_desc = ""
                self.partner_address_id = contact_id[0].id

                if contact_id[0].street:
                    delivery_address_desc = contact_id[0].street + ", "

                if contact_id[0].street2:
                    delivery_address_desc = delivery_address_desc + contact_id[0].street2 + ", "

                if contact_id[0].city:
                    delivery_address_desc = delivery_address_desc + contact_id[0].city

                self.delivery_address_desc = delivery_address_desc

            if self.partner_id.purchase_incoterm:
                self.incoterm_id = self.partner_id.purchase_incoterm
            else:
                self.incoterm_id = self.company_id.purchase_incoterm

    def write(self, values):
        res = super(PurchaseOrder, self).write(values)
        if values.get('date_planned'):
            lines = [x.id for x in self.order_line]
            moves = self.env['stock.move'].search([('purchase_line_id', 'in', lines)])
            if moves:
                pickings = list(set([x.picking_id for x in moves if x.picking_id.state != 'cancel']))
                if pickings:
                    for picking in pickings:
                        picking.write({'scheduled_date': values['date_planned'],
                                       'date_deadline': values['date_planned'],
                                       })
        return res

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        if invoice_vals.get('partner_id', None):
            invoice_vals['partner_id'] = self.partner_id.id
        return invoice_vals


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    _order = "date_planned desc, id"

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'qty_received', 'product_uom_qty',
                 'order_id.state')
    def _compute_qty_invoiced(self):
        super(PurchaseOrderLine, self)._compute_qty_invoiced()
        for line in self:
            if line.qty_invoiced >= line.product_qty:
                line.qty_invoiced = line.product_qty
                line.qty_to_invoice = 0.0

    ###########################################################################
    # Fields
    ###########################################################################
    account = fields.Many2one("account.account", "Expense A/C", ondelete="cascade")

    ###########################################################################
    # Model methods
    ###########################################################################

    @api.onchange("product_id")
    def onchange_product_id(self):
        """
        Override to populate expense account. Test for anglo done as try to avoid any dependency issues around enterprise
        """
        result = super(PurchaseOrderLine, self).onchange_product_id()
        self.account = (self.product_id.property_account_expense_id or
                        self.product_id.categ_id.property_account_expense_categ_id)
        return result

    def _prepare_stock_moves(self, picking):
        """
        Force partner_id to picking partner..
        """
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for val in res:
            val.update({"partner_id": picking.partner_id.id})
        return res

    def _convert_to_middle_of_day(self, date):
        """
        Fix purchase/models/purchase.py's version which returns the previous day's time if date is after midday UTC.
        """
        midday = timezone(self.order_id.user_id.tz or self.company_id.partner_id.tz or 'UTC').localize(
            datetime.combine(date, time(12))).astimezone(UTC).replace(tzinfo=None)
        if midday < date:
            return midday + relativedelta(days=1)
        return midday

    def write(self, vals):
        """
        Modify the stock move expected date if the PO expected date has changed.
        """
        res = super(PurchaseOrderLine, self).write(vals)

        date_planned = vals.get("date_planned", "")
        if date_planned:
            exclude_states = ("done", "cancel")
            moves = self.mapped("move_ids").filtered(lambda r: r.state not in exclude_states)
            if moves:
                moves.write({"date_deadline": date_planned, "date": date_planned})

        return res

    def _compute_price_unit_and_date_planned_and_name(self):

        result = super(PurchaseOrderLine, self)._compute_price_unit_and_date_planned_and_name()
        for line in self:
            if line.product_id and line.order_id.partner_id:
                supplierinfo = self.env['product.supplierinfo'].search([
                    ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                    ('partner_id', '=', line.order_id.partner_id.id),
                ], limit=1)
                if not supplierinfo:
                    line.price_unit = 0.0
        return result
