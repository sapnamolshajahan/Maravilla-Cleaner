# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo.exceptions import UserError

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ForecastGeneratePO(models.TransientModel):
    _name = "forecast.generate.purchase"
    _description = "Generate Purchase Order"

    ###########################################################################
    # Fields
    ###########################################################################
    forecast_data = fields.Many2one("forecast.data", string="Forecast",
                                    required=True, readonly=True, ondelete="cascade")
    lines = fields.One2many("forecast.generate.purchase.line", "wizard", string="Suppliers")

    @api.model
    def create_wizard(self, forecast_data):
        wizard = self.create({"forecast_data": forecast_data.id})
        suppliers = set()
        for line in forecast_data.lines:
            # ignore lines already assigned, and lines without suppliers
            if line.purchase or not line.supplierinfo or line.supplierinfo.partner_id.id in suppliers:
                continue

            suppliers.add(line.supplierinfo.partner_id.id)
            self.env["forecast.generate.purchase.line"].create(
                {
                    "wizard": wizard.id,
                    "supplier": line.supplierinfo.partner_id.id,
                })

        if not suppliers:
            raise UserError("No available lines with suppliers found")
        return wizard

    def button_generate(self):

        purchase_model = self.env["purchase.order"]
        buyline_model = self.env["purchase.order.line"]
        for gline in self.lines:
            if not gline.select:
                continue

            datalines = self.forecast_data.lines.filtered(
                lambda d: d.supplierinfo.partner_id.id == gline.supplier.id and d.order_qty > 0 and not d.purchase)
            if not datalines:
                continue
            if not gline.supplier.property_purchase_currency_id:
                raise UserError('No currency is set for {}. Please update the partner record, even if NZD.'.format(gline.supplier.name))

            purchase_order = purchase_model.create(
                {
                    "partner_id": gline.supplier.id,
                    "currency_id": gline.supplier.property_purchase_currency_id.id,
                })
            # TODO test if purchase UOM different from stock UOM and adjust quantity, price etc - not an issue for Deeco
            # for now just ignore if we encounter
            for dline in datalines:
                if dline.product.product_tmpl_id.uom_id.id != dline.product.product_tmpl_id.uom_po_id.id:
                    continue
                product_description = ''
                if dline.product.product_tmpl_id.default_code:
                    product_description = "[" + dline.product.product_tmpl_id.default_code + "] "
                product_description += dline.product.name
                buyline_model.create(
                    {
                        "order_id": purchase_order.id,
                        "account": dline.product.categ_id.property_stock_account_input_categ_id.id,
                        "product_id": dline.product.id,
                        "product_qty": dline.order_qty,
                        "name": product_description,
                        "product_uom": dline.supplierinfo.product_uom.id,
                        "date_planned": fields.Date.context_today(self) + timedelta(days=dline.delay),
                        "price_unit": dline.supplierinfo.price,
                    })
                dline.write({"purchase": purchase_order.id})

            _logger.info("Generated purchase={}".format(purchase_order))

        return {"type": "ir.actions.act_window_close"}


class ForecastGeneratePOSupplier(models.TransientModel):
    _name = "forecast.generate.purchase.line"

    wizard = fields.Many2one("forecast.generate.purchase", readonly=True, required=True, ondelete="cascade")
    supplier = fields.Many2one("res.partner", string="Supplier", readonly=True, required=True, ondelete="cascade")
    select = fields.Boolean(string="Select", default=True)
