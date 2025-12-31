# -*- coding: utf-8 -*-
import base64
import io
import logging
import math
import re
import traceback
from xml.etree import ElementTree as ET

from PIL import Image

from .escpos.escpos import Escpos

_logger = logging.getLogger(__name__)


def utfstr(stuff):
    """ converts stuff to string and does without failing if stuff is a utf8 string """
    if isinstance(stuff, str):
        return stuff
    else:
        return str(stuff)


class StyleStack:
    """
    The stylestack is used by the xml escpos serializer to compute the active styles along the xml
    document. Styles are just xml attributes, there is no css mechanism. But the style applied by
    the attributes are inherited by deeper nodes.
    """

    def __init__(self):
        self.stack = []
        self.defaults = {  # default style values
            "align": "left",
            "underline": "off",
            "bold": "off",
            "size": "normal",
            "font": "a",
            "width": 48,
            "indent": 0,
            "tabwidth": 2,
            "bullet": " - ",
            "line-ratio": 0.5,
            "color": "black",

            "value-decimals": 2,
            "value-symbol": "",
            "value-symbol-position": "after",
            "value-autoint": "off",
            "value-decimals-separator": ".",
            "value-thousands-separator": ",",
            "value-width": 0,
        }

        self.types = {  # attribute types, default is string and can be ommitted
            "width": "int",
            "indent": "int",
            "tabwidth": "int",
            "line-ratio": "float",
            "value-decimals": "int",
            "value-width": "int",
        }

        self.cmds = {
            "align": {"left", "right", "center"},
            "underline": {"off", "on", "double"},
            "bold": {"off", "on"},
            "font": {"a", "b", "c"},
            "size": {"normal", "double-height", "double-width", "double"},
            "color": {"black", "red"},
        }

        self.push(self.defaults)

    def get(self, style):
        """ what's the value of a style at the current stack level"""
        level = len(self.stack) - 1
        while level >= 0:
            if style in self.stack[level]:
                return self.stack[level][style]
            else:
                level = level - 1
        return None

    def enforce_type(self, attr, val):
        """converts a value to the attribute's type"""
        if not attr in self.types:
            return utfstr(val)
        elif self.types[attr] == "int":
            return int(float(val))
        elif self.types[attr] == "float":
            return float(val)
        else:
            return utfstr(val)

    def push(self, style):
        """push a new level on the stack with a style dictionnary containing style:value pairs"""
        _style = {}
        for attr in style:
            if attr in self.cmds and not style[attr] in self.cmds[attr]:
                _logger.warning(f"ignoring invalid value: {style[attr]} for style {attr}")
            else:
                _style[attr] = self.enforce_type(attr, style[attr])
        self.stack.append(_style)

    def set(self, style):
        """overrides style values at the current stack level"""
        _style = {}
        for attr in style:
            if attr in self.cmds and not style[attr] in self.cmds[attr]:
                _logger.warning(f"ignoring invalid value: {style[attr]} for style {attr}")
            else:
                self.stack[-1][attr] = self.enforce_type(attr, style[attr])

    def pop(self):
        """ pop a style stack level """
        if len(self.stack) > 1:
            self.stack = self.stack[:-1]

    def output_styles(self, escpos: Escpos):
        """
        Output the current style to the Escpos device.

        :param escpos: output device
        :return list: list of current style attributes
        """

        # Sizing
        double_width = False
        double_height = False
        size = self.get("size")
        if size == "double-height":
            double_height = True
        elif size == "double-width":
            double_width = True
        elif size == "double":
            double_height = double_width = True

        # Bold
        bold = False
        attr = self.get("bold")
        if attr == "on":
            bold = True

        underline = 0
        attr = self.get("underline")
        if attr == "on":
            underline = 1
        elif attr == "double":
            underline = 2

        escpos.set(
            align=self.get("align"),
            font=self.get("font"),
            bold=bold, underline=underline,
            double_width=double_width, double_height=double_height)


class XmlSerializer:
    """
    Converts the xml inline / block tree structure to a string,
    keeping track of newlines and spacings.
    The string is outputted asap to the provided escpos driver.
    """

    def __init__(self, escpos: Escpos):
        self.escpos = escpos
        self.stack = ["block"]
        self.dirty = False

    def start_inline(self, stylestack=None):
        """ starts an inline entity with an optional style definition """
        self.stack.append("inline")
        if self.dirty:
            self.escpos.text(" ")
        if stylestack:
            self.style(stylestack)

    def start_block(self, stylestack=None):
        """ starts a block entity with an optional style definition """
        if self.dirty:
            self.escpos.ln()
            self.dirty = False
        self.stack.append("block")
        if stylestack:
            self.style(stylestack)

    def end_entity(self):
        """ ends the entity definition. (but does not cancel the active style!) """
        if self.stack[-1] == 'block' and self.dirty:
            self.escpos.ln()
            self.dirty = False
        if len(self.stack) > 1:
            self.stack = self.stack[:-1]

    def pre(self, text):
        """ puts a string of text in the entity keeping the whitespace intact """
        if text:
            self.escpos.text(text)
            self.dirty = True

    def text(self, text):
        """ puts text in the entity. Whitespace and newlines are stripped to single spaces. """
        if text:
            text = utfstr(text)
            text = text.strip()
            text = re.sub('\s+', ' ', text)
            if text:
                self.dirty = True
                self.escpos.text(text)

    def linebreak(self):
        """ inserts a linebreak in the entity """
        self.dirty = False
        self.escpos.ln()

    def style(self, stylestack: StyleStack):
        """ apply a style to the entity (only applies to content added after the definition) """
        stylestack.output_styles(self.escpos)

    def raw(self, raw):
        """ puts raw text or escpos command in the entity without affecting the state of the serializer """
        self.escpos.text(raw)


class XmlLineSerializer:
    """
    This is used to convert a xml tree into a single line, with a left and a right part.
    The content is not output to escpos directly, and is intended to be fedback to the
    XmlSerializer as the content of a block entity.
    """

    def __init__(self, indent=0, tabwidth=2, width=48, ratio=0.5):
        self.tabwidth = tabwidth
        self.indent = indent
        self.width = max(0, width - int(tabwidth * indent))
        self.lwidth = int(self.width * ratio)
        self.rwidth = max(0, self.width - self.lwidth)
        self.clwidth = 0
        self.crwidth = 0
        self.lbuffer = ''
        self.rbuffer = ''
        self.left = True

    def _txt(self, txt):
        if self.left:
            if self.clwidth < self.lwidth:
                txt = txt[:max(0, self.lwidth - self.clwidth)]
                self.lbuffer += txt
                self.clwidth += len(txt)
        else:
            if self.crwidth < self.rwidth:
                txt = txt[:max(0, self.rwidth - self.crwidth)]
                self.rbuffer += txt
                self.crwidth += len(txt)

    def start_inline(self, stylestack=None):
        if (self.left and self.clwidth) or (not self.left and self.crwidth):
            self._txt(' ')

    def start_block(self, stylestack=None):
        self.start_inline(stylestack)

    def end_entity(self):
        pass

    def pre(self, text):
        if text:
            self._txt(text)

    def text(self, text):
        if text:
            text = utfstr(text)
            text = text.strip()
            text = re.sub('\s+', ' ', text)
            if text:
                self._txt(text)

    def linebreak(self):
        pass

    def style(self, stylestack):
        pass

    def raw(self, raw):
        pass

    def start_right(self):
        self.left = False

    def get_line(self):
        return ' ' * self.indent * self.tabwidth + self.lbuffer + ' ' * (
                self.width - self.clwidth - self.crwidth) + self.rbuffer


class XmlEscPosGenerator(object):
    """
    XML ESC/POS
    """

    def __init__(self, escpos: Escpos):
        self.escpos = escpos

    def print_image_data(self, image_attr):
        """
        Print the image-data attribute onto the Escpos device.

        :param image_attr: image-data from html attribute
        :return:
        """
        marker = ";base64,"
        marker_pt = image_attr.find(marker)
        if marker_pt < 0:
            _logger.error(f"invalid image-data attribute: {image_attr}")
            return
        image_b64 = image_attr[marker_pt + len(marker):]
        image_bytes = base64.b64decode(image_b64.encode())
        buf = io.BytesIO(image_bytes)
        self.escpos.image(Image.open(buf))

    def generate(self, xml):
        """
        Parse and generate output onto the Escpos device.
        """

        def strclean(string):
            if not string:
                string = ''
            string = string.strip()
            string = re.sub('\s+', ' ', string)
            return string

        def format_value(value, decimals=3, width=0, decimals_separator='.', thousands_separator=',', autoint=False,
                         symbol='', position='after'):
            decimals = max(0, int(decimals))
            width = max(0, int(width))
            value = float(value)

            if autoint and math.floor(value) == value:
                decimals = 0
            if width == 0:
                width = ''

            if thousands_separator:
                formatstr = "{:" + str(width) + ",." + str(decimals) + "f}"
            else:
                formatstr = "{:" + str(width) + "." + str(decimals) + "f}"

            ret = formatstr.format(value)
            ret = ret.replace(',', 'COMMA')
            ret = ret.replace('.', 'DOT')
            ret = ret.replace('COMMA', thousands_separator)
            ret = ret.replace('DOT', decimals_separator)

            if symbol:
                if position == 'after':
                    ret = ret + symbol
                else:
                    ret = symbol + ret
            return ret

        def print_elem(stylestack, serializer, elem, indent=0):

            elem_styles = {
                "h1": {"bold": "on", "size": "double"},
                "h2": {"size": "double"},
                "h3": {"bold": "on", "size": "double-height"},
                "h4": {"size": "double-height"},
                "h5": {"bold": "on"},
                "em": {"font": "b"},
                "b": {"bold": "on"},
            }

            stylestack.push({})
            if elem.tag in elem_styles:
                stylestack.set(elem_styles[elem.tag])
            stylestack.set(elem.attrib)

            if elem.tag in (
                    "escpos",  # top-level (new)
                    "p", "div",
                    "section", "article", "header", "footer", "li",
                    "h1", "h2", "h3", "h4", "h5"):
                serializer.start_block(stylestack)
                serializer.text(elem.text)
                for child in elem:
                    print_elem(stylestack, serializer, child)
                    serializer.start_inline(stylestack)
                    serializer.text(child.tail)
                    serializer.end_entity()
                serializer.end_entity()

            elif elem.tag in ("span", "em", "b", "left", "right"):
                serializer.start_inline(stylestack)
                serializer.text(elem.text)
                for child in elem:
                    print_elem(stylestack, serializer, child)
                    serializer.start_inline(stylestack)
                    serializer.text(child.tail)
                    serializer.end_entity()
                serializer.end_entity()

            elif elem.tag == "value":
                serializer.start_inline(stylestack)
                serializer.pre(format_value(
                    elem.text,
                    decimals=stylestack.get("value-decimals"),
                    width=stylestack.get("value-width"),
                    decimals_separator=stylestack.get("value-decimals-separator"),
                    thousands_separator=stylestack.get("value-thousands-separator"),
                    autoint=(stylestack.get("value-autoint") == "on"),
                    symbol=stylestack.get("value-symbol"),
                    position=stylestack.get("value-symbol-position")
                ))
                serializer.end_entity()

            elif elem.tag == "line":
                width = stylestack.get("width")
                if stylestack.get("size") in ("double", "double-width"):
                    width = width / 2

                lineserializer = XmlLineSerializer(stylestack.get("indent") + indent, stylestack.get("tabwidth"), width,
                                                   stylestack.get("line-ratio"))
                serializer.start_block(stylestack)
                for child in elem:
                    if child.tag == 'left':
                        print_elem(stylestack, lineserializer, child, indent=indent)
                    elif child.tag == 'right':
                        lineserializer.start_right()
                        print_elem(stylestack, lineserializer, child, indent=indent)
                serializer.pre(lineserializer.get_line())
                serializer.end_entity()

            elif elem.tag == 'ul':
                serializer.start_block(stylestack)
                bullet = stylestack.get('bullet')
                for child in elem:
                    if child.tag == 'li':
                        serializer.style(stylestack)
                        serializer.raw(' ' * indent * stylestack.get('tabwidth') + bullet)
                    print_elem(stylestack, serializer, child, indent=indent + 1)
                serializer.end_entity()

            elif elem.tag == 'ol':
                cwidth = len(str(len(elem))) + 2
                i = 1
                serializer.start_block(stylestack)
                for child in elem:
                    if child.tag == 'li':
                        serializer.style(stylestack)
                        serializer.raw(' ' * indent * stylestack.get('tabwidth') + ' ' + (str(i) + ')').ljust(cwidth))
                        i = i + 1
                    print_elem(stylestack, serializer, child, indent=indent + 1)
                serializer.end_entity()

            elif elem.tag == 'pre':
                serializer.start_block(stylestack)
                serializer.pre(elem.text)
                serializer.end_entity()

            elif elem.tag == 'hr':
                width = stylestack.get('width')
                if stylestack.get('size') in ('double', 'double-width'):
                    width = width / 2
                serializer.start_block(stylestack)
                serializer.text('-' * width)
                serializer.end_entity()

            elif elem.tag == 'br':
                serializer.linebreak()

            elif elem.tag == 'img':
                if 'src' in elem.attrib and 'data:' in elem.attrib['src']:
                    self.print_image_data(elem.attrib["src"])

            elif elem.tag == 'barcode' and 'encoding' in elem.attrib:
                serializer.start_block(stylestack)
                self.escpos.barcode(strclean(elem.text), elem.attrib['encoding'])
                serializer.end_entity()

            elif elem.tag == 'cut':
                self.escpos.cut()
            elif elem.tag == 'partialcut':
                self.escpos.cut(mode="PART")
            elif elem.tag == 'cashdraw':
                self.escpos.cashdraw(2)
                self.escpos.cashdraw(5)

            stylestack.pop()

        try:
            stylestack = StyleStack()
            serializer = XmlSerializer(self.escpos)
            root = ET.fromstring(xml.encode("utf-8"))

            stylestack.output_styles(self.escpos)

            print_elem(stylestack, serializer, root)

            if "open-cashdrawer" in root.attrib and root.attrib["open-cashdrawer"] == "true":
                self.escpos.cashdraw(2)
                self.escpos.cashdraw(5)
            if not 'cut' in root.attrib or root.attrib['cut'] == 'true':
                self.escpos.cut()

        except Exception as e:
            errmsg = str(e) + '\n' + '-' * 48 + '\n' + traceback.format_exc() + '-' * 48
            self.escpos.textln(errmsg)
            self.escpos.cut()

            raise e
