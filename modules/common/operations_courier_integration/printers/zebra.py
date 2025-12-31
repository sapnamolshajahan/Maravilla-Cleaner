# -*- coding: utf-8 -*-
import math

from .abstract_converter import AbstractConverter


class ZebraConverter(AbstractConverter):
    """
    Converts input to something suitable to be used on a Zebra Label Printer
    """

    def print_image(self, bytes_image):
        """
        Use ZPL2 ^GF command to display an image.

        This requires a bitmap conversion and ASCII encoding.

        :param bytes_image: byte array of image data
        :return: bytestream of ZPL suitable to be printed on a Zebra Label Printer.
        """
        image = self.cook_image(bytes_image)
        w, h = image.size
        pixel_list = list(image.getdata(0))  # band-0 is good enough for b&w images
        pixel_count = len(pixel_list)
        if w % 8:
            pixel_pad = [256] * (8 - w % 8)  # padding to align row-pixels to byte
        else:
            pixel_pad = []

        row_bytes = math.ceil(w / 8)
        size = h * row_bytes

        lines_hex = []
        for i in range(0, pixel_count, w):

            # convert a line of (byte-aligned) pixels to a string
            j = i + w
            if j > pixel_count:
                j = pixel_count
            row_pixels = pixel_list[i:j] + pixel_pad
            row = "".join(["0" if p else "1" for p in row_pixels])

            # convert the pixel-bit-string to hex
            last_zero = 0
            line_hex = []
            for i in range(0, len(row), 8):
                hex_str = f"{int(row[i:i + 8], 2):02x}".upper()
                line_hex.append(hex_str)
                if hex_str != "00":
                    last_zero = i // 8 + 1

            # use zero-trimming optimisation
            if last_zero == 0:
                lines_hex.append(",")
            else:
                if last_zero < row_bytes:
                    line_hex = line_hex[0:last_zero] + [","]
                lines_hex.append("".join(line_hex))

        data_ascii = "".join(lines_hex)

        zpl = "^XA\n"
        zpl += "^FO0,0"  # position at 0,0
        zpl += f"^GFA,{size},{size},{row_bytes},{data_ascii}"
        zpl += "^FS\n"
        zpl += "^XZ\n"

        return bytes(zpl, "utf-8")
