# -*- coding: utf-8 -*-
import logging

from odoo import fields, models
from odoo.exceptions import UserError
from ..printers.datamax import DatamaxConverter
from ..printers.intermec import IntermecConverter
from ..printers.sato import SatoConverter
from ..printers.zebra import ZebraConverter

TYPE_DPL = "dpl"
TYPE_IDP = "idp"
TYPE_PDF = "pdf"
TYPE_SBPL = "sbpl"
TYPE_ZPL = "zpl"

MIMETYPE_BIN = "application/octet-stream"
MIMETYPE_PDF = "application/pdf"
MIMETYPE_JPG = "image/jpeg"
MIMETYPE_PNG = "image/png"

_logger = logging.getLogger(__name__)


class CarrierLabelPrinter(models.Model):
    """
    Carrier Label Printer
    """
    _name = "carrier.label.printer"
    _description = __doc__.strip()
    _inherit = "remote.print.mixin"

    ################################################################################
    # Fields
    ################################################################################
    name = fields.Char("Name", required=True)
    default = fields.Boolean("Default")
    printer_type = fields.Selection([
        (TYPE_DPL, "Datamax Printer"),
        (TYPE_IDP, "Itermec Direct Protocol (Honeywell)"),
        (TYPE_PDF, "PDF Printer"),
        (TYPE_SBPL, "Sato Printer"),
        (TYPE_ZPL, "Zebra Printer"),
    ], default="pdf", required=True)
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")

    ################################################################################
    # Methods
    ################################################################################
    def print_attachment(self, attachment, raise_exceptions=False):
        """
        Filter and convert the attachment to print
        """
        data = self.convert_attachment(attachment)
        if data:
            self.print_label(data, raise_exceptions)
        else:
            _logger.debug(f"ignored mimetype={attachment.mimetype} for printer-type={self.printer_type}")

    def convert_attachment(self, attachment):
        """
        Convert an attachment into a form suitable for the printer queue.
        Override and chain as more printer_type selections are introduced.

        :param attachment: ir.attachment
        :return: bytes or None if not supported
        """
        if self.printer_type == TYPE_DPL:
            return self.convert_dpl(attachment)
        if self.printer_type == TYPE_IDP:
            return self.convert_idp(attachment)
        if self.printer_type == TYPE_PDF:
            return self.convert_pdf(attachment)
        if self.printer_type == TYPE_SBPL:
            return self.convert_sbpl(attachment)
        if self.printer_type == TYPE_ZPL:
            return self.convert_zpl(attachment)
        return None

    def convert_pdf(self, attachment):
        """
        With PDF data, we don't need to do anything, as that's the default.

        :param attachment: ir.attachment
        :return: bytes
        """
        if attachment.mimetype == MIMETYPE_PDF:
            return attachment.raw
        return None

    def convert_dpl(self, attachment):
        """
        We expect image data, which we then wrap up in valid DPL to push to the printer.

        :param attachment: ir.attachment
        :return: bytes
        """
        if attachment.mimetype in (MIMETYPE_JPG, MIMETYPE_PNG):
            converter = DatamaxConverter()
            return converter.print_image(attachment.raw)
        return None

    def convert_idp(self, attachment):
        """
        We expect image data, which we then convert into multiple IDP jobs for the printer.

        :param attachment: ir.attachment
        :return: bytes
        """
        if attachment.mimetype in (MIMETYPE_JPG, MIMETYPE_PNG):
            converter = IntermecConverter()
            return converter.print_image(attachment.raw)
        return None

    def convert_zpl(self, attachment):
        """
        We expect image data, which we then wrap up in valid ZPL to push to the printer.

        :param attachment: ir.attachment
        :return: bytes
        """
        if attachment.mimetype in (MIMETYPE_JPG, MIMETYPE_PNG):
            converter = ZebraConverter()
            return converter.print_image(attachment.raw)
        return None

    def convert_sbpl(self, attachment):
        if attachment.mimetype == MIMETYPE_PDF:
            converter = SatoConverter()
            sbpl = converter.print_pdf(attachment.raw)
            return bytes(sbpl, "utf-8")
        return None

    def print_label(self, data, raise_exceptions=False):
        """
        Push the label to the printer file

        @param data: bytes
        @param raise_exceptions: True if exceptions must be raised in case of errors
        """
        self.ensure_one()
        if not data:
            _logger.info("print_label: Nothing to print, ignored")
            return

        if not self.lp_command(self.name, data) and raise_exceptions:
            raise UserError("Failed to print parcel labels")
