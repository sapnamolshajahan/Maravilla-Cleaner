# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
from odoo.addons.queue_job.delay import group, chain
from odoo.exceptions import UserError
from odoo.osv import expression
from ..utils.serial_numbers import numeric_decompose, compute_serial_format

_logger = logging.getLogger(__name__)


class Inventory(models.Model):
    _name = "stock.inventory"
    _description = "Inventory"
    _order = "date desc, id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def get_selection_name(self, model, selection_field_name, selected_option):
        for item in model._fields[selection_field_name].selection:
            if item[0] == selected_option:
                return item[1]

    def _allow_cancel(self):
        for r in self:
            allow = True
            for m in r.move_ids:
                if m.state == "done":
                    allow = False
                    break
            r.allow_cancel = allow

    def _compute_bg_task_state(self):
        for rec in self:
            if rec.bg_task_id:
                self.env.cr.execute("SELECT state FROM queue_job WHERE uuid = %s", (rec.bg_task_id,))
                res = self.env.cr.fetchall()
                if res:
                    val = res[0][0]
                    rec.bg_task_state = self.get_selection_name(self.env['queue.job'], 'state', val)
                else:
                    rec.bg_task_state = None

            else:
                rec.bg_task_state = None

    name = fields.Char('Inventory Reference', default="Inventory", required=True)
    date = fields.Datetime('Inventory Date', readonly=True, required=True, default=fields.Datetime.now,
                           help="If the inventory adjustment is not validated, date at which the theoritical quantities have been checked.\n"
                                "If the inventory adjustment is validated, date at which the inventory adjustment has been validated.")
    accounting_date = fields.Date(string='Accounting Date', default=fields.Date.context_today,
                                  help='Both stock moves and accounting moves will use this date')
    line_ids = fields.One2many("stock.inventory.line", "inventory_id", string="Inventories", copy=False, readonly=False)
    move_ids = fields.One2many('stock.move', 'inventory_id', string='Created Moves')
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('queued', 'Queued'),
        ('done', 'Validated')],
                             copy=False, index=True, readonly=True, tracking=True, default='draft')
    company_id = fields.Many2one('res.company', 'Company', readonly=True, index=True, required=True,
                                 default=lambda self: self.env.company)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_ids = fields.Many2many(
        'stock.location', string='Locations',
        readonly=True, check_company=True, required=True)
    product_ids = fields.Many2many(
        'product.product', string='Products',
        domain="[('type', '=', 'consu')]",
        help="Specify Products to focus your inventory on particular Products.")
    category_ids = fields.Many2many('product.category', string='Categories')
    start_empty = fields.Boolean('Empty Inventory', help="Allows to start with an empty inventory.")
    prefill_counted_quantity = fields.Selection(string='Counted Quantities',
                                                help="Allows to start with a pre-filled counted quantity for each lines or "
                                                     "with all counted quantities set to zero.", default='counted',
                                                selection=[('counted', 'Default to stock on hand'),
                                                           ('zero', 'Default to zero')])
    exhausted = fields.Boolean('Include Exhausted Products',
                               help="Include also products with quantity of 0")
    stocktake_datas = fields.One2many("stocktake.data.entry", "inventory", readonly=True)
    coverage = fields.Selection([
        ("products", "By Selected Products"),
        ("warehouses", "By Selected Warehouses"),
    ], string="Coverage", default="products", required=True)
    include_uncounted_items = fields.Boolean("Include Uncounted Items",
                                             help='If set, lines will be added for uncounted items if the SOH is calculated as != 0')
    allow_cancel = fields.Boolean("Allow Adjustment Cancellation", compute="_allow_cancel")
    has_unprocessed_move_lines = fields.Boolean("Has unprocessed Move lines", compute="_compute_unprocessed_moves")
    prepopulate_lines = fields.Boolean(string="Pre-populate Lines", default=False,
                                       help="""If using Stocktake Data Entry process, then uncheck.""")

    bg_task_id = fields.Char(string='Task ID', readonly=True, copy=False)
    bg_task_state = fields.Char(string='Task State', compute='_compute_bg_task_state')
    queued_state = fields.Selection(selection=[('queued', 'Queued for Processing'), ('processed', 'Done')],
                                    string='Queued State', copy=False)
    location_ids_domain = fields.Binary(string="tag domain",
                                        help="Dynamic domain used for the tag that can be set on tax",
                                        compute="_compute_location_ids_domain")

    @api.depends('warehouse_id')
    def _compute_location_ids_domain(self):
        for rec in self:
            existing_domain = [('usage', 'in', ['internal', 'transit'])]
            if rec.warehouse_id:
                warehouse_location_ids = self.env['stock.location'].search(
                    [('location_id', '=', self.warehouse_id.view_location_id.id)]).ids
                new_domain = [('id', 'in', warehouse_location_ids)]
                combined_domain = expression.AND([existing_domain, new_domain])

                rec.location_ids_domain = combined_domain
            else:
                rec.location_ids_domain = existing_domain

    @api.onchange('company_id')
    def _onchange_company_id(self):
        # If the multilocation group is not active, default the location to the one of the main
        # warehouse.
        if not self.env.user.has_groups('stock.group_stock_multi_locations'):
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
            if warehouse:
                self.location_ids = warehouse.lot_stock_id

    @api.onchange('warehouse_id')
    def _onchange_warehouse(self):
        existing_domain = [('usage', 'in', ['internal', 'transit'])]
        if self.warehouse_id:
            # Retrieve the locations associated with the selected warehouse
            warehouse_location_ids = self.env['stock.location'].search(
                [('location_id', '=', self.warehouse_id.view_location_id.id)]).ids

            # Combine the new domain with existing domains
            new_domain = [('id', 'in', warehouse_location_ids)]
            combined_domain = expression.AND([existing_domain, new_domain])
            return {'domain': {'location_ids': new_domain}}
        else:
            # Reset the domain to the existing one if no warehouse is selected
            return {'domain': {'location_ids': existing_domain}}

    def copy(self, default=None):
        raise UserError("Sorry, but duplication is not allowed to be performed on inventory adjustment items")

    def copy_data(self, default=None):
        name = _("%s (copy)") % (self.name)
        default = dict(default or {}, name=name)
        return super(Inventory, self).copy_data(default)

    def unlink(self):
        for inventory in self:
            if (inventory.state not in ('draft', 'cancel')
                    and not self.env.context.get(MODULE_UNINSTALL_FLAG, False)):
                raise UserError(
                    _('You can only delete a draft inventory adjustment. If the inventory adjustment is not done, you can cancel it.'))
        return super(Inventory, self).unlink()

    def calculate_products_quantity(self, location_ids, products):
        result_count = {}

        for product in products:
            for loc_id in location_ids:
                key = (product.id, loc_id.id)
                available = product.with_context(location=loc_id.id).qty_available
                if key in result_count:
                    result_count[key] += available
                else:
                    result_count[key] = available

        return result_count

    def add_include_uncounted_items(self):
        """
        Include uncounted items where theoretical on hand != 0
        """

        def chunk_list(big_list, chunk_size):
            for i in range(0, len(big_list), chunk_size):
                yield big_list[i:i + chunk_size]

        for location in self.location_ids:
            inventory_product_ids = list(
                set([inventory_line.product_id.id for inventory_line in self.line_ids.filtered(
                    lambda x: x.location_id.id == location.id)]))

            if len(inventory_product_ids) == 1:
                inventory_product_ids = "({})".format(inventory_product_ids[0])
            elif inventory_product_ids:
                inventory_product_ids = str(tuple(inventory_product_ids))

            if inventory_product_ids:
                sql_select = """
                select distinct product_id from stock_move 
                where (location_id = {location} or location_dest_id = {location} ) 
                and product_id not in {products} and state = 'done' """.format(
                    location=location.id,
                    products=inventory_product_ids)
            else:
                sql_select = """
                select distinct product_id from stock_move 
                where (location_id = {location} or location_dest_id = {location}) 
                and state = 'done' """.format(location=location.id)

            self.env.cr.execute(sql_select)
            if self.env.cr.rowcount:
                all_location_product_ids = list(set([tup[0] for tup in self.env.cr.fetchall()]))
            else:
                all_location_product_ids = []

            prod_ids_to_create_new_inventory_lines_for = list(
                set(all_location_product_ids) - set(inventory_product_ids))

            if len(prod_ids_to_create_new_inventory_lines_for) > 0:
                for chunk in chunk_list(prod_ids_to_create_new_inventory_lines_for, 250):
                    products_to_create_lines = self.env["product.product"].browse(chunk)

                    for product in products_to_create_lines:
                        self.create_inventory_line(product, location)
                        self.env.cr.commit()

                    products_to_create_lines.invalidate_recordset()

    def create_inventory_line(self, product, location):
        if product.type != 'consu' and product.is_storable == True:
            return

        if product.bom_ids and product.bom_ids[0].type == 'phantom':
            return

        from_stock_moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
            ('state', '=', 'done')])

        from_qty = sum([x.product_uom_qty for x in from_stock_moves])

        to_stock_moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('location_dest_id', '=', location.id),
            ('state', '=', 'done')])

        to_qty = sum([x.product_uom_qty for x in to_stock_moves])
        theoretical_qty = to_qty - from_qty

        if theoretical_qty:
            product_line = {
                "product_id": product.id,
                "inventory_id": self.id,
                "location_id": location.id,
                "product_uom_id": product.product_tmpl_id.uom_id.id,
                "product_qty": 0.0,
                "theoretical_qty": theoretical_qty
            }
            return self.env["stock.inventory.line"].create(product_line)

    def post_inventory(self):
        """
        Commits per line.
        """
        ctx = self.env.context.copy()
        ctx['force_period_date'] = self.accounting_date
        self.env.context = ctx.copy()
        move_ids = self.move_ids.filtered(lambda x: x.state != 'done').ids
        move_model = self.env["stock.move"]
        for move_id in move_ids:
            move = move_model.browse(move_id)
            move.move_line_ids._compute_quantity_product_uom()
            move.move_line_ids.write({'picked': True})
            move._action_assign()
            move._action_done()
            move.write({'state': 'done', 'date': fields.Datetime.now()})
            move.move_line_ids.write({'state': 'done'})
            stocktake_line = self.env['stock.inventory.line'].search([('inventory_id', '=', self.id),
                                                                      ('stock_moves', 'in', move.id)])
            stocktake_line.write({"moves_done": True})
            self.env.cr.commit()
            _logger.debug("Stocktake: Committed {}".format(move))

    def check_ok_to_proceed(self):
        if not self.accounting_date:
            e = 'Please set an accounting date before validating'
            self.message_post(body=e)
            raise UserError(e)
        if not self.env.user.has_groups('stock.group_stock_manager'):
            e = "Only a stock manager can validate an inventory adjustment."
            self.message_post(body=e)
            raise UserError(e)
        if self.state not in ('confirm', 'queued'):
            e = """You can't validate the inventory {name},
            maybe this inventory has been already validated or isn't ready.""".format(name=self.name)
            self.message_post(body=e)
            raise UserError(e)

        self.check_if_inprogress_counts()
        if self.state == "done":
            e = "Stock Inventory {name} has already been processed.".format(name=self.name)
            self.message_post(body=e)
            raise UserError(e)
        return

    def action_validate_background(self):
        if self.state == 'queued':
            raise UserError("Submitted to Queue for processing")
        self.state = 'queued'
        task = self.with_delay(channel=self.light_job_channel(),
                               description="Stocktake Background Confirm Main({})".format(
                                   self.name)).action_create_child_queue(
            stocktake_id=self.id,
            uid=self.env.user.id,
        )
        self.bg_task_id = task.uuid
        self.message_post(body="Queued for Stocktake Confirm")

    def action_create_child_queue(self, stocktake_id, uid):

        stock_inventory_model = self.env['stock.inventory']
        stocktake = stock_inventory_model.with_user(uid).browse(int(stocktake_id))

        job_list = []
        # Queue tasks for each line and store task reference
        for line in stocktake.line_ids.filtered(lambda x: not x.moves_done):
            job_list.append(stocktake.delayable(channel=self.light_job_channel(),
                                                description="Stocktake Background Confirm ({}) - Line {}".format(
                                                    self.name,
                                                    line.product_id.display_name)
                                                )._run_validate_line(
                stocktake_id=stocktake.id,
                line_id=line.id,
                uid=stocktake.env.user.id
            ))
        final_job = stocktake.delayable(
            channel=self.light_job_channel(),
            description=f"Confirm stock take"
        ).confirm_stock_take(stocktake_id=stocktake.id, uid=stocktake.env.user.id)
        chain(group(*job_list), final_job).delay()
        self.message_post(body="Queued tasks for lines.")

    def action_post_move(self, line):
        moves = line.stock_moves.filtered(lambda x: x.state != 'done')
        if moves:
            ctx = self.env.context.copy()
            ctx['force_period_date'] = self.accounting_date
            self.env.context = ctx.copy()
            for move in moves:
                move._action_confirm()
                move.move_line_ids._compute_quantity_product_uom()
                move.move_line_ids.write({'picked': True})
                move._action_done()
                move.write({'state': 'done', 'date': fields.Datetime.now()})
                move.move_line_ids.write({'state': 'done'})
                line.write({"moves_done": True})
                self.env.cr.commit()
                _logger.debug("Stocktake: Committed {}".format(move))

    def _run_validate_line(self, stocktake_id, line_id, uid):
        stocktake = self.with_user(uid).browse(int(stocktake_id))
        line = stocktake.line_ids.browse(int(line_id))

        # Ensure the stocktake is still in queued state
        if stocktake.state == 'queued':
            try:
                # Validate and process the specific line
                stocktake.action_validate_line(stocktake, line)
                stocktake.action_post_move(line)
            except Exception as e:
                stocktake.write({'state': 'confirm'})
                stocktake.message_post(body="Error processing line: {}".format(e))
                return False

        # Check if all tasks are done
        return True

    def action_validate_line(self, stocktake, line):

        if not stocktake.exists():
            return

        self.ensure_one()
        stocktake.check_ok_to_proceed()
        if (not stocktake.line_ids.filtered(lambda x: x.moves_done)) and stocktake.include_uncounted_items:
            stocktake.add_include_uncounted_items()

        count = len(stocktake.line_ids.filtered(lambda x: not x.moves_done))
        # for line in stocktake.line_ids.filtered(lambda x: not x.moves_done):
        unlink = None
        if line.product_id.bom_ids and line.product_id.bom_ids[0].type == 'phantom':
            unlink = line.sudo().unlink()


        elif line.product_id.type != 'consu' and line.product_id.is_storable != True:
            unlink = line.unlink()

        negative = next((line for line in self.mapped("line_ids")
                         if line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            e = """You cannot set a negative product quantity in an inventory line:
                            {name} - qty: {qty}""".format(name=negative.product_id.name, qty=negative.product_qty)
            self.message_post(body=e)
            raise UserError(e)
        self.env.clear()
        if not line.stock_moves and not unlink:
            line._generate_moves()
        return True

    def confirm_stock_take(self, stocktake_id, uid):
        stock_inventory_model = self.env['stock.inventory']
        stocktake = stock_inventory_model.with_user(uid).browse(int(stocktake_id))
        if stocktake:
            stocktake.post_inventory()
            stocktake.write({"state": "done", 'date': fields.Datetime.now()})

    def action_validate(self):
        """
               Finalise Stock Counts.

               * override (and ignore) base code.
               * handle possible race conditions between task and user.
               * When including "uncounted" items at an internal location, missing items are added with a quantity of zero.
               """

        if not self.exists():
            return

        ctx = self.env.context.copy()
        ctx["stock_inventory__validation"] = True
        self.env.context = ctx
        self.ensure_one()
        self.check_ok_to_proceed()
        if (not self.line_ids.filtered(lambda x: x.moves_done)) and self.include_uncounted_items:
            self.add_include_uncounted_items()

        count = len(self.line_ids.filtered(lambda x: not x.moves_done))
        row = 1
        for line in self.line_ids.filtered(lambda x: not x.moves_done):
            unlink = None
            if line.product_id.bom_ids and line.product_id.bom_ids[0].type == 'phantom':
                unlink = line.sudo().unlink()

            elif line.product_id.type != 'consu' and line.product_id.is_storable != True:
                unlink = line.unlink()

            negative = next((line for line in self.mapped("line_ids")
                             if line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
            if negative:
                e = """You cannot set a negative product quantity in an inventory line:
                                {name} - qty: {qty}""".format(name=negative.product_id.name, qty=negative.product_qty)
                self.message_post(body=e)
                raise UserError(e)
            self.env.clear()
            if not line.stock_moves and not unlink:
                line._generate_moves()
            _logger.info('Row {row} of {count} done'.format(row=row, count=count))
            row += 1

        self.post_inventory()
        # collect unprocessed move lines (state != done)
        unprocessed_move_lines = self.env['stock.move.line'].search(
            [('move_id', 'in', self.move_ids.ids), ('state', 'not in', ['cancel', 'done'])])
        if not unprocessed_move_lines:
            self.write({"state": "done", 'date': fields.Datetime.now()})
        return True

    def _compute_unprocessed_moves(self):
        for record in self:
            unprocessed_move_lines = self.env['stock.move.line'].search(
                [('move_id', 'in', record.move_ids.ids), ('state', 'not in', ['cancel', 'done'])])
            if unprocessed_move_lines:
                record.has_unprocessed_move_lines = True
            else:
                record.has_unprocessed_move_lines = False

    def action_validate_unprocessed_lines(self):
        '''
        this function is to handle the unprocessed stock move lines after validating the stocktake
        '''
        unprocessed_moves = self.env['stock.move'].search(
            [('id', 'in', self.move_ids.ids), ('state', 'not in', ['cancel', 'done'])])
        for move in unprocessed_moves:
            move.move_line_ids._compute_quantity_product_uom()
            move.move_line_ids.write({'picked': True})
            move.write({'state': 'done', 'date': fields.Datetime.now()})
            move.move_line_ids.write({'state': 'done'})
        self.write({"state": "done", 'date': fields.Datetime.now()})
        return True

    def check_if_inprogress_counts(self):
        """
        Raise an exception if we have stock data entry records not imported.
        """
        if len([x for x in self.stocktake_datas if x.state != "done"]) > 0:
            raise UserError(
                "Stock Inventory {name} cannot be processed as there are undone Stocktake Data Entry records. "
                "Please import or delete these.".format(name=self.name))

    def action_view_related_count_lines(self):
        self.ensure_one()
        domain = [('inventory_id', '=', self.id)]
        action = {
            'name': ('Counts'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.inventory.line',
            'view_type': 'list',
            'view_mode': 'list',
            'domain': domain,
        }
        return action

    def action_cancel_draft(self):
        if not self.allow_cancel:
            raise UserError("Can't cancel partially confirmed Inventory Adjustment")
        self.mapped('move_ids')._action_cancel()
        self.line_ids.unlink()
        self.write({'state': 'draft'})

    def action_start(self):
        self.ensure_one()
        if self.category_ids:
            for category in self.category_ids:
                products = self.env['product.product'].search([('categ_id', '=', category.id)])
                for product in products:
                    self.write({'product_ids': [(4, product.id)]})
        if self.prepopulate_lines:
            self._action_start()

        self.write(
            {
                "state": "confirm",
                "date": fields.Datetime.now()
            })
        self._check_company()
        return self.action_open_inventory_lines()

    def _action_start(self):
        """ Confirms the Inventory Adjustment and generates its inventory lines
        if its state is draft and don't have already inventory lines (can happen
        with demo data or tests).
        """
        for inventory in self:
            if inventory.state != 'draft':
                continue
            vals = {
                'state': 'confirm',
                'date': fields.Datetime.now()
            }
            if not inventory.line_ids and not inventory.start_empty:
                self.env['stock.inventory.line'].create(inventory._get_inventory_lines_values())
            inventory.write(vals)

    def action_open_inventory_lines(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'name': _('Inventory Lines'),
            'res_model': 'stock.inventory.line',
        }
        context = {
            'default_is_editable': True,
            'default_inventory_id': self.id,
            'default_company_id': self.company_id.id,
        }
        # Define domains and context
        domain = [
            ('inventory_id', '=', self.id),
            ('location_id.usage', 'in', ['internal', 'transit'])
        ]
        if self.location_ids:
            context['default_location_id'] = self.location_ids[0].id
            if len(self.location_ids) == 1:
                if not self.location_ids[0].child_ids:
                    context['readonly_location_id'] = True

        if self.product_ids:
            # no_create on product_id field
            action['view_id'] = self.env.ref('operations_stocktake.stock_inventory_line_list').id
            if len(self.product_ids) == 1:
                context['default_product_id'] = self.product_ids[0].id
        else:
            # no product_ids => we're allowed to create new products in list
            action['view_id'] = self.env.ref('operations_stocktake.stock_inventory_line_list').id

        action['context'] = context
        action['domain'] = domain
        return action

    def action_view_related_move_lines(self):
        self.ensure_one()
        domain = [('move_id', 'in', self.move_ids.ids)]
        action = {
            'name': _('Product Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_type': 'list',
            'view_mode': 'list,form',
            'domain': domain,
        }
        return action

    def action_print(self):
        return self.env.ref('stock.action_report_inventory').report_action(self)

    def _get_quantities(self):
        """Return quantities group by product_id, location_id, lot_id, package_id and owner_id

        :return: a dict with keys as tuple of group by and quantity as value
        :rtype: dict
        """
        self.ensure_one()
        if self.location_ids:
            domain_loc = [('id', 'child_of', self.location_ids.ids)]
        elif self.warehouse_id:
            domain_loc = [('warehouse_id', '=', self.warehouse_id.id), ('usage', 'in', ['internal', 'transit'])]
        else:
            domain_loc = [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]
        locations_ids = [l['id'] for l in self.env['stock.location'].search_read(domain_loc, ['id'])]
        domain = [('company_id', '=', self.company_id.id),
                  ('quantity', '!=', '0'),
                  ('location_id', 'in', locations_ids)]
        if self.prefill_counted_quantity == 'zero':
            domain.append(('product_id.active', '=', True))

        if self.product_ids:
            domain = expression.AND([domain, [('product_id', 'in', self.product_ids.ids)]])

        fields = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'quantity:sum']
        group_by = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id']

        quants = self.env['stock.quant'].read_group(domain, fields, group_by, lazy=False)
        return {(
                    quant['product_id'] and quant['product_id'][0] or False,
                    quant['location_id'] and quant['location_id'][0] or False,
                    quant['lot_id'] and quant['lot_id'][0] or False,
                    quant['package_id'] and quant['package_id'][0] or False,
                    quant['owner_id'] and quant['owner_id'][0] or False):
                    quant['quantity'] for quant in quants
                }

    def _get_exhausted_inventory_lines_vals(self, non_exhausted_set):
        """Return the values of the inventory lines to create if the user
        wants to include exhausted products. Exhausted products are products
        without quantities or quantity equal to 0.

        :param non_exhausted_set: set of tuple (product_id, location_id) of non exhausted product-location
        :return: a list containing the `stock.inventory.line` values to create
        :rtype: list
        """
        self.ensure_one()
        if self.product_ids:
            product_ids = self.product_ids.ids
        else:
            product_ids = self.env['product.product'].search_read([
                '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False),
                ('type', '=', 'consu'),
                ('active', '=', True)], ['id'])
            product_ids = [p['id'] for p in product_ids]

        if self.location_ids:
            location_ids = self.location_ids.ids
        elif self.warehouse_id:
            location_ids = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id), ('id', '=', self.warehouse_id.id)]).lot_stock_id.ids
        else:
            location_ids = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)]).lot_stock_id.ids

        vals = []
        for product_id in product_ids:
            for location_id in location_ids:
                if ((product_id, location_id) not in non_exhausted_set):
                    vals.append({
                        'inventory_id': self.id,
                        'product_id': product_id,
                        'location_id': location_id,
                        'theoretical_qty': 0
                    })
        return vals

    def _get_inventory_lines_values(self):
        """Return the values of the inventory lines to create for this inventory.

        :return: a list containing the `stock.inventory.line` values to create
        :rtype: list
        """
        self.ensure_one()
        quants_groups = self._get_quantities()
        vals = []
        for (product_id, location_id, lot_id, package_id, owner_id), quantity in quants_groups.items():
            line_values = {'inventory_id': self.id,
                           'product_qty': 0 if self.prefill_counted_quantity == "zero" else quantity,
                           'theoretical_qty': quantity, 'prod_lot_id': lot_id, 'partner_id': owner_id,
                           'product_id': product_id,
                           'location_id': location_id, 'package_id': package_id,
                           'product_uom_id': self.env['product.product'].browse(product_id).uom_id.id}
            vals.append(line_values)
        if self.exhausted:
            vals += self._get_exhausted_inventory_lines_vals({(l['product_id'], l['location_id']) for l in vals})
        return vals

    def action_import_stock_counts(self):
        """
        Button-box "Import Stock Counts" on stock.inventory form.

        This clears out existing lines and re-does everything all over again.
        """
        for r in self:

            if not r.stocktake_datas:
                _logger.debug("No stocktake.data.entry, ignore")
                continue

            # Clear out existing line data
            r.line_ids.unlink()

            r.import_serial_data_entries()
            r.import_non_serial_data_entries()

            r.stocktake_datas.write({"state": "done"})

            if r.include_uncounted_items:
                r.add_include_uncounted_items()

    def import_non_serial_data_entries(self):
        """
        Sum quantities on all stock.data.entry.lines into groups for non-serialised products
        Ignore lines with 99999 as quantity as these are not counted lines
        """
        line_model = self.env["stock.inventory.line"]
        product_model = self.env["product.product"]

        self.env.cr.execute(
            "select product_id, location, sum(quantity) "
            "from stocktake_data_entry, stocktake_data_entry_line "
            "where inventory = {0} "
            "and production_lot_id is null "
            "and stocktake_data_entry_line.quantity != 99999 "
            "and stocktake_data_entry_line.stocktake_id = stocktake_data_entry.id "
            "group by product_id, location".format(self.id))

        # TODO - instead of errors which will mean potentially running many times, display a log of issues at end and deal with in inventory
        for product_id, location_id, quantity in self.env.cr.fetchall():
            product = product_model.browse(product_id)
            # if quantity and quantity < 0.0:
            #     raise UserError('You cannot import a negative quantity - see product {sheet}'.format(sheet=product.name))
            # if product.tracking != 'none':
            #     raise UserError(' Product {product} requires tracking but no serial numbers completed'.format(product=product.name))
            if product.type != 'consu' and product.is_storable != True:
                continue
            if quantity:
                self.env.cr.execute(
                    ("select sum(product_uom_qty) from stock_move "
                     "where product_id = %s and location_id = %s and state = 'done'"),
                    (product.id, location_id))
                from_qty = self.env.cr.fetchone()[0] or 0

                self.env.cr.execute(
                    ("select sum(product_uom_qty) from stock_move "
                     "where product_id = %s and location_dest_id = %s and state = 'done'"),
                    (product.id, location_id))
                to_qty = self.env.cr.fetchone()[0] or 0

                theoretical_qty = to_qty - from_qty
                line_model.create(
                    {
                        "product_id": product.id,
                        "inventory_id": self.id,
                        "location_id": location_id,
                        "product_qty": quantity,
                        "product_uom_id": product.uom_id.id,
                        "theoretical_qty": theoretical_qty
                    })

    def import_serial_data_entries(self):
        """
        Convert stocktake.data.entry.line containing serialised items.
        """
        data_line_model = self.env["stocktake.data.entry.line"]
        line_model = self.env["stock.inventory.line"]

        self.env.cr.execute(
            "select stocktake_data_entry_line.id "
            "from stocktake_data_entry, stocktake_data_entry_line "
            "where inventory = {0} "
            "and production_lot_id is not null "
            "and stocktake_data_entry_line.stocktake_id = stocktake_data_entry.id ".format(self.id))

        done = []
        for row in self.env.cr.fetchall():
            # TODO could have the same lot at multiple locations - this only works for serialised products
            data = data_line_model.browse(row[0])
            if data.quantity:
                if data.quantity < 0.0:
                    raise UserError('You cannot import a negative quantity - see sheet {sheet}'.format(
                        sheet=data.stocktake_id.name))
                for production_lot in self.enumerate_production_lots(data.production_lot_id, data.quantity):
                    # TODO - instead of errors which will mean potentially running many times, display a log of issues at end and deal with in inventory
                    # if production_lot in done:
                    #     raise UserError("Duplicated production lot '{lot}' in import - see {page}".format(lot=production_lot.name,
                    #                                                                                       page=data.name))
                    done.append(production_lot)
                    from_stock_moves = self.env['stock.move.line'].search([('product_id', '=', data.product_id.id),
                                                                           ('location_id', 'in', [x.id for x in
                                                                                                  data.stocktake_id.inventory_locations]),
                                                                           ('lot_id', '=', production_lot.id),
                                                                           ('state', '=', 'done')])
                    from_qty = sum([x.quantity for x in from_stock_moves])
                    to_stock_moves = self.env['stock.move.line'].search([('product_id', '=', data.product_id.id),
                                                                         ('location_dest_id', 'in', [x.id for x in
                                                                                                     data.stocktake_id.inventory_locations]),
                                                                         ('lot_id', '=', production_lot.id),
                                                                         ('state', '=', 'done')])

                    to_qty = sum([x.quantity for x in to_stock_moves])
                    theoretical_qty = to_qty - from_qty

                    # one row per serial item
                    line_model.create(
                        {
                            "product_id": data.product_id.id,
                            "product_uom_id": data.product_id.uom_id.id,
                            "inventory_id": self.id,
                            "location_id": data.stocktake_id.location.id,
                            "product_qty": theoretical_qty,
                            "prod_lot_id": production_lot.id,
                        })

    def enumerate_production_lots(self, base_production, count):
        lot_model = self.env["stock.lot"]
        result = [base_production]
        segments = numeric_decompose(base_production.name)
        if segments:
            base_number = segments[len(segments) - 1]
            serial_number_format = compute_serial_format(base_production.name)
            for n in range(base_number + 1, base_number + int(count)):
                serial = serial_number_format.format(n)
                lot = lot_model.search(
                    [
                        ("product_id", "=", base_production.product_id.id),
                        ("name", "=", serial),
                    ])
                if not lot:
                    raise UserError(
                        "Expected Lot {} not found for '{}'".format(serial, base_production.product_id.name))
                result.append(lot)

        return result

    def button_import_count(self):
        wizard = self.env["stocktake.import.count"].create({"stocktake": self.id})

        return {
            "name": wizard._description,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "target": "new",
        }


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    @api.depends('code')
    def _compute_use_existing_lots(self):
        res = super(PickingType, self)._compute_use_existing_lots()
        for picking_type in self:
            if picking_type.code == 'outgoing':
                picking_type.use_existing_lots = True
            else:
                picking_type.use_existing_lots = False
        return res

    @api.depends('code')
    def _compute_use_create_lots(self):
        res = super(PickingType, self)._compute_use_create_lots()
        for picking_type in self:
            if picking_type.code == 'incoming':
                picking_type.use_create_lots = True
            else:
                picking_type.use_create_lots = False
        return res
