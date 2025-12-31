# -*- coding: utf-8 -*-
from odoo import fields, models


class LabelPrinter(models.Model):
    """
    Named Label Printers
    """
    _name = "label.printer"
    _description = __doc__.strip()
    _sql_constraints = [
        ("unique_label", "unique (name)", "Names must be unique")
    ]

    ###########################################################################
    # Fields
    ###########################################################################
    name = fields.Char("Label Printer", required=True)
    queue = fields.Char("Printer Queue", required=True)
