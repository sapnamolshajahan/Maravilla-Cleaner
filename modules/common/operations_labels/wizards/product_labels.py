# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductLabels(models.TransientModel):
    """
    Print Labels for Products
    """
    _name = "operations.labels.product.wizard"
    _description = __doc__.strip()

    ################################################################################
    # Field Computations
    ################################################################################
    def _compute_active_model(self):
        for rec in self:
            rec.active_model = 'product.template' if rec.product_tmpl_ids or not rec.product_ids else 'product.product'

    ################################################################################
    # Fields
    ################################################################################
    printer = fields.Many2one("label.printer")
    queue = fields.Char(related="printer.queue")
    label = fields.Many2one("label.printer.template")
    product_ids = fields.Many2many("product.product")
    product_tmpl_ids = fields.Many2many('product.template')
    active_model = fields.Char(compute="_compute_active_model")
    barcoded_only = fields.Boolean("Barcoded Products Only", default=True)

    ################################################################################
    # Technical Methods
    ################################################################################
    def default_get(self, fields_list):

        result = super().default_get(fields_list)

        # default in the printer, if there are any
        for printer in self.env["label.printer"].search([]):
            result["printer"] = printer.id
            break

        return result

    ################################################################################
    # Business Methods
    ################################################################################
    def action_print(self):
        to_print = self.product_tmpl_ids if self.active_model == "product.template" else self.product_ids

        if self.barcoded_only:
            to_print = to_print.filtered(lambda p: p.barcode)
        self.label.print_to_queue(to_print, self.queue)

        return {"type": "ir.actions.act_window_close"}
