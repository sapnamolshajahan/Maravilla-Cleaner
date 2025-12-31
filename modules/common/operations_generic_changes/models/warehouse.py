# -*- coding: utf-8 -*-
from odoo import fields, models


class StockInventory(models.Model):
    _inherit = "stock.warehouse"

    ################################################################################
    # Fields
    ################################################################################
    company_partner = fields.Many2one("res.partner", related="company_id.partner_id",
                                      help="Technical field used in views")

    exclude_in_avail_stock = fields.Boolean(
        "Exclude in Avail Stock",
        help=("If set, the warehouse is excluded from the calculation of "
              "available stock on the product display and other places.")
    )

    ################################################################################
    # Functions
    ################################################################################
    def get_locations_in_tree(self):
        """ Get all locations for warehouse.

            Gets the input, output and stock locations for the warehouse,
            and the children/grand children etc., of all those locations.
        """
        res = {}
        locations = self.env["stock.location"]
        for wh_item in self:
            locations += (wh_item.wh_input_stock_loc_id + wh_item.wh_output_stock_loc_id + wh_item.lot_stock_id)
            res[wh_item.id] = locations.get_child_locations()

        return res
