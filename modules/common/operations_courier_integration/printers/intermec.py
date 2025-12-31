# -*- coding: utf-8 -*-
import io
import math

from PIL.PcxImagePlugin import logger

from .abstract_converter import AbstractConverter

_logger = logger  # Forces PCX Plugin load


class IntermecConverter(AbstractConverter):
    """
    Converts input to something suitable to be used on Direct-Protocol
    printers; ie Honeywell.

    The Honeywell printers appear to have size-limits on jobs, and
    anything significantly larger than 14K will be silently discarded.

    We get around this by splitting the original image into smaller
    chunks to be uploaded onto the printer, and then have a job
    that prints all the uploaded images.
    """
    LIMIT = 16 * 1024  # bytes. image compression allows a number > 14K

    def print_image(self, bytes_image):
        """
        IDP only accepts PCX files.

        :param bytes_image: byte array of image data
        :return: list of IPL to be submitted
        """
        flat = self.cook_image(bytes_image)
        w, h = flat.size

        chunk_h = math.ceil(self.LIMIT / w * 8)  # make a guess on the number of height-pix for LIMIT
        chunk_h = math.ceil(chunk_h / 50) * 50  # align to 50 pixel height
        chunk_count = math.ceil(h / chunk_h)

        name_prefix = "LABEL"
        jobs = []

        # divide image into chunk_h cropped-images
        for n in range(chunk_count):

            # 0,0 is upper-left corner
            lower = h - n * chunk_h
            upper = lower - chunk_h
            if upper < 0:
                upper = 0

            bounds = (0, upper, w, lower)
            cropped = flat.crop(bounds)
            out = io.BytesIO()
            cropped.save(out, format="pcx")
            pcx_bytes = out.getvalue()
            out.close()

            size = len(pcx_bytes)

            # Upload Image
            upload = f'IMAGE LOAD"{name_prefix}.{n}",{size},""\n'
            jobs.append(upload.encode() + pcx_bytes)

        # Print Commands
        idp_print = "CLIP ON\n"
        for n in range(chunk_count):
            idp_print += f"PRPOS 0,{n * chunk_h}\n"
            idp_print += f'PRIMAGE "{name_prefix}.{n}"\n'
        idp_print += "PRINTFEED\n"
        # Remove uploaded files
        for n in range(chunk_count):
            idp_print += f'REMOVE IMAGE"{name_prefix}.{n}"\n'

        jobs.append(idp_print.encode())
        return jobs
