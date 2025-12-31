# -*- coding: utf-8 -*-
import base64
from collections import defaultdict
from io import BytesIO

import xlsxwriter
from odoo.exceptions import UserError

from odoo import fields, models


class StocktakeCountSheet(models.TransientModel):
    """
    Count Sheets for StockTake
    """

    _name = "stocktake.count.sheet"

    report_name = fields.Char(string="Report Name", readonly=True, default="Count Sheets.xlsx")
    stocktake_id = fields.Many2one("stock.inventory", string="Stocktake", required=True, domain="[('state', '=', 'confirm')]")
    data = fields.Binary("Download File", readonly=True)
    lines_per_page = fields.Integer(string="Lines per Page", default=40)
    include_counts = fields.Boolean(string="Include Expected Count on Report", help="If yes, print the current on hand")
    line_per_serial = fields.Boolean(
        string="Line per Serial Number", help="If set, print one line per serial number expected"
    )
    line_per_bin = fields.Boolean(string="Line per Bin")
    print_serial = fields.Boolean(
        string="Print Serial Number", help="If yes, print the serial number for the product, one line per serial number"
    )
    populate_qty_data_entry = fields.Boolean(string="Populate expected counts onto data entry records")

    def get_all_products_for_location(self, stock_inventory_location):
        self.env.cr.execute(
            (
                "select product_id "
                "from stock_move "
                "where state = 'done' "
                "group by product_id "
                "having sum(CASE "
                "when location_id=%(loc)s then 0 - product_uom_qty "
                "when location_dest_id=%(loc)s then product_uom_qty END ) != 0"
            ),
            {"loc": stock_inventory_location.id},
        )

        if self.env.cr.rowcount:
            product_list = set([tup[0] for tup in self.env.cr.fetchall()])
            return_list = []
            products = self.env["product.product"].browse(product_list)
            for product_id in products:
                if product_id.bom_ids and product_id.bom_ids[0].type == 'phantom':
                    pass
                return_list.append(product_id)
            return return_list
        else:
            return []

    def build_other_bins(self, all_bins, this_bin):
        return ",".join([x.name for x in all_bins if x.name and x.name != this_bin.name])

    def get_data(self, stock_inventory):
        def chunk_list(big_list, chunk_size):
            for i in range(0, len(big_list), chunk_size):
                yield big_list[i:i + chunk_size]

        move_products = []
        stocktake_products = []

        # Validate warehouses first and create a mapping
        location_warehouse_map = {}
        for location in stock_inventory.location_ids:
            warehouse = self.env["stock.warehouse"].search([("lot_stock_id", "=", location.id)])
            if not warehouse:
                raise UserError(
                    "{location} is not the main stock location for any warehouse".format(location=location.name)
                )
            location_warehouse_map[location.id] = warehouse

        if stock_inventory.coverage == "warehouses":
            serialised = self.env['product.template'].search([('tracking', '!=', 'none')])
            serialised_products = [x.id for x in serialised.product_variant_ids]
            for location in stock_inventory.location_ids:
                extra_products = self.get_all_products_for_location(location)
                if extra_products:
                    move_products.extend(extra_products)
                # need to handle serialised products with +ve and -ve values
                quants = self.env['stock.quant'].search([('product_id', 'in', serialised_products),
                                                         ('location_id', '=', location.id),
                                                         ('quantity', '!=', 0)])
                if quants:
                    move_products.extend(list(set([x.product_id for x in quants])))

        stocktake_products.extend([p for p in stock_inventory.product_ids])
        products = list(set(move_products + stocktake_products))
        if not products:
            raise UserError("No products found")

        line_result = ["", "", "", "", "", 0, 0]
        dict_of_results = defaultdict(dict)

        for chunk in chunk_list(products, 250):
            for product in chunk:
                if not product:
                    continue
                product_result = []

                # Get warehouses for all locations that contain this product
                product_warehouses = []
                for location in stock_inventory.location_ids:
                    if location.id in location_warehouse_map:
                        product_warehouses.append(location_warehouse_map[location.id])

                # Use the first warehouse as default, or handle multiple warehouses
                if product_warehouses:
                    warehouse = product_warehouses[0]
                    bins = self.env["stock.warehouse.bin"].search(
                        [("product_id", "=", product.id), ("warehouse_id", "=", warehouse.id)], order="name asc"
                    )
                    other_bins = ""
                    if bins:
                        primary_bin = bins[0].name
                    else:
                        primary_bin = "None"
                else:
                    bins = self.env["stock.warehouse.bin"].search(
                        [("product_id", "=", product.id)], order="name asc"
                    )
                    primary_bin = bins[0].name if bins else "None"
                    other_bins = ""

                # TODO - need to include child location
                locations = [x.id for x in stock_inventory.location_ids]
                from_stock_moves = self.env['stock.move'].search([('product_id', '=', product.id),
                                                                  ('location_id', 'in', locations),
                                                                  ('state', '=', 'done')])
                from_qty = sum([x.product_uom_qty for x in from_stock_moves])
                to_stock_moves = self.env['stock.move'].search([('product_id', '=', product.id),
                                                                ('location_dest_id', 'in', locations),
                                                                ('state', '=', 'done')])

                to_qty = sum([x.product_uom_qty for x in to_stock_moves])
                on_hand = to_qty - from_qty

                line_result = [product.default_code, product.name, "", primary_bin, other_bins, on_hand, product.id]

                if self.line_per_serial and product.tracking != 'none':
                    if product.tracking == 'serial':
                        quants = self.env['stock.quant'].search([('product_id', '=', product.id),
                                                                 ('location_id', 'in',
                                                                  [x.id for x in stock_inventory.location_ids])])
                        for quant in quants:
                            line_result = [product.default_code, product.name, quant.lot_id.id, primary_bin, other_bins,
                                           quant.quantity, product.id]
                            product_result.append(line_result)
                    elif product.tracking == 'lot':
                        quants = self.env['stock.quant'].search([('product_id', '=', product.id),
                                                                 ('location_id', 'in',
                                                                  [x.id for x in stock_inventory.location_ids])])
                        for quant in quants:
                            line_result = [product.default_code, product.name, quant.lot_id.id, primary_bin, other_bins,
                                           quant.quantity, product.id]
                            product_result.append(line_result)

                # if product is serialised there will be a quant per lot/serial so will already have a separate line
                # set quantity to 0 for by bin as we are not holding stock by bin
                elif self.line_per_bin and bins:
                    for unique_bin in bins:
                        other_bins = self.build_other_bins(bins, unique_bin)
                        line_result = [product.default_code, product.name, "", unique_bin.name, other_bins, 0,
                                       product.id]
                        product_result.append(line_result)

                if not self.include_counts:
                    if not product_result:
                        line_result[5] = 0.0
                    else:
                        for result in product_result:
                            result[5] = 0.0
                if not product.name:
                    continue
                if not product_result:
                    unique_key = str(primary_bin) + "-" + str(product.default_code) + "-" + str(product.name)
                    dict_of_results[unique_key] = line_result
                else:
                    for i in range(0, len(product_result)):
                        if not product_result[i][2]:
                            lot_name = 'AAA'
                        else:
                            lot_name = str(product_result[i][2])
                        unique_key = str(primary_bin) + "-" + str(product.default_code) + "-" + str(
                            product.name) + "-" + lot_name
                        dict_of_results[unique_key] = product_result[i]

                from_stock_moves.invalidate_recordset()
                to_stock_moves.invalidate_recordset()

        return dict_of_results

    def create_stocktake_data_entry(self, stock_inventory, worksheet_counter):
        if not stock_inventory.location_ids:
            if stock_inventory.warehouse_id:
                stock_inventory.write({'location_ids': [(6, 0, [stock_inventory.warehouse_id.lot_stock_id.id])]})
            else:
                raise UserError('Did not find any locations or warehouse for this inventory')

        data_entry_id = self.env["stocktake.data.entry"].create(
            {
                "name": stock_inventory.name + " Page " + str(worksheet_counter),
                "inventory": stock_inventory.id,
                "state": "draft",
                "location": stock_inventory.location_ids[0].id,
            }
        )
        return data_entry_id

    def button_process(self):
        """
        Create the report.
        """
        wizard_item = self[0]
        data = BytesIO()
        stock_inventory = wizard_item.stocktake_id

        # delete any existing data entry records so can run more than once
        entry_recs = self.env["stocktake.data.entry"].search([("inventory", "=", stock_inventory.id)])
        lines = self.env["stocktake.data.entry.line"].search([("stocktake_id", "=", stock_inventory.id)])
        lines.unlink()
        entry_recs.unlink()

        workbook = xlsxwriter.Workbook(data, {"in_memory": True})

        dict_of_results = self.get_data(stock_inventory)
        line_count = 0
        worksheet_counter = 1
        data_entry_id = self.create_stocktake_data_entry(stock_inventory, worksheet_counter)
        # do first page headings
        worksheet = workbook.add_worksheet(str(worksheet_counter))
        worksheet.write(1, 0, "Page" + str(worksheet_counter))
        worksheet.write(2, 0, "Code")
        worksheet.write(2, 1, "Description")
        worksheet.write(2, 2, "Serial #")
        worksheet.write(2, 3, "Primary Bin")
        worksheet.write(2, 4, "Other Bins")
        worksheet.write(2, 5, "On Hand")
        worksheet.write(2, 6, "Count")
        row = 3

        for key in sorted(dict_of_results.keys()):
            if line_count >= wizard_item.lines_per_page:
                worksheet_counter += 1
                worksheet = workbook.add_worksheet(str(worksheet_counter))
                worksheet.write(1, 0, "Page" + str(worksheet_counter))
                worksheet.write(2, 0, "Code")
                worksheet.write(2, 1, "Description")
                worksheet.write(2, 2, "Serial #")
                worksheet.write(2, 3, "Bin")
                worksheet.write(2, 4, "Other Bins")
                worksheet.write(2, 5, "On Hand")
                worksheet.write(2, 6, "Count")

                row = 3
                line_count = 0
                data_entry_id = self.create_stocktake_data_entry(stock_inventory, worksheet_counter)
            record = dict_of_results[key]
            for i in range(0, 6):
                worksheet.write(row, i, record[i])
            row += 1
            line_count += 1
            if record[5] and record[5] >= 0.0:
                quantity = record[5]
            else:
                quantity = 99999
            if self.populate_qty_data_entry:
                if not record[6]:
                    pass
                self.env["stocktake.data.entry.line"].create(
                    {
                        "name": data_entry_id.name,
                        "product_id": record[6],
                        "stocktake_id": data_entry_id.id,
                        "quantity": quantity if quantity > 0 else 0,
                        "production_lot_id": record[2] if record[2] else False,
                    }
                )
            else:
                if not record[6]:
                    pass
                self.env["stocktake.data.entry.line"].create(
                    {
                        "name": data_entry_id.name,
                        "product_id": record[6],
                        "stocktake_id": data_entry_id.id,
                        "production_lot_id": record[2] if record[2] else False,
                    }
                )

        format_number = workbook.add_format({"num_format": "0.00", "align": "right"})
        format_text_wrap = workbook.add_format({"text_wrap": True})
        format_row = workbook.add_format({"text_wrap": True, "bold": True})
        for worksheet in workbook.worksheets():
            worksheet.set_landscape()
            worksheet.print_area(0, 0, wizard_item.lines_per_page + 4, 6)
            worksheet.hide_gridlines(0)  # print the gridlines
            worksheet.set_margins(0.4, 0.4, 0.4, 0.4)
            worksheet.set_row(0, 20, format_row)
            worksheet.set_column(
                "A:A",
                12,
            )
            worksheet.set_column("A:A", 20, format_text_wrap)
            worksheet.set_column("B:B", 80, format_text_wrap)
            worksheet.set_column("C:C", 15)
            worksheet.set_column("D:D", 10)
            worksheet.set_column("E:E", 12, format_text_wrap)
            worksheet.set_column("F:G", 8, format_number)

        workbook.close()
        data.seek(0)
        output = base64.b64encode(data.read()).decode()
        self.write({"data": output})

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": wizard_item.id,
            "target": "new",
        }
