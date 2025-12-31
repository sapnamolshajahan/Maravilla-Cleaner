# -*- coding: utf-8 -*-
from collections import OrderedDict
from io import BytesIO
import base64

import xlsxwriter

from odoo import models, api
from odoo.tools import float_compare


class OperationsMovesVsQuantsReport(models.TransientModel):
    """
    Reports any stock moves that do not match up with quants (qty-wise)

    Produces a XLSX file

    Attributes:
    """
    _name = "operations.moves.quants.report"

    @api.model
    def _write_worksheet_header_row(self, worksheet):
        worksheet.write(0, 0, "Product Code")
        worksheet.write(0, 1, "Product")
        worksheet.write(0, 2, "Location")
        worksheet.write(0, 3, "Move Qty")
        worksheet.write(0, 4, "Quant Qty")

    def _get_orphaned_quants(self, locations):
        if len(locations) == 1:
            loc = "({})".format(locations[0].id)
        else:
            loc = tuple(locations.ids)

        self.env.cr.execute("""
        select
          stock_quant.id,
          product_product.id,
          product_product.default_code,
          stock_quant.location_id,
          stock_quant.create_date,
          stock_quant.quantity,
          count (stock_move)
        from stock_quant, product_product, product_template, stock_move
        where stock_quant.location_id in
          (select stock_location.id from stock_location where usage = 'internal' and id in {loc})
        and product_product.id = stock_quant.product_id
        and product_template.id = product_tmpl_id
        and product_template.type = 'product'        
        and stock_move.product_id = stock_quant.product_id
        and
        (
            stock_move.location_id = stock_quant.location_id or
            stock_move.location_dest_id = stock_quant.location_id
        )
        group by
          stock_quant.id,
          stock_quant.location_id,
          product_product.id,
          product_product.default_code,
          stock_quant.create_date,
          stock_quant.quantity
        having count (stock_move) = 0
        order by
          stock_quant.location_id,
          product_product.default_code
        """.format(loc=loc))

        return self.env.cr.fetchall()

    def get_stock_moves_soh(self, product, location):
        stock_moves = self.env['stock.move.line'].search([
            '|', ('location_id', '=', location.id),
            ('location_dest_id', '=', location.id),
            ('product_id', '=', product.id),
            ('state', '=', 'done')])

        soh = 0.0
        for stock_move in stock_moves:
            if stock_move.location_id.id == location.id and \
                    stock_move.location_dest_id.id == location.id:
                continue
            elif stock_move.location_id.id == location.id:
                if stock_move.product_uom_id.category_id.id == stock_move.product_id.uom_id.category_id.id:
                    soh -= stock_move.product_uom_id._compute_quantity(stock_move.quantity,
                                                                    stock_move.product_id.uom_id)
                else:
                    soh -= stock_move.quantity
            else:
                if stock_move.product_uom_id.category_id.id == stock_move.product_id.uom_id.category_id.id:
                    soh += stock_move.product_uom_id._compute_quantity(stock_move.quantity,
                                                                    stock_move.product_id.uom_id)
                else:
                    soh += stock_move.quantity

        return soh

    def get_stock_quants_soh(self, product, location):
        quants = self.env['stock.quant'].search([('product_id', '=', product.id),
                                                 ('location_id', '=', location.id)])

        soh = sum([x.quantity for x in quants])
        return soh

    def _generate_report(self):
        """
        Create product on hand download.
        """
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data')
        self._write_worksheet_header_row(worksheet)
        row = 1

        products = self.env['product.product'].search([('product_tmpl_id.type', 'not in', ('service', 'consu'))])
        stock_locations = self.env['stock.location'].search([('company_id', '=', self.env.company.id),
                                                             ('usage', '=', 'internal')])

        for location in stock_locations:
            for product in products:
                stock_moves_soh = self.get_stock_moves_soh(product, location)
                quants_soh = self.get_stock_quants_soh(product, location)

                if float_compare(stock_moves_soh, quants_soh, precision_rounding=0.001) != 0:
                    worksheet.write(row, 0, product.default_code)
                    worksheet.write(row, 1, product.name)
                    worksheet.write(row, 2, location.complete_name)
                    worksheet.write(row, 3, stock_moves_soh)
                    worksheet.write(row, 4, quants_soh)
                    row += 1

        row += 2
        worksheet.write(row, 0, "'Orphaned' Quants")
        row += 1
        worksheet.write(row, 0, "Product Id")
        worksheet.write(row, 1, "Part Number")
        worksheet.write(row, 2, "Warehouse")
        worksheet.write(row, 3, "Quant Qty")
        worksheet.write(row, 4, "Create Date")
        row += 1

        orph_quants = self._get_orphaned_quants(stock_locations)
        # row = sq.id, product_id, product.default_code, sq.location_id, dt, sq.qty, count(sm)
        for r in orph_quants:
            worksheet.write(row, 0, r[2])
            worksheet.write(row, 1, r[1])
            worksheet.write(row, 2, r[3])
            worksheet.write(row, 3, r[4])
            worksheet.write(row, 4, r[5])
            row += 1

        workbook.close()
        output.seek(0)

        job_uuid = self.env.context.get("job_uuid")
        if job_uuid:
            job = self.env["queue.job"].search([('uuid', '=', job_uuid)], limit=1)
            if job:
                self.env["ir.attachment"].create(
                    {
                        "name": 'Quants-Moves.xlsx',
                        "datas": base64.encodebytes(output.getvalue()),
                        "mimetype": "application/octet-stream",
                        "description": "Quant/Moves Discrepancy",
                        "res_model": job._name,
                        "res_id": job.id,
                    })
        return ("Quant/Moves Discrepancy report completed - wrote {ct} rows"
                ).format(ct=row)

    def schedule_report(self):
        self.with_delay(channel=self.light_job_channel(),
                        description="Quant/Moves Discrepancy Report")._generate_report()
