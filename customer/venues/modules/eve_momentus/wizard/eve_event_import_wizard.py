from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import base64
import xlrd
from math import ceil
import logging

_logger = logging.getLogger(__name__)


class EveEventImportWizard(models.TransientModel):
    _name = 'eve.event.import'
    _description = 'Import Event Data from Momentus'

    file = fields.Binary(string="Import File", required=True)

    def action_process_file(self):
        """Process XLSX from Momentus and create/update events, stock moves & pickings."""
        if not self.file:
            raise UserError(_("Please upload a Momentus export file."))

        # === Validate uploaded file ===
        file_data = base64.b64decode(self.file)
        if not (file_data.startswith(b'PK') or file_data.startswith(b'\xD0\xCF')):
            raise UserError(_("Invalid file type. Please upload a valid Excel file (.xls or .xlsx)."))

        try:
            wb = xlrd.open_workbook(file_contents=file_data)
            sheet = wb.sheet_by_index(0)
        except Exception as e:
            raise UserError(_("Unable to read Excel file.\n%s") % str(e))

        _logger.info("Momentus Import Started: sheet=%s rows=%s cols=%s",
                     sheet.name, sheet.nrows, sheet.ncols)

        headers = [str(sheet.cell_value(0, col)).strip() for col in range(sheet.ncols)]
        if headers[0] != "Event ID":
            headers = [str(sheet.cell_value(1, col)).strip() for col in range(sheet.ncols)]
            start_row = 2
        else:
            start_row = 1

        required_cols = ['Event ID', 'Event', 'Resource Code', 'Order Units', 'Item Status']
        for col in required_cols:
            if col not in headers:
                raise UserError(_(f"Missing required column '{col}' in Excel file."))

        # === Models ===
        event_model = self.env['eve.event']
        move_model = self.env['stock.move']
        product_model = self.env['product.product']
        location_model = self.env['stock.location']
        picking_model = self.env['stock.picking']

        picking_type = self.env.ref('stock.picking_type_out')

        created_events = 0
        created_moves = 0
        created_pickings = 0
        cancelled_moves = 0
        skipped_lines = 0

        # === To group pickings ===
        picking_map = {}

        for row_idx in range(start_row, sheet.nrows):

            row_data = {headers[i]: sheet.cell_value(row_idx, i) for i in range(sheet.ncols)}

            try:
                momentus_id = int(row_data.get('Event ID') or 0)
                event_name = row_data.get('Event') or "Unnamed Event"
                resource_code = str(row_data.get('Resource Code') or "").strip()
                order_units = float(row_data.get('Order Units') or 0.0)
                item_status = str(row_data.get('Item Status') or "").lower()
                space_code = str(row_data.get('Space Code - Order') or "").strip()
                momentus_wo = int(row_data.get('Order') or 0)

                if not momentus_id or not resource_code:
                    skipped_lines += 1
                    continue

                # === Find or create event ===
                event = event_model.search([('momentus_id', '=', momentus_id)], limit=1)
                if not event:
                    event = event_model.create({
                        'momentus_id': momentus_id,
                        'name': event_name,
                    })
                    created_events += 1
                    _logger.info("Event created: %s", event.name)

                uplift = event.qty_uplift or self.env.company.qty_uplift or 0
                move_qty = ceil(order_units * (1 + uplift / 100))

                # === Find product ===
                product = product_model.search([('momentus_resource_code', '=', resource_code)], limit=1)
                if not product:
                    skipped_lines += 1
                    continue

                # === Destination location ===
                dest_location = location_model.search([('momentus_space_code', '=', space_code)], limit=1)
                if not dest_location:
                    skipped_lines += 1
                    continue

                # === Cancel logic ===
                if "cancel" in item_status:
                    existing_move = move_model.search([
                        ('eve_event', '=', event.id),
                        ('product_id', '=', product.id),
                        ('momentus_wo', '=', momentus_wo)
                    ], limit=1)
                    if existing_move and existing_move.state not in ('done', 'cancel'):
                        existing_move.action_cancel()
                        cancelled_moves += 1
                        _logger.info("Move cancelled: ID %s", existing_move.id)
                    continue

                # === RETURN CATEGORY ===
                return_flag = product.categ_id.return_category or False

                # === PICKING GROUP KEY ===
                picking_key = (event.id, dest_location.id, return_flag)

                if picking_key not in picking_map:
                    picking = picking_model.create({
                        'picking_type_id': picking_type.id,
                        'origin': event.name,
                        'location_id': self.env.ref('stock.stock_location_stock').id,
                        'location_dest_id': dest_location.id,
                    })
                    picking_map[picking_key] = picking
                    created_pickings += 1

                    _logger.info("Picking created: %s | Return=%s", picking.name, return_flag)
                else:
                    picking = picking_map[picking_key]

                # === MOVE CREATE/UPDATE ===
                move = move_model.search([
                    ('eve_event', '=', event.id),
                    ('product_id', '=', product.id),
                    ('momentus_wo', '=', momentus_wo)
                ], limit=1)

                if move:
                    if move.state not in ('done', 'cancel'):
                        move.write({
                            'product_uom_qty': move_qty,
                            'origin': event.name,
                            'picking_id': picking.id
                        })
                        _logger.info("Move updated: %s Qty=%s", move.id, move_qty)
                else:
                    move = move_model.create({
                        'eve_event': event.id,
                        'momentus_wo': momentus_wo,
                        'product_id': product.id,
                        'product_uom_qty': move_qty,
                        'product_uom': product.uom_id.id,
                        'location_id': self.env.ref('stock.stock_location_stock').id,
                        'location_dest_id': dest_location.id,
                        'origin': event.name,
                        'picking_id': picking.id,
                    })
                    created_moves += 1
                    _logger.info("Move created: %s Qty=%s", move.id, move_qty)

            except Exception as e:
                skipped_lines += 1
                _logger.warning("Row %s failed: %s", row_idx, e)

        # === FINAL SUMMARY LOG ===
        _logger.info(
            "Import Summary → Events=%s Pickings=%s Moves=%s Cancelled=%s Skipped=%s",
            created_events, created_pickings, created_moves, cancelled_moves, skipped_lines
        )

        # === UI Notification ===
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Momentus Import Complete"),
                'message': _(
                    f"Events: {created_events}, Moves: {created_moves}, "
                    f"Cancelled: {cancelled_moves}, Skipped: {skipped_lines}"
                ),
                'sticky': False,
                'type': 'success',

                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                    'next': {
                        'type': 'ir.actions.act_window_close',
                        'next': {
                            'type': 'ir.actions.client',
                            'tag': 'reload',
                        },
                    },
                },
            },
        }