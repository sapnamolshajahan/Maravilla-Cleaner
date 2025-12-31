# -*- coding: utf-8 -*-
import math

from .abstract_converter import AbstractConverter


class DatamaxConverter(AbstractConverter):
    """
    Converts input to something suitable to be used on a Zebra Label Printer
    """

    def build_lines_hex(self, image):
        """
        :return: lines of hex
        """
        w, h = image.size
        pixel_list = list(image.getdata(0))  # band-0 is good enough for b&w images
        pixel_count = len(pixel_list)
        if w % 8:
            pixel_pad = [256] * (8 - w % 8)  # padding to align row-pixels to byte
        else:
            pixel_pad = []

        row_bytes = math.ceil(w / 8)
        row_header = f"80{row_bytes:02x}".upper()

        lines_hex = []
        for i in range(0, pixel_count, w):

            # convert a line of (byte-aligned) pixels to a string
            j = i + w
            if j > pixel_count:
                j = pixel_count
            row_pixels = pixel_list[i:j] + pixel_pad
            row = "".join(["0" if p else "1" for p in row_pixels])

            # convert the pixel-bit-string to hex
            line_hex = []
            for i in range(0, len(row), 8):
                hex_str = f"{int(row[i:i + 8], 2):02x}".upper()
                line_hex.append(hex_str)

            row_rec = row_header + "".join(line_hex)
            lines_hex.append(row_rec)

        lines_hex.reverse()
        return lines_hex

    def print_image(self, bytes_image):
        """
        Use DPL <STX>I to load and print a label.

        This requires a conversion to ASCII encoding.

        :param bytes_image: byte array of image data
        :return: bytestream of DPL
        """
        flat = self.cook_image(bytes_image)
        lines_hex = self.build_lines_hex(flat)
        data_ascii = "\r".join(lines_hex)

        module = "D"  # transient storage
        name = "LABEL"

        dpl = f"{self.STX}q{module}\r"
        dpl += f"{self.STX}I{module}AF{name}\r"
        dpl += f"{data_ascii}\r"
        dpl += "FFFF\r"
        dpl += f"{self.STX}L\r"
        dpl += f"1Y1100000000000{name}\r"
        dpl += "E\r"

        return bytes(dpl, "utf-8")
