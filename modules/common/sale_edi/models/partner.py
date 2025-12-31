# -*- coding: utf-8 -*-
import logging

from odoo import fields, models
from odoo.exceptions import UserError
from .itm_generator import ItmEDI
from .mitre10_generator import Mitre10EDI
from .buildlink_generator import BuildLinkEDI

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    """
    Extend to include EDI fields.

    "edi_generator" is a dropdown selector for EDI generators. Sub-modules
    are expected to add to the selection list and create a generator as required.
    """
    _inherit = "res.partner"

    ###########################################################################
    # Fields
    ###########################################################################
    edi_email = fields.Char("EDI Email")
    edi_reference = fields.Char("EDI Reference", help="Partner's EDI code for us")
    edi_generator = fields.Selection(
        [
            ("mitre10", "Mitre 10"),
            ("itm", "ITM"),
            ("buildlink", "BuildLink"),
            ("bunnings", "Bunnings"),
        ],
        string="EDI Format",
        ondelete={
            "mitre10": "set null",
            "itm": "set null",
            "buildlink": "set null",
            "bunnings": "set null",
        },
    )
    supplier_code = fields.Char("Supplier code")
    store_code = fields.Char(string='Store Code')


    def get_generator(self):
        """
        Subclasses should override and inspect res.partner:edi_generator, returning
        the appropriate EDIGenerator sub-class.
        """
        if self.edi_generator == "mitre10":
            return Mitre10EDI(self.env)
        if self.edi_generator == "itm":
            return ItmEDI(self.env)
        if self.edi_generator == "buildlink":
            return BuildLinkEDI(self.env)

        raise UserError("No generator for {} found".format(self.edi_generator))

    def generate_edi(self, invoices):
        """
        @param invoices - record-set of invoices
        """
        if not self.edi_email:
            _logger.warning("EDI unsent, no EDI email address found for {}".format(self.name))
            return
        self.get_generator().send_email(self, invoices)


    def is_bunnings_partner(self):
        """Check if partner OR its parent has edi_generator = bunnings"""
        if not self:
            return False
        self.ensure_one()
        child_gen = (self.edi_generator or "").strip().lower()
        parent_gen = (self.parent_id.edi_generator or "").strip().lower()
        return child_gen == "bunnings" or parent_gen == "bunnings"
