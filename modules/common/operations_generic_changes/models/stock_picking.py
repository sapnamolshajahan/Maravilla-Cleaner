# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = "id desc"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    def count_invoices(self):
        for r in self:
            r.invoice_count = 1 if r.invoice_id else 0

    @api.depends('sale_id')
    def _set_source_partner(self):
        for data in self:
            if data.sale_id:
                data.source_partner_id = data.sale_id.partner_id.id
            else:
                data.source_partner_id = False

    ###########################################################################
    # Fields
    ###########################################################################
    customer_return_reference = fields.Char(string="Customer Return Reference", size=64)
    sale_warehouse_id = fields.Many2one(related="sale_id.warehouse_id",
                                        comodel_name="stock.warehouse", string="Warehouse (Sale)", readonly=True)
    invoice_id = fields.Many2one("account.move", string="Invoice", copy=False)
    invoice_count = fields.Integer("Invoices", compute="count_invoices")
    source_partner_id = fields.Many2one("res.partner", string="Source Partner",
                                        compute="_set_source_partner", store=True)

    ###########################################################################
    # Model methods
    # ###########################################################################

    @api.onchange("picking_type_id")
    def onchange_picking_type(self):
        if not self.location_id:
            self.location_id = self.picking_type_id.default_location_src_id
        if not self.location_dest_id:
            self.location_dest_id = self.picking_type_id.default_location_dest_id

        if self.picking_type_id.code == "internal":
            return {
                "domain":
                    {
                        "location_id": [("usage", "=", "internal")],
                        "location_dest_id": [("usage", "=", "internal")],
                    }
            }

        return {}

    def write(self, vals):
        """
        Handle write processing.
        :return:  If the picking_type_id has changed, push to the stock move source location.
        """
        update_moves = False
        if ("picking_type_id" in vals and
                self.picking_type_id.code == "outgoing"):
            update_moves = True
        res = super(StockPicking, self).write(vals)

        if update_moves:
            self.move_ids.write({"location_id": self.picking_type_id.default_location_src_id.id})

        return res

    @api.model
    def default_get(self, fields_list):
        res = super(StockPicking, self).default_get(fields_list)

        if self.env.context.get('default_picking_type_code', False):
            res['picking_type_code'] = self.env.context['default_picking_type_code']

        else:
            res['picking_type_code'] = 'internal'

        if 'product_moves_out' in res:
            product_moves_out = res['product_moves_out']
            res['product_moves_out'] = self.sort_product_moves_according_to_product_code(res, product_moves_out)

        if 'product_moves_in' in res:
            product_moves_in = res['product_moves_in']
            res['product_moves_in'] = self.sort_product_moves_according_to_product_code(res, product_moves_in)

        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(StockPicking, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu
        )
        if view_type == 'form':
            if 'Delivery_Orders' in self.env.context and 'customer_return_reference' in result['fields']:
                result['fields']['customer_return_reference']['string'] = "Customer Return Reference"

            elif 'Incoming_Shipments' in self.env.context and 'customer_return_reference' in result['fields']:
                result['fields']['customer_return_reference']['string'] = "Supplier Return Reference"
        return result

    def sort_product_moves_according_to_product_code(self, res, product_moves):
        products = {}
        products_with_no_code_set = []
        sorted_product_moves = []
        product_ids = []
        product_ids_and_moves = {}

        for product_move in product_moves:
            product_id = product_move['product_id']
            product_ids.append(product_id)

            if product_id in product_ids_and_moves:
                product_ids_and_moves[product_id].append(product_move)
            else:
                product_ids_and_moves[product_id] = []
                product_ids_and_moves[product_id].append(product_move)

        product_records = list(set(self.env["product.product"].browse(product_ids)))
        for product_rec in product_records:

            if product_rec.code:
                if product_rec.code in products:
                    products[product_rec.code].extend(product_ids_and_moves[product_rec.id])
                else:
                    products[product_rec.code] = []
                    products[product_rec.code].extend(product_ids_and_moves[product_rec.id])
            else:
                products_with_no_code_set.extend(product_ids_and_moves[product_rec.id])

        product_code_set = set([p.code for p in product_records if p.code])
        product_codes_list = list(product_code_set)
        product_codes_list.sort()

        for product_code in product_codes_list:
            sorted_product_moves.extend(products[product_code])
        sorted_product_moves.extend(products_with_no_code_set)

        return sorted_product_moves

    @api.model
    def more_action_cancel(self):
        super(StockPicking, self).action_cancel()
        return {}

    def action_view_sale_orders(self):
        return super(StockPicking, self).action_view_sale_orders()

    def action_view_invoice(self):

        # The names of the actions and views are pulled out from
        # sale/models/sale.py action_view_invoice()
        action = self.env.ref("account.action_move_in_invoice_type")
        return {
            "name": action.name,
            "help": action.help,
            "views": [(self.env.ref("account.view_move_form").id, "form")],
            "type": action.type,
            "view_mode": "form",
            "target": action.target,
            "context": action.context,
            "res_model": action.res_model,
            "res_id": self.invoice_id.id,
            "domain": action.domain
        }

    def button_validate(self):
        if self.picking_type_id.code != 'internal':
            if not self.partner_id:
                raise UserError("Partner required for delivery orders and incoming shipments")

        return super(StockPicking, self).button_validate()

    def button_create_blank_return(self):
        self.ensure_one()

        vals = {'picking_id': self.id,
                'is_parts_return': True
                }

        wiz = self.env['stock.return.picking'].create(vals)
        ctx = dict(self.env.context)
        return {
            'name': 'Reverse Transfer - Parts',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': wiz._name,
            'res_id': wiz.id,
            'target': 'new',
            'context': ctx
        }
