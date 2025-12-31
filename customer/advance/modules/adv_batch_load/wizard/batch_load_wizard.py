import base64
import xlrd
from odoo import models, fields, api
from odoo.exceptions import UserError


class AdvBatchLoadWizard(models.TransientModel):
    _name = 'adv.batch.load.wizard'
    _description = 'Batch Excel Import Wizard'

    file = fields.Binary("Upload Excel File", required=True)
    filename = fields.Char("File Name")

    def action_import(self):
        try:
            data = base64.b64decode(self.file)
            book = xlrd.open_workbook(file_contents=data)
        except:
            raise UserError("Invalid file format. Please upload a valid Excel (.xls) file.")
        sheet = book.sheet_by_index(0)
        for row in range(1, sheet.nrows):
            product_name = str(sheet.cell(row, 0).value).strip()
            qty = float(sheet.cell(row, 1).value)
            lot_name = str(sheet.cell(row, 2).value).strip()
            location_name = str(sheet.cell(row, 3).value).strip()

            product = self.env['product.product'].search([
                ('name', '=', product_name)
            ], limit=1)

            if not product:
                product = self.env['product.product'].create({
                    'name': product_name,
                    'type': 'consu',
                    'is_storable': True,
                })

            location = self.env['stock.location'].search([
                ('name', '=', location_name)
            ], limit=1)

            if not location:
                location = self.env['stock.location'].create({
                    'name': location_name,
                    'usage': 'internal',
                    'location_id': self.env.ref('stock.stock_location_stock').id,  # Parent = Stock
                })

            lot = False
            if lot_name:
                lot = self.env['stock.lot'].search([
                    ('name', '=', lot_name),
                    ('product_id', '=', product.id)
                ], limit=1)
                if not lot:
                    lot = self.env['stock.lot'].create({
                        'name': lot_name,
                        'product_id': product.id,
                    })

            quant = self.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('location_id', '=', location.id),
                ('lot_id', '=', lot.id if lot else False),
            ], limit=1)

            if quant:
                quant.inventory_quantity = qty
                quant.action_apply_inventory()
            else:
                new_quant = self.env['stock.quant'].create({
                    'product_id': product.id,
                    'location_id': location.id,
                    'lot_id': lot.id if lot else False,
                    'inventory_quantity': qty,
                })
                new_quant.action_apply_inventory()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
