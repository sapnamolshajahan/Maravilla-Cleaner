# -*- coding: utf-8 -*-
import base64
import logging
from datetime import datetime, timedelta
from io import BytesIO

import pytz
import xlsxwriter

from odoo import models, fields, api
from odoo.tools import float_is_zero, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _

log = logging.getLogger(__name__)


class ProductInventoryDownload(models.TransientModel):
    """
    Reports product Inventory Download
    Produces a CSV of stock levels of all products.
    Note in future this can be extended to include filters etc.
    """
    _name = "product.inventory.download"

    ###########################################################################
    # Fields
    ###########################################################################
    as_at_date = fields.Date("As At Date")
    include_location_ids = fields.Many2many(
        "stock.location", "product_inventory_report_loc_inc_rel",
        "report_id", "location_id", "Include Locations",
        domain=[("usage", "=", "internal")],
        help="Include only these Internal locations from the report")

    exclude_location_ids = fields.Many2many(
        "stock.location", "product_inventory_report_loc_exc_rel",
        "report_id", "location_id", "Exclude Locations",
        domain=[("usage", "=", "internal")],
        help="Exclude these Internal locations from the report")

    exclude_zero_quantity = fields.Boolean(
        "Exclude Zero Quantities", default=True,
        help=("If checked, lines with a zero quantity of the product "
              "at the location are excluded"))

    product_category_ids = fields.Many2many(
        "product.category", "product_inventory_report_category_rel",
        "report_id", "category_id", "Categories",
        help="Include only products in these categories")

    supplier_ids = fields.Many2many(
        "res.partner", "product_inventory_report_partner_rel",
        "report_id", "partner_id", "Suppliers",
        domain=[("supplier_rank", ">", 0)],
        help="Include only products supplied by these partners")

    ###########################################################################
    # Model methods
    ###########################################################################
    @api.onchange("include_location_ids")
    def _onchange_include_location_ids(self):
        if self.include_location_ids:
            self.exclude_location_ids = None

    @api.onchange("exclude_location_ids")
    def _onchange_exclude_location_ids(self):
        if self.exclude_location_ids:
            self.include_location_ids = None

    def button_process(self):
        """ Submit download task. """
        if len(self) > 1:
            raise Warning(_("Can only process one download at a time"))

        report_date = fields.Datetime.context_timestamp(self, datetime.now())
        report_date = report_date.strftime("%Y%m%d_%H%M%S")

        file_name = "Product Inventory Report-{date}-{user}.xlsx".format(date=report_date,
                                                                         user=self.env.user.display_name)

        stock_move_date = self._get_stock_move_filter_date(self.as_at_date)
        args = {'suppliers': [x.id for x in self.supplier_ids],
                'categories': [x.id for x in self.product_category_ids],
                'locations': [x.id for x in self.include_location_ids],
                'as_at_date': stock_move_date,
                'file_name': file_name,
                'exclude_locations': [x.id for x in self.exclude_location_ids],
                'exclude_zero': self.exclude_zero_quantity}

        job = self.with_delay(channel=self.light_job_channel())._create_product_inventory_report(args['suppliers'],
                                                                                                 args['categories'],
                                                                                                 args['locations'],
                                                                                                 args['as_at_date'],
                                                                                                 args['file_name'],
                                                                                                 args['exclude_locations'],
                                                                                                 args['exclude_zero'])
        Queue = self.env['queue.job']
        Queue.set_suppress_notifications(job.uuid, sen=False, ssn=False)
        return True

    @api.model
    def _get_stock_move_filter_date(self, as_at_date):
        """ Convert the as_at_date to a UTC date time.

            Stock move date is a date time so we need midnight of the next day
            as the query will use less than.

            :param as_at_date: date to select from.
            :returns A datetime string in UTC.
        """
        if not as_at_date:
            return ""

        user_tz = self.env.context.get("tz")
        local_tz = pytz.timezone(user_tz)
        end_datetime = (fields.Datetime.from_string(as_at_date) + timedelta(days=1))
        end_datetime = local_tz.localize(end_datetime)
        end_datetime = end_datetime.astimezone(pytz.UTC)
        return end_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _create_product_inventory_report(self, supplier_ids, category_ids,
                                         location_ids,
                                         as_at_date, file_name,
                                         exclude_location_ids,
                                         exclude_zero_quantity):
        """ Create product inventory download.

            Args:
                supplier_ids: res.partner IDs to filter.
                category_ids: product.category IDs to filter.
                location_ids: stock.location IDs to filter
                as_at_date: report as at date
                file_name: output file name.
                exclude_location_ids: stock.location IDs to exclude.
                exclude_zero_quantity: exclude lines with zero quantity.

        """

        def chunk_list(big_list, chunk_size):
            """
            Yield successive chunks from a list.

            :param big_list: big list of items.
            :param chunk_size: number of items in each chunk max.
            :return A list representing the next chunk of big_list.
            """
            for i in range(0, len(big_list), chunk_size):
                yield big_list[i:i + chunk_size]

        locations = self._get_stock_locations(location_ids, exclude_location_ids)
        products = self._get_products(supplier_ids, category_ids)

        if not locations or not products:
            return ("No Locations or Products found using report filters "
                    "and exclusions")

        rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Data')
        self._write_worksheet_header_row(worksheet)

        row = 1
        inbound_dict = self._get_inbound_quantities(locations, products, as_at_date, rounding)
        outbound_dict = self._get_outbound_quantities(locations, products, as_at_date, rounding)

        grand_total = 0
        for location in locations:
            for chunk in chunk_list(products, 500):
                for product in chunk:
                    stock_key = (location.id, product.id)
                    qty = (inbound_dict.get(stock_key, 0.00) - outbound_dict.get(stock_key, 0.00))

                    if float_is_zero(qty, precision_rounding=product.uom_id.rounding) and exclude_zero_quantity:
                        continue

                    self._write_worksheet_data_row(worksheet, row, location, product, qty)
                    grand_total += product.standard_price * qty
                    row += 1

        row += 1
        worksheet.write(row, 3, 'Total')
        worksheet.write(row, 5, grand_total)
        workbook.close()
        job_uuid = self.env.context.get("job_uuid")
        if job_uuid:
            job = self.env["queue.job"].search([('uuid', '=', job_uuid)], limit=1)
            if job:
                self.env["ir.attachment"].create(
                    {
                        "name": file_name,
                        "datas": base64.encodebytes(output.getvalue()),
                        "mimetype": "application/octet-stream",
                        "description": "Product Inventory Download",
                        "res_model": job._name,
                        "res_id": job.id,
                    })
        return ("Product Inventory report completed - wrote {ct} rows"
                ).format(ct=row)

    @api.model
    def _write_worksheet_data_row(self, worksheet, row, location, product, qty):
        u"""
        Write data line
        Made it a separate function so can vary columns for different customers
        """
        worksheet.write(row, 0, location.complete_name)
        worksheet.write(row, 1, product.id)
        worksheet.write(row, 2, product.default_code)
        worksheet.write(row, 3, product.name)
        worksheet.write(row, 4, product.categ_id.display_name)
        worksheet.write(row, 5, qty)
        worksheet.write(row, 6, product.standard_price)
        worksheet.write(row, 7, product.standard_price * qty)

    @api.model
    def _write_worksheet_header_row(self, worksheet):
        worksheet.write(0, 0, "Location")
        worksheet.write(0, 1, "Product ID")
        worksheet.write(0, 2, "Reference")
        worksheet.write(0, 3, "Description")
        worksheet.write(0, 4, "Category")
        worksheet.write(0, 5, "Real Stock")
        worksheet.write(0, 6, "Cost Price")
        worksheet.write(0, 7, "Cost Value")

    @api.model
    def _get_stock_locations(self, location_ids, exclude_location_ids):
        """ Get internal locations.

            If location_ids is set, return these locations,
            otherwise get all internal locations for the company
            less any exclude_location_ids.

            Args:
                location_ids: A list of locations to include
                exclude_location_ids: list of stock.location IDs to exclude.

            Returns:
                A list of internal location records or an empty list.
        """
        if location_ids:
            search_args = [("id", "in", location_ids)]
        else:
            search_args = [
                ("usage", "=", "internal"),
                ("company_id", "=", self.env.company.id)
            ]
            if exclude_location_ids:
                search_args.append(("id", "not in", exclude_location_ids))

        return self.env["stock.location"].search(search_args)

    @api.model
    def _get_products(self, supplier_ids, category_ids):
        """ Get a list of products to process.

            Args:
                supplier_ids: list of res.partner IDs for suppliers to filter.
                category_ids: list of product.category IDs to filter

            Returns:
                A list of product records or an empty list.
        """
        search_args = []
        if supplier_ids:
            product_suppliers = self.env["product.supplierinfo"].search(
                [("id", "in", supplier_ids)]
            )
            if product_suppliers:
                search_args.append(("product_tmpl_id", "in", [x.product_tmpl_id.id for x in product_suppliers]))

        if category_ids:
            search_args.append(("categ_id", "in", category_ids))

        search_args.append(("type", "!=", 'service'))

        products = self.env["product.product"].search(search_args)
        log.debug("_get_products: {{product_count: {ct}}}".format(ct=len(products)))
        return products

    @api.model
    def _get_inbound_quantities(self, locations, products, as_at_date, rounding):
        """ Get a dict of inbound quantities by location and product.

            Args:
                locations: stock.location records.
                products: product.product records.
                as_at_date: filter to this date if present.

            Returns:
                A dict of inbound quantities from stock.move
        """
        if as_at_date:
            date_filter = "and date < %(as_at_date)s "
        else:
            date_filter = ""

        self.env.cr.execute(
            ("select location_dest_id, product_id, "
             "sum(round(product_qty, {rounding})) from stock_move "
             "where location_dest_id in %(locn)s and "
             "product_id in %(prod)s and state='done' {date_filter} "
             "group by location_dest_id, product_id;"
             ).format(date_filter=date_filter, rounding=rounding),
            {"locn": tuple([x.id for x in locations]),
             "prod": tuple([x.id for x in products]),
             "date_filter": date_filter,
             "as_at_date": as_at_date}
        )

        res = dict([((x[0], x[1]), x[2]) for x in self.env.cr.fetchall()])
        log.debug("_get_inbound_quantities: {{item_count: {ct}}}".format(ct=len(res)))
        return res

    @api.model
    def _get_outbound_quantities(self, locations, products, as_at_date, rounding):
        """ Get a dict of outbound quantities by location and product.

            Args:
                locations: stock.location records.
                products: product.product records.
                as_at_date: filter to this date if present.

            Returns:
                A dict of outbound quantities from stock.move
        """
        if as_at_date:
            date_filter = "and date < %(as_at_date)s "
        else:
            date_filter = ""

        self.env.cr.execute(
            ("select location_id, product_id, "
             "sum(round(product_qty, {rounding})) from stock_move "
             "where location_id in %(locn)s and "
             "product_id in %(prod)s and state='done' {date_filter} "
             "group by location_id, product_id;"
             ).format(date_filter=date_filter, rounding=rounding),
            {"locn": tuple([x.id for x in locations]),
             "prod": tuple([x.id for x in products]),
             "date_filter": date_filter,
             "as_at_date": as_at_date}
        )

        res = dict([((x[0], x[1]), x[2]) for x in self.env.cr.fetchall()])
        log.debug("_get_outbound_quantities: {{item_count: {ct}}}".format(ct=len(res)))
        return res
