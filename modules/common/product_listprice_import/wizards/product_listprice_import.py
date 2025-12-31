# -*- coding: utf-8 -*-
import base64
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ProductListpriceImport(models.TransientModel):
    _name = "product.listprice.import"
    _description = "Import Product Listprices"

    file = fields.Binary("File", required=True,
                         help=("Select the CSV file to import. The format should be:\n"
                               "Product-Code,List-Price\n"
                               "e.g. \"ABC01\",1.50"))
    notes = fields.Text("Notes", readonly=True)

    def button_import(self):

        product_model = self.env["product.product"].with_context(exact_match=True)

        notes = ""
        error_count = 0
        process_count = 0
        for line_no, line in enumerate(base64.b64decode(self.file).decode("utf-8").split("\n")):

            # Ignore header
            if not line_no:
                continue

            unpacked = line.split(",")
            if len(unpacked) < 2:
                if line:
                    _logger.warning("bad line={0}".format(line))
                    notes += "** Line {0} - unexpected number of fields: {1}\n".format(line_no + 1, len(unpacked))
                    error_count += 1
                continue

            product_code = unpacked[0]
            product = product_model.search([("default_code", '=', product_code)])
            list_price = False

            if not product:
                _logger.warning("couldn't find product={0}".format(product_code))
                notes += "** Line {0} - Unable to find product={1}\n".format(line_no + 1, product_code)
                error_count += 1
                continue

            if not unpacked[1]:
                _logger.warning("empty price for line={0}".format(line))
                notes += "** Line {0} - empty price field\n".format(line_no + 1)
                error_count += 1
                continue
            try:
                list_price = float(unpacked[1])
            except (TypeError, ValueError):
                _logger.warning("unconvertible Listprice={0}".format(unpacked[1]))
                notes += "** Line {0} - non-numeric price: {1}\n".format(line_no + 1, unpacked[1])
                error_count += 1
                continue

            if product and list_price:
                product.list_price = list_price

            process_count += 1

        self.notes = "{}\nProcessed: {}, Errors: {}".format(notes, process_count, error_count)

        return {
            "name": self._description,
            "view_mode": "form",
            "view_id": False,
            "view_type": "form",
            "res_model": self._name,
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "new",
        }
