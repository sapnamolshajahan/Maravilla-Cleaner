# -*- coding: utf-8 -*-
import math

from PIL import ImageOps
from pdf2image import convert_from_bytes

from .abstract_converter import AbstractConverter


class SatoConverter(AbstractConverter):
    """
    Converts input to something suitable to be used on a Sato Label Printer
    """

    def print_image(self, bytes_image):
        """
        This requires a bitmap conversion and ASCII encoding.

        :param bytes_image: byte array of image data
        :return: a string suitable to be printed on a SATO Label Printer.
        """
        image = self.cook_image(bytes_image)
        w, h = image.size
        inverted = ImageOps.invert(image)

        sbpl = "\033A"
        sbpl += "\033V0005\033H0005\033"
        sbpl += f"GH{w:03}{h:03}{inverted.tobytes().hex().upper()}"
        sbpl += f"\033Q1"
        sbpl += "\033Z"

        return sbpl

    def print_pdf(self, bytes_pdf):
        images = convert_from_bytes(bytes_pdf, grayscale=True)
        height = math.ceil(images[0].height / 8)
        width = math.ceil(images[0].width / 8)
        # only print the first page for now
        img = images[0].resize((width * 8, height * 8))
        img = img.convert('1')
        img = ImageOps.invert(img)

        sbpl = "\033A"
        sbpl += "\033V0005\033H0005\033"
        sbpl += f"GH{width:03}{height:03}{img.tobytes().hex().upper()}"
        sbpl += f"\033Q1"
        sbpl += "\033Z"

        return sbpl
