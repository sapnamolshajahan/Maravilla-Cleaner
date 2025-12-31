# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class PrintLabel(models.TransientModel):
    """
    Print a Label
    """
    _name = "label.printer.wizard"
    _description = __doc__.strip()

    ################################################################################
    # Fields
    ################################################################################
    template = fields.Many2one("label.printer.template", required=True, readonly=True, ondelete="cascade")
    printer = fields.Many2one("label.printer")
    queue = fields.Char("Queue name", related="printer.queue")
    model = fields.Char(related="template.model")
    record = fields.Many2oneReference(model_field="model")

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
    # Methods
    ################################################################################
    def button_print(self):
        if not self.printer:
            raise UserError("Label Printer needs to be specified")
        if not self.record:
            raise UserError("Record to Print required")

        records = self.env[self.model].browse(self.record)
        self.template.print_to_queue(records, self.queue)

        return {"type": "ir.actions.act_window_close"}
