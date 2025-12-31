# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from ..printer import LabelPrinter

_logger = logging.getLogger(__name__)

# Printer Driver Notes (HTML)
FLAVOUR_NOTES = {
    "dpl": "<p><b>Note:</b></p>"
           "<ul>"
           "<li>Newlines are auto-converted to CR</li>"
           "<li><b><tt>{&lt;img()&gt;}</tt></b>: returns data-lines for &lt;STX&gt;I{{module}}Ab{{name}}</li>"
           "</ul>",
    "sbpl": "<p><b>Notes:</b></p>"
            "<ul>"
            "<li>For clarity, start each ESC command on a newline</li>"
            "<li>All lines will be concatenated; ie: newlines are removed from the template</li>"
            "</ulL",
    "zpl": "<p><b>Notes:</b></p>"
           "<ul>"
           "<li><b><tt>{&lt;img()&gt;}</tt></b>: returns \"size,size,row,data\" for ^GFA only, eg: <tt>^GFA,{&lt;img:obj.logo&gt;}</tt></li>"
           "</ul>",
}


class Label(models.Model):
    """
    Label Template
    """
    _name = "label.printer.template"
    _description = __doc__.strip()
    _inherit = "remote.print.mixin"
    _order = "state, sequence, id desc"

    ##################################################################################
    # Field Computations
    ##################################################################################
    @api.depends("flavour")
    def _flavour_notes(self):
        for rec in self:
            rec.flavour_notes = FLAVOUR_NOTES.get(rec.flavour, "")

    ##################################################################################
    # Fields
    ##################################################################################
    sequence = fields.Integer('Sequence', default=20, required=True)
    name = fields.Char("Name", required=True)
    description = fields.Text("Description")
    flavour = fields.Selection(
        [
            ("dpl", "Datamax"),
            ("idp", "Honeywell"),  # Intermec Direct Protocol
            ("sbpl", "Sato"),
            ("tspl", "TSC"),
            ("zpl", "Zebra"),
            ("escpos", "ESC/POS"),
        ], default="zpl", required=True)
    flavour_notes = fields.Html(compute="_flavour_notes")
    model = fields.Char("Model Name", required=True)
    content = fields.Text("Label Template")
    state = fields.Selection(
        [
            ("a-active", "Active"),  # use a prefix to help with sorting
            ("b-draft", "Draft"),
            ("c-archived", "Archived"),
        ], default="b-draft", required=True, copy=False)

    ##################################################################################
    # Business Methods
    ##################################################################################
    @api.model
    def current(self, name):
        """
        Return the latest active template with the given name.

        :return:
        """
        return self.search(
            [
                ("name", "=", name),
                ("state", "=", "a-active"),
            ], order="id desc", limit=1)

    def render(self, record, values):
        """
        Render label using the record.

        :param record: singleton
        :param values: dict of additional values to be used in rendering the label.
        """
        record.ensure_one()

        printer = LabelPrinter.driver(self.flavour)
        rvalues = dict(values)
        rvalues.update(
            {
                "obj": record,
                "context": self.env.context,
            })
        return printer.render(self.content, rvalues)

    def print_to_queue(self, records, queue: str, copies=1, values=None):
        """
        Render and Print to given queue.

        :param records: recordset
        :param queue: queue name
        :param values: dict to pass to the template
        """
        if records._name != self.model:
            raise Exception(f"Label Template '{self.name}' expects: {self.model}, but got: {records._name}")
        if not values:
            values = {}

        for rec in records:
            self.lp_command(queue, self.render(rec, values), copies)

    def action_print_label(self):
        """
        Wizard to print a label manually.
        """
        wizard = self.env["label.printer.wizard"].create(
            {
                "template": self.id,
            })

        return {
            "name": wizard._description,
            "view_mode": "form",
            "res_model": wizard._name,
            "type": "ir.actions.act_window",
            "res_id": wizard.id,
            "target": "new",
        }
