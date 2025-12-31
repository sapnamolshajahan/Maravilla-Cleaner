# -*- coding: utf-8 -*-
import base64
import io
import math
import re
from uuid import uuid4

import dateutil.relativedelta as relativedelta
from PIL import Image
from jinja2 import Template

from odoo.tools import safe_eval

#
# - provide minimal set of functions for use in templates
LABEL_TEMPLATE_FUNCTIONS = {
    "str": str,
    "datetime": safe_eval.datetime,
    "len": len,
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "filter": filter,
    "map": map,
    "relativedelta": relativedelta.relativedelta,
    "round": round,
    "hasattr": hasattr,
}


class LabelPrinter():
    """
    Abstract Printer
    """

    # Standard Printer Keywords
    NUL = "\000"
    SOH = "\001"
    STX = "\002"
    ETX = "\003"
    LF = "\012"  # newline
    CR = "\015"  # carriage return
    ESC = "\033"
    GS = "\035"

    @staticmethod
    def driver(name):

        if name == "dpl":
            return DplPrinter()
        if name == "escpos":
            return EscPosPrinter()
        if name == "idp":
            return IntermecPrinter()
        if name == "sbpl":
            return SatoPrinter()
        if name == "tspl":
            return TscPrinter()
        if name == "zpl":
            return ZplPrinter()
        raise Exception(f"Unsupported Label Printer {name}")

    def cook_template(self, raw: str) -> str:
        """
        Allow sub-classes to modify template prior to rendering.

        :param template:
        :return:
        """
        return raw

    def render(self, raw: str, in_values) -> bytes:

        # Embed the driver for rendering
        driver_name = f"_{uuid4().hex}"
        values = dict(in_values)
        values[driver_name] = self

        exprs = self.eval_printer(driver_name, raw)
        for expr, value in exprs.items():
            raw = raw.replace(expr, value)

        jinjt = Template(raw, trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
        jinjt.globals.update(LABEL_TEMPLATE_FUNCTIONS)
        render = jinjt.render(values)

        result = self.cook_template(render)

        return result.encode("utf-8")

    def eval_printer(self, driver_name: str, raw: str):
        """
        Evaluate Printer Specific Expressions:
        - {<key>}
        - {<key:expression>}

        :param key:
        :param values:
        :return:
        """
        exprs = {}

        for m in re.finditer(r"{<(.*?)>}", raw, re.DOTALL):
            k_expr = m.group(0)
            if k_expr in exprs:
                continue

            word = m.group(1)
            words = word.split(":")
            if len(words) == 2:
                exprs[k_expr] = "{{" + f"{driver_name}.{words[0]}({words[1]})" + "}}"
            else:
                exprs[k_expr] = "{{" + f"{driver_name}.{word}" + "}}"

        return exprs

    def img(self, field_data: bytes) -> str:
        """
        Convert image bytstream to printer-specific output string
        :param field_data: field binary, ie: base64 encoded bytes.
        """
        return "UNIMPLEMENTED"


class EscPosPrinter(LabelPrinter):
    """
    Epsom
    """


class IntermecPrinter(LabelPrinter):
    """
    Honeywell, using Intermec Direct Protocol
    """


class SatoPrinter(LabelPrinter):
    """
    SATO
    """

    def cook_template(self, raw: str) -> str:
        """
        Strip all newlines from the template.
        :return:
        """
        return raw.replace("\n", "")


class TscPrinter(LabelPrinter):
    """
    TSC Printronix
    """


class DplPrinter(LabelPrinter):
    """
    Datamax
    """

    def cook_template(self, original: str) -> str:
        """
        Convert Command Terminators from newline to carriage-return.
        Add trailing "\r" if required

        :return:
        """
        cooked = original.replace("\n", "\r")
        if cooked[-1] == "\r":
            return cooked
        return cooked + "\r"

    def img(self, field_data: bytes) -> str:
        """
        Convert image bytstream to string for <STX>I{{module}}AF{{name}}

        :param field_data: Binary field-data, ie: base64 encoded bytes
        :return: Datamax ASCII for <STX>I{{module}}AF{{name}}
        """
        raw = base64.b64decode(field_data)
        image = Image.open(io.BytesIO(raw))
        image = image.convert("1", dither=Image.Dither.NONE)  # 1-bit pixels, stored with one pixel per byte
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

        data_ascii = "\r".join(lines_hex)
        return data_ascii + "\rFFFF"


class ZplPrinter(LabelPrinter):
    """
    Zebra Technologies
    """

    def img(self, field_data: bytes) -> str:
        """
        Convert image bytstream to string for ^GFA.

        :param field_data: Binary field-data, ie: base64 encoded bytes
        :return: string suitable for data-parameter in ^GFA
        """
        raw = base64.b64decode(field_data)
        image = Image.open(io.BytesIO(raw))
        image = image.convert("1", dither=Image.Dither.NONE)  # 1-bit pixels, stored with one pixel per byte
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
        return f"{size},{size},{row_bytes},{data_ascii}"
