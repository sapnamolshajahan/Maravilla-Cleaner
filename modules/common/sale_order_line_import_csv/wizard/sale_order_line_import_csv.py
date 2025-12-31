# -*- coding: utf-8 -*-
import logging
from datetime import datetime
import csv
import base64
from io import StringIO


from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class SaleOrderLineImport(models.TransientModel):
    """ Create sale order lines from a CSV"""
    _name = "sale.order.line.import"

    ###########################################################################
    # Fields
    ###########################################################################

    csv_delimiter = fields.Char(string="Delimiter", required=True, readonly=True, default=",",
                                help=("CSV field delimter - default is \",\"\n"
                                      "This must either be a single character or use "
                                      "\"SPACE\" for space delimited files"))
    csv_file = fields.Binary(string="File", required=True, readonly=True,
                             help=("Select the CSV file to import.  The format should be \n"
                                   "Product Reference,quantity \n"
                                   "e.g. \"ABC01\",1.5"))
    csv_quote_char = fields.Char(string="Quote Character", required=True, readonly=True, default='"',
                                 help="CSV quote character - default is \"")
    notes = fields.Text(string="Notes", readonly=True,
                        help="These notes will be added to all sale order lines created")
    has_header_line = fields.Boolean("CSV has header", readonly=True, default=True,
                                     help="If checked, the first line in the file will be ignored")
    ignore_errors = fields.Boolean(string="Ignore Errors", readonly=True, default=False,
                                   help=("If checked, lines with errors are skipped but lines without "
                                         "errors are processed.  If not checked, a single error causes "
                                         "the entire import to fail"))
    order_id = fields.Many2one(comodel_name="sale.order", string="Order", readonly=True, ondelete="set null")
    processing_notes = fields.Text(string="Processing Notes", readonly=True)
    state = fields.Selection([("draft", "Draft"), ("done", "Done")], string="State", readonly=True, default="draft")

    def button_import_csv(self):
        self.ensure_one()

        start_time = datetime.now()
        logger = logging.getLogger(__name__)
        logger.info("button_import_csv - start order line csv import")
        product_cache = {}
        process_notes = []
        wizard_item = self.browse(self.ids[0])

        if wizard_item.state != "draft":
            raise UserError(_("Error - CSV File already processed!") + "\n" +
                            _("The CSV file has already been processed."))

        sol_model = self.env["sale.order.line"]
        decoded_data = base64.b64decode(wizard_item.csv_file).decode("utf-8", errors="ignore")
        csv_data = StringIO(decoded_data)
        ws = csv.reader(csv_data, delimiter=wizard_item.csv_delimiter[0])

        line_count = 0
        delimiter = str(wizard_item.csv_delimiter)
        if delimiter == "SPACE":
            delimiter = " "
        else:
            delimiter = delimiter[0]

        process_error = "ERROR - Skipped line - {msg}"

        next(ws, None)  # skip header
        for row in ws:
            sale_order_line = {}
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(row)

            # Skip blank rows
            if not row:
                continue

            # Check the row
            if not row or len(row) not in [2, 3, 4]:
                message = ("CSV row \"{row}\" should be product reference{delim}quantity{delim}discount{delim}"
                           "warehouse.\r\nDiscount and Warehouse are optional").format(row=row, delim=delimiter)
                if wizard_item.ignore_errors:
                    process_notes.append(process_error.format(msg=message))
                    continue
                else:
                    raise UserError(_("Error - CSV row error!") + "\n" + _(message))

            # Get the product data
            product_ref = row[0]
            product_data = self.get_product_with_reference(product_ref, product_cache)
            if not product_data:
                message = "Product \"{ref}\" not found".format(ref=product_ref)
                if wizard_item.ignore_errors:
                    process_notes.append(process_error.format(msg=message))
                    continue
                else:
                    raise UserError(_("Error - Product Reference error!") + "\n" + _(message))
            product_id = product_data["id"]
            product = self.env['product.product'].browse(product_id)

            # Get the quantity data
            quantity = self.get_quantity(row[1])
            if not quantity:
                message = "Quantity \"{qty}\" is zero or could not be converted to a number".format(qty=row[1])
                if wizard_item.ignore_errors:
                    process_notes.append(process_error.format(msg=message))
                    continue
                else:
                    raise UserError(_("Error - Quantity error!") + "\n" + _(message))

            discount = 0
            if len(row) > 2:
                # Get the discount
                discount = row[2]
                if discount != None:

                    try:
                        discount = float(discount)
                    except Exception:
                        message = "Discount \"{ref}\" is not valid".format(ref=discount)
                        if wizard_item.ignore_errors:
                            process_notes.append(process_error.format(msg=message))
                            continue
                        else:
                            raise UserError(_("Error - Discount error!") + "\n" + _(message))

            # - Get the warehouse
            warehouse_id = False
            if len(row) == 4 and row[3] != None:
                warehouse_id = self.get_warehouse(row[3])

                if not warehouse_id and row[3]:
                    message = "Warehouse \"{wh}\" cannot be found in the system".format(wh=row[3])
                    if wizard_item.ignore_errors:
                        process_notes.append(process_error.format(msg=message))
                        continue
                    else:
                        raise UserError(_("Error - Warehouse Error!") + "\n" + _(message))

            if not warehouse_id:
                warehouse_id = wizard_item.order_id.warehouse_id.id

            product_uom = product.uom_id.id

            sale_order_line.update({
                "product_id": product.id,
                "price_unit": 0,
                "order_id": wizard_item.order_id.id,
                "product_uom_id": product_uom,
                "product_uom_qty": quantity,
                "name": product.name,
                # "notes": wizard_item.notes and wizard_item.notes or False,
                "discount": 0
            })

            sol_id = sol_model.create(sale_order_line)
            sol_id._compute_price_unit()
            sol_id._compute_discount()

            if discount:
                sol_id.discount = discount
                sol_id._compute_amount()

            logger.debug("button_import_csv - order line {sol_id} created".format(sol_id=sol_id))
            line_count += 1

        process_notes.append("Added {ct} sale order lines".format(ct=line_count))
        self.write({"processing_notes": "\n".join(process_notes), "state": "done"})
        elapsed = (datetime.now() - start_time).seconds

        logger.info(("button_import_csv - completed sale order line import. "
                     "Order line count is {sol_ct}, elapsed = {secs}s").format(sol_ct=line_count, secs=elapsed))

        return {"type": "ir.actions.act_window_close"}

    def get_product_with_reference(self, product_ref, product_cache):
        """ Get product information from the cache or from the database.
                        Args:
                                product_ref: Product default code field
                                product_cache: Product cache to check

                        Returns:
                                Product details dictionary from the cache
        """
        if not product_ref:
            return False

        if product_ref in product_cache:
            return product_cache[product_ref]

        product_model = self.env["product.product"].with_context(exact_match=True)
        prod_ids = product_model.search([("default_code", '=', product_ref)], limit=1)
        if prod_ids:
            product_cache[product_ref] = {'id': prod_ids[0].id}

        return product_cache.get(product_ref, False)

    @api.model
    def get_quantity(self, quantity):
        """ Convert the quantity into a float.
            :param: quantity: Quantity from the CSV file.
            :return: Quantity or 0 if this cannot be determined
        """
        if quantity is None or not quantity:
            return 0.0

        try:
            return float(quantity)
        except (TypeError, ValueError):
            return 0.0

    @api.model
    def get_warehouse(self, warehouse):

        if not warehouse:
            return False

        warehouse_id = self.env["stock.warehouse"].search([('name', '=ilike', warehouse)], limit=1)
        if not warehouse_id:
            return False
        else:
            return warehouse_id[0].id
