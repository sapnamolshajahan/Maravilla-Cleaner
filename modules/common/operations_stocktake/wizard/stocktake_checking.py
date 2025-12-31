# -*- coding: utf-8 -*-
import base64
from io import BytesIO

import xlsxwriter

from odoo import fields, models, api


class StocktakeCheckingReport(models.TransientModel):
    """
    Reports on stocktake Checking
    """
    _name = "stocktake.checking.report"
    _description = 'Stocktake Checking Report'

    stocktake_id = fields.Many2one("stock.inventory", string="Stocktake")
    report_name = fields.Char(string="Report Name", readonly=True, default="Stocktake Checking Report.xlsx")
    data = fields.Binary("Download File", readonly=True)

    @api.model
    def _get_truncated_note(self, note, length=30):
        if note and (len(note) > length):
            return note[:length] + "..."
        return note

    @api.model
    def _get_all_locations(self, inventory_line_ids):
        location_list = []
        for inventory_line in inventory_line_ids:
            location_list.append(inventory_line.location_id.id)
        location_list = list(set(location_list))
        return location_list

    def button_process(self):
        """ Create the report.
        """
        wizard_item = self[0]
        data = BytesIO()
        stock_inventory = wizard_item.stocktake_id

        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('Data')

        # write report header
        worksheet.write(0, 0, 'Stocktake Report')

        # write headings
        worksheet.write(2, 0, 'Code')
        worksheet.write(2, 1, 'Description')
        worksheet.write(2, 2, 'Counter')
        worksheet.write(2, 3, 'Notes')
        worksheet.write(2, 4, 'Quantity')
        worksheet.write(2, 5, 'Theoretical Stock')
        worksheet.write(2, 6, 'Var Units')
        worksheet.write(2, 7, 'Var $')
        row = 3

        stocktake_product_list = {}
        participating_stock_inventory_products = []
        participating_location_id = []
        location_name = False

        data_ids = stock_inventory.stocktake_datas
        for data_id in data_ids:
            for line in data_id.products:

                location_name = line.stocktake_id.location.name
                product = line.product_id
                if product.id not in stocktake_product_list.keys():
                    product_id = product.id
                    rs = {
                        'product_id': product_id,
                        'location_lines': [],
                        'product': product,
                        'quantity': 0,
                        'real_stock': 0,
                        'var_qty': 0,
                        'standard_price': product.standard_price,
                        'var_cost': 0,
                    }
                    stocktake_product_list[product_id] = rs
                    participating_stock_inventory_products.append(product_id)
                    if data_id.location.id not in participating_location_id:
                        participating_location_id.append(data_id.location.id)
                rs = stocktake_product_list[product.id]
                rs['quantity'] += line.quantity

                product_line = {
                    'location_name': line.stocktake_id.location.name,
                    'counter': line.stocktake_id.counter if line.stocktake_id.counter else "",
                    'notes': self._get_truncated_note(line.stocktake_id.notes) if line.stocktake_id.notes else "",
                    'quantity': line.quantity,
                }
                rs['location_lines'].append(product_line)

        inventory_line_ids = stock_inventory.line_ids
        all_locations = self._get_all_locations(inventory_line_ids)
        for inventory_line in inventory_line_ids:
            product = inventory_line.product_id
            product_id = product.id
            if product_id not in stocktake_product_list:
                rs = {
                    'product_id': product_id,
                    'location_lines': [],
                    'product': product,
                    'quantity': 0,
                    'real_stock': 0,
                    'var_qty': 0,
                    'standard_price': product.standard_price,
                    'var_cost': 0,
                }
                stocktake_product_list[product_id] = rs
                participating_stock_inventory_products.append(product_id)
                if inventory_line.location_id.id not in participating_location_id:
                    participating_location_id.append(inventory_line.location_id.id)
            rs = stocktake_product_list[product_id]
            product_line = {
                'location_name': location_name,
                'counter': 0,
                'notes': '',
                'quantity': 0,
            }
            rs['location_lines'].append(product_line)

        # CORRECTED SECTION: Create new environment with updated context
        env = self.env(context=dict(self.env.context, location=participating_location_id))

        for prod_item in env['product.product'].browse(participating_stock_inventory_products):
            rs = stocktake_product_list[prod_item.id]
            stocktake_line = env['stock.inventory.line'].search([
                ('inventory_id', '=', self.stocktake_id.id),
                ('product_id', '=', prod_item.id)
            ])
            if stocktake_line:
                stocktake_qoh = stocktake_line.theoretical_qty
            else:
                stocktake_qoh = 0.0
            rs['real_stock'] = stocktake_qoh
            rs['var_qty'] = rs['quantity'] - rs['real_stock']
            rs['var_cost'] = rs['standard_price'] * rs['var_qty']

        product_list = stocktake_product_list.values()

        for line in product_list:
            worksheet.write(row, 0, line['product'].default_code)
            worksheet.write(row, 1, line['product'].name)

            inv = line['location_lines'][0]
            if not inv['counter']:
                inv['counter'] = ""
            worksheet.write(row, 2, inv['counter'])
            worksheet.write(row, 3, inv['notes'])
            worksheet.write(row, 4, line['quantity'])
            worksheet.write(row, 5, line['real_stock'])
            worksheet.write(row, 6, line['var_qty'])
            worksheet.write(row, 7, line['var_cost'])
            row += 1

        format_number = workbook.add_format({'num_format': '0.00', 'align': 'right'})
        format_row = workbook.add_format({'text_wrap': True, 'bold': True})
        worksheet.set_row(0, 20, format_row)
        worksheet.set_column('B:B', 50, )
        worksheet.set_column('E:H', 20, format_number)

        workbook.close()
        data.seek(0)
        output = base64.b64encode(data.read()).decode()
        self.write({'data': output})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stocktake.checking.report',
            'view_mode': 'form',
            'res_id': wizard_item.id,
            'target': 'new',
        }
