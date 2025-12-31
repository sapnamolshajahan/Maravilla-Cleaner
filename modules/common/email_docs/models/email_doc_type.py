# -*- coding: utf-8 -*-
from odoo import api, fields, models

NAME_DESC = {
    "invoice": (30, "Invoice"),
    "credit-note": (40, "Credit Note"),
    'marketing': (50, 'Marketing')
}


class EmailDocTypes(models.Model):
    """
    References list of documents that can be email. Non-user modifiable.
    """
    _name = "email.doc.type"
    _description = __doc__
    _sql_constraints = [
        ("unique_name", "unique(name)", "Name already defined")
    ]

    @api.model
    def _name_selection_list(self):
        """
        Return sequenced selection list for use in name-selection.

        :return: list of tuples [(sequence, selection, description)]
        """
        result = []
        for k, v in NAME_DESC.items():
            result.append((v[0], k, v[1]))
        return result

    @api.model
    def _name_selection(self):
        """
        Build ordered selection list for use in name-selection.
        :return: list of tuple [(selection, description)]
        """
        result = []
        for selection in sorted(self._name_selection_list()):
            result.append((selection[1], selection[2]))
        return result

    ###########################################################################
    # Fields
    ###########################################################################
    name = fields.Selection(selection="_name_selection", string="Document", required=True, readonly=True)
    model_name = fields.Char("Odoo Model", required=True, readonly=True)
    template = fields.Many2one("mail.template", string="Covering Email Template", required=True,
                               help="Email template to send with report")
    enabled = fields.Boolean("Enabled", default=True)

    def get_description(self, name):
        """
        Override when adding type names.
        """
        if name in NAME_DESC:
            return NAME_DESC[name][1]
        return ""

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = self.get_description(record.name)
