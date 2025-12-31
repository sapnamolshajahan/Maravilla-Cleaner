# -*- coding: utf-8 -*-
import io
import math

from PIL import Image

from ..config import LABEL_WIDTH


class AbstractConverter():
    """
    Superclass for Converters
    """

    # Standard Printer Keywords
    SOH = "\001"
    STX = "\002"
    ETX = "\003"
    LF = "\012"  # newline
    CR = "\015"  # carriage return
    ESC = "\033"

    def cook_image(self, bytes_image):
        """
        Flatten and possibly resize an image-bytestream.

        :param bytes_image: byte array of image data
        :return: PIL Image
        """
        image = Image.open(io.BytesIO(bytes_image))
        flat = image.convert("1", dither=Image.Dither.NONE)  # 1-bit pixels, stored with one pixel per byte

        if not LABEL_WIDTH:
            return flat

        w, h = flat.size
        r_h = math.ceil(h / w * LABEL_WIDTH)
        return flat.resize((LABEL_WIDTH, r_h))
