# -*- coding: utf-8 -*-
import base64
from io import BytesIO as StringIO

import xlsxwriter

from odoo import fields, models, api
from odoo.tools import float_is_zero, float_compare


class StocktakeVarianceReport(models.TransientModel):
    """
    Reports on stocktake variances
    """
    _name = "stocktake.variance.report"
    _description = 'Stocktake Variance Report'

    stocktake_id = fields.Many2one("stock.inventory", string="Stocktake")
    report_name = fields.Char(string="Report Name", readonly=True, default="Stocktake Variance Report.xlsx")
    data = fields.Binary("Download File", readonly=True)
    include_non_counted_products = fields.Boolean("Include Products not counted",
                                                  help=("If checked, the report will include "
                                                        "products with stock on hand that were "
                                                        "not included in the stock take counts"))

    @api.model
    def _get_all_locations(self, inventory_line_ids):
        return list(set([line.location_id.id for line in inventory_line_ids]))

    @api.model
    def _get_products_with_stock(self, location_list, precision):
        """ Get  all products with SOH<>0 for this company and locations not already in count lines
        """

        all_quants = self.env['stock.quant'].search([('location_id', 'in', location_list)])
        all_products = list(set([x.product_id for x in all_quants]))
        res = {}

        for product in all_products:
            stocktake_line = self.env['stock.inventory.line'].search([('inventory_id', '=', self.stocktake_id.id),
                                                                      ('product_id', '=', product.id)])
            if not stocktake_line:
                values = res.setdefault(product.id,
                                        {"counted_stock": 0.0,
                                         "theoretical_stock": 0.0}
                                        )

                from_stock_moves = self.env['stock.move'].search([('product_id', '=', product.id),
                                                                  ('location_id', 'in', self.stocktake_id.location_ids.ids),
                                                                  ('state', '=', 'done')])
                from_qty = sum([x.product_uom_qty for x in from_stock_moves])
                to_stock_moves = self.env['stock.move'].search([('product_id', '=', product.id),
                                                                ('location_dest_id', 'in', self.stocktake_id.location_ids.ids),
                                                                ('state', '=', 'done')])

                to_qty = sum([x.product_uom_qty for x in to_stock_moves])
                theoretical_qty = to_qty - from_qty
                values["theoretical_stock"] = theoretical_qty

        return res

    @api.model
    def _get_counted_stock(self, lines):
        """ Get the counted and theoretical quantity per product.

            There may be multiple counts of the same product so we add up,
            we do not care about location at this point

            Args:
                lines: stock.inventory.line records.

            Returns:
                dictionary: key = product.id,
                    value = dictionary of counted and theoretical stock.
        """
        res = {}
        for line in lines:
            values = res.setdefault(line.product_id.id,
                                    {"counted_stock": 0.0,
                                     "theoretical_stock": 0.0}
                                    )

            values["counted_stock"] = values["counted_stock"] + line.product_qty
            values["theoretical_stock"] = values["theoretical_stock"] + line.theoretical_qty

        return res

    @api.model
    def _get_stock_for_product(self, product_id, location_list):
        """ Get current product available at the locations.

            Args:
                product_id: product.product ID
                location_list: list of stock.location IDs.

            Returns:
                quantity available
        """
        ctx = dict(self.env.context or {}, location=location_list)
        self.env.context = ctx
        return self.env["product.product"].browse(product_id).qty_available

    def button_process(self):
        """
        Create the report.
        """
        wizard = self[0]
        data = StringIO()
        stock_inventory = wizard.stocktake_id

        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('Data')
        self._write_worksheet_headings(worksheet)

        all_locations = self._get_all_locations(stock_inventory.line_ids)

        obj_precision = self.env["decimal.precision"]
        prec = obj_precision.precision_get("Product Unit of Measure")

        if wizard.include_non_counted_products:
            in_stock_products = self._get_products_with_stock(all_locations, prec)
        else:
            in_stock_products = {}

        counted_stock_products = self._get_counted_stock(stock_inventory.line_ids)

        report_products = list(set(list(in_stock_products.keys()) + list(counted_stock_products.keys())))
        report_products = self.env["product.product"].browse(report_products)

        row = 0
        for product in report_products:
            row += 1
            counted_stock = 0.0
            current_on_hand = 0.0
            variance = 0.0
            variance_cost = 0.0
            variance_cost_percentage = 0.0
            variance_qty_percentage = 0.0

            standard_price = product.standard_price
            if not standard_price:
                standard_price = product.product_tmpl_id.standard_price

            if product.id in in_stock_products:
                current_on_hand = in_stock_products[product.id]['theoretical_stock']
            else:
                current_on_hand = counted_stock_products[product.id]['theoretical_stock']

            if product.id in counted_stock_products:
                counted_stock = counted_stock_products[product.id]["counted_stock"]
                variance = counted_stock - current_on_hand
                variance_cost = variance * product.standard_price
                if float_is_zero(counted_stock, precision_digits=prec):
                    if not float_is_zero(current_on_hand, precision_digits=prec):
                        if current_on_hand > 0:
                            variance_qty_percentage = -100
                        else:
                            variance_qty_percentage = 100
                else:
                    variance_qty_percentage = (current_on_hand / counted_stock * 100)

                counted_cost = counted_stock * product.standard_price
                if float_is_zero(counted_cost, precision_digits=prec):

                    theoretical_cost = current_on_hand * standard_price
                    if not float_is_zero(theoretical_cost, precision_digits=prec):
                        if current_on_hand > 0:
                            variance_cost_percentage = -100
                        else:
                            variance_cost_percentage = 100

                else:
                    variance_cost_percentage = (variance_cost / counted_cost * 100)

            if product.id not in counted_stock_products:
                variance = 0 - current_on_hand
                variance_cost = variance * standard_price
                compare = float_compare(variance, 0.0, precision_digits=prec)
                if compare < 0:
                    variance_qty_percentage = -100
                    variance_cost_percentage = -100
                elif compare > 0:
                    variance_qty_percentage = 100
                    variance_cost_percentage = 100

            self._write_worksheet_row(worksheet, row, product,
                                      counted_stock=counted_stock,
                                      variance=variance,
                                      variance_qty_percentage=variance_qty_percentage,
                                      variance_cost=variance_cost,
                                      variance_cost_percentage=variance_cost_percentage,
                                      current_on_hand=current_on_hand,
                                      standard_price=standard_price)

        self._add_worksheet_formats(workbook, worksheet)
        workbook.close()
        data.seek(0)
        output = base64.encodebytes(data.read())
        self.write({'data': output})

        return {
            "type": "ir.actions.act_window",
            "res_model": "stocktake.variance.report",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }

    def _write_worksheet_row(self, worksheet, row, product, theoretical_stock=0.0,
                             counted_stock=0.0, variance=0.0,
                             variance_qty_percentage=0.0,
                             variance_cost=0.0, variance_cost_percentage=0.0,
                             current_on_hand=0.0, standard_price=0.0):
        """ Write a row to the worksheet.

            Args:
                worksheet: current worksheet object.
                row: row number to write.
                product: product.product record.
        """

        # bit belt and braces but name get returns list with tuple inside and not sure what happens if no variants
        actual_name = False
        prod_name = product.display_name
        if prod_name and prod_name[0]:
            ret_list = list(prod_name[0])
            if len(ret_list) > 0:
                actual_name = ret_list[1]

        if not actual_name:
            actual_name = product.product_tmpl_id.name

        worksheet.write(row, 0, product.default_code)
        worksheet.write(row, 1, actual_name)
        worksheet.write(row, 2, counted_stock)
        worksheet.write(row, 3, current_on_hand)
        worksheet.write(row, 4, variance)
        worksheet.write(row, 5, variance_qty_percentage)
        worksheet.write(row, 6, standard_price)
        worksheet.write(row, 7, variance_cost)
        worksheet.write(row, 8, variance_cost_percentage)

    def _write_worksheet_headings(self, worksheet):
        worksheet.write(0, 0, "Code")
        worksheet.write(0, 1, "Description")
        worksheet.write(0, 2, "Real (Counted) Qty")
        worksheet.write(0, 3, "Stock on-hand")
        worksheet.write(0, 4, "Variance Qty")
        worksheet.write(0, 5, "Variance Qty%")
        worksheet.write(0, 6, "Cost Price")
        worksheet.write(0, 7, "Variance $")
        worksheet.write(0, 8, "% Variance $")

    def _add_worksheet_formats(self, workbook, worksheet):
        """ Add required formats to the workseet. """
        format_number = workbook.add_format({'num_format': '0.00', 'align': 'right'})
        format_row = workbook.add_format({'text_wrap': True, 'bold': True})
        worksheet.set_row(0, 20, format_row)
        worksheet.set_column('B:B', 50, )
        worksheet.set_column('C:J', 20, format_number)
