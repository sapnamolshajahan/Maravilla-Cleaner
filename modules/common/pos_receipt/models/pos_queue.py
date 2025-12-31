# -*- coding: utf-8 -*-
from odoo import _, api, models, fields
from odoo.addons.escpos_reports.escpos.capabilities import PROFILES
from odoo.exceptions import ValidationError


class PosQueue(models.Model):
    """
    ESC/POS queues for Point of Sale
    """
    _name = "pos.queue.escpos"
    _order = "name"

    ################################################################################
    # Fields
    ################################################################################
    name = fields.Char("System queue name", required=True)
    escpos_profile = fields.Selection(selection="_profile_selections", string="ESC/POS Profile",
                                      default="default", required=True)

    _unique_name = models.Constraint(
        'unique (name)',
        'Queue name already defined.',
    )

    @api.model
    def _profile_selections(self):
        """
        Dynamically extract the list of ESC/POS profiles from python-escpos
        for the selection list.

        :return: list of tuple [(selection, description)]
        """
        result = []
        for k, v in PROFILES.items():
            result.append((k, v.get("name", "?")))
        return result
