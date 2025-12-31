# -*- coding: utf-8 -*-

from odoo import fields, models

BORDER_STYLE_SELECTION = [('1', 'Continuous'),
                          ('3', 'Dash'),
                          ('4', 'Dot'),
                          ('6', 'Double')]


class XlsxStyle(models.Model):
    """
    A collection of somewhat orthogonal attributes
    """
    _name = "report.xlsx.style"
    _description = "Excel Styling"

    name = fields.Char("Name", required=True)
    description = fields.Char("Description")

    # Text attributes
    font_name = fields.Many2one(comodel_name='report.xlsx.style.font', string="Optional font-name")
    font_size = fields.Integer("Optional font size")
    bold = fields.Boolean("Bold")
    italic = fields.Boolean("Italic")
    underline = fields.Boolean("Underlined")
    strikeout = fields.Boolean("Strikout")

    # indent

    indent = fields.Integer(string='Indent')

    # Alignment
    h_align = fields.Selection(
        selection=[
            ("left", "Left"),
            ("right", "Right"),
            ("centre", "Centred"),
            ("justify", "Justify"),
            ('fill', 'Fill'),
            ('center_across', 'Centre Across'),
            ('distributed', 'Distributed')
        ], string="Horizonal Alignment", required=True, default="left")

    v_align = fields.Selection(selection=[
        ("top", "Top"),
        ("bottom", "Bottom"),
        ("vcentre", "Centred"),
        ('vjustify', "Justified"),
        ('vdistributed', 'Distributed')
    ], string="Vertical Alignment", required=True, default="bottom")

    # Borders
    border_full = fields.Boolean("Full border")
    border_top = fields.Boolean("Top border")
    border_bottom = fields.Boolean("Bottom border")
    border_left = fields.Boolean("Left border")
    border_right = fields.Boolean("Right border")
    border_full_style = fields.Selection(selection=BORDER_STYLE_SELECTION, string='Full Border Style')
    border_top_style = fields.Selection(selection=BORDER_STYLE_SELECTION, string='Top Border Style')
    border_bottom_style = fields.Selection(selection=BORDER_STYLE_SELECTION, string='Bottom Border Style')
    border_left_style = fields.Selection(selection=BORDER_STYLE_SELECTION, string='Left Border Style')
    border_right_style = fields.Selection(selection=BORDER_STYLE_SELECTION, string='Right Border Style')
    text_wrap = fields.Boolean(string='Text Wrap')

    # Colours
    foreground = fields.Char("Foreground colour")
    background = fields.Char("Background colour")

    def build_format(self, workbook, dollar_format=False):
        """
        @param workbook xlsxwriter.workbook.Workbook
        @return dictionary of worksheet styles keyed by report.xlsx.style.
        """
        xls_format = workbook.add_format()

        if self.font_name:
            xls_format.set_font_name(self.font_name.name)
        if self.font_size:
            xls_format.set_font_size(self.font_size)

        if self.text_wrap:
            xls_format.set_text_wrap()

        if self.indent:
            xls_format.set_indent(self.indent)

        if self.bold:
            xls_format.set_bold()
        if self.italic:
            xls_format.set_italic()
        if self.underline:
            xls_format.set_underline()
        if self.strikeout:
            xls_format.set_font_strikeout()

        if self.border_full:
            xls_format.set_border(int(self.border_full_style))
        else:
            if self.border_top:
                xls_format.set_top(int(self.border_top_style))
            if self.border_bottom:
                xls_format.set_bottom(int(self.border_bottom_style))
            if self.border_right:
                xls_format.set_right(int(self.border_right_style))
            if self.border_left:
                xls_format.set_left(int(self.border_left_style))

        if self.foreground:
            xls_format.set_font_color(self.foreground)
        if self.background:
            xls_format.set_bg_color(self.background)

        if self.v_align:
            xls_format.set_align(self.v_align)
        if self.h_align:
            xls_format.set_align(self.h_align)

        if dollar_format:
            xls_format.set_num_format(dollar_format)

        return xls_format


class ReportXLSXStyleBorderValue(models.Model):
    _name = 'report.xlsx.style.font'
    _description = 'XLSX Font Style'

    name = fields.Char(string='Font')
