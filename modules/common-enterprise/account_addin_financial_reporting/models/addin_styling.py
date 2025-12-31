# -*- coding: utf-8 -*-

from odoo import fields, models


class AddinStyling(models.Model):
    """
    Styling to be applied to addin.financial.report
    """
    _name = "addin.styling"
    _description = "Set of styles to be applied to a Financial Report"

    name = fields.Char("Name", required=True)

    dollar_rounding = fields.Char("Dollar Rounding Format", default="0", required=True,
                                  help="Excel format for reports values rounded to the dollar")
    no_rounding = fields.Char("No Rounding Format", default="0.00", required=True,
                              help="Excel format for reports values with no rounding")

    default_text = fields.Many2one("report.xlsx.style", string="Default Text Styling")
    default_line_value = fields.Many2one("report.xlsx.style", string="Default Line Value Styling")

    title = fields.Many2one("report.xlsx.style", string="Company Name Styling")
    parameters = fields.Many2one("report.xlsx.style", string="Run Date Styling")
    chart = fields.Many2one("report.xlsx.style", string="Report Name and As At Date Styling")
    column = fields.Many2one("report.xlsx.style", string="Column Name Styling")
    col_width_name = fields.Integer(string="First Col Width", default=20, required=True)
    col_width_desc = fields.Integer(string="Second Col Width", default=50, required=True)
    col_width_value = fields.Integer(string="Subsequent Col Width", default=20, required=True)
    code = fields.Many2one("report.xlsx.style", string="Account Code Styling")
    group_styles = fields.One2many("addin.styling.account.group", "styling")

    def generate_formats(self, rounding, workbook):

        if rounding == "dollar":
            dollar_format = self.dollar_rounding
        else:
            dollar_format = self.no_rounding

        formats = AddinStyleFormats(dollar_format, workbook)

        if self.default_text:
            formats.default_text = self.default_text.build_format(workbook)

            formats.default_dollar = self.default_text.build_format(workbook)
            formats.default_dollar.set_num_format(dollar_format)

            formats.default_percent = self.default_text.build_format(workbook)
            formats.default_percent.set_num_format("0.00%")

        if self.default_line_value:
            formats.default_line_value = self.default_line_value.build_format(workbook)

            formats.default_dollar = self.default_line_value.build_format(workbook)
            formats.default_dollar.set_num_format(dollar_format)

            formats.default_percent = self.default_line_value.build_format(workbook)
            formats.default_percent.set_num_format("0.00%")

        if self.title:
            formats.title = self.title.build_format(workbook)
        if self.parameters:
            formats.parameters = self.parameters.build_format(workbook)
        if self.chart:
            formats.chart = self.chart.build_format(workbook)
        if self.column:
            formats.column = self.column.build_format(workbook)
        if self.code:
            formats.code = self.code.build_format(workbook)

        for group_style in self.group_styles:

            group_format = AddinGroupFormats(formats)

            if group_style.header:
                group_format.header = group_style.header.build_format(workbook)
            if group_style.account:
                group_format.account = group_style.account.build_format(workbook)
            if group_style.footer:
                group_format.footer = group_style.footer.build_format(workbook)

            if group_style.footer_cell:
                group_format.footer_cell = group_style.footer_cell.build_format(workbook, dollar_format)

                group_format.footer_dollar = group_style.footer_cell.build_format(workbook, dollar_format)
                group_format.footer_dollar.set_num_format(dollar_format)

                group_format.footer_percent = group_style.footer_cell.build_format(workbook, dollar_format)
                group_format.footer_percent.set_num_format("0.00%")

            formats.group[group_style.name] = group_format

        return formats


class AddinStylingAccountGroup(models.Model):
    """
    Styling to be applied to Account Groups in a report
    """
    _name = "addin.styling.account.group"

    styling = fields.Many2one("addin.styling", required=True, ondelete="cascade")
    name = fields.Integer("Depth", default=0, required=True)
    header = fields.Many2one("report.xlsx.style", string="Header Style")
    account = fields.Many2one("report.xlsx.style", string="Account Name Style")
    footer = fields.Many2one("report.xlsx.style", string="Footer Style")
    footer_cell = fields.Many2one("report.xlsx.style", string="Footer Total Cells")


class AddinStyleFormats():

    def __init__(self, dollar_format, workbook):
        self.default_text = workbook.add_format()
        self.title = self.parameters = self.chart = self.column = self.code = self.default_text

        self.default_dollar = workbook.add_format()
        self.default_dollar.set_num_format(dollar_format)

        self.default_percent = workbook.add_format()
        self.default_percent.set_num_format("0.00%")
        self.default_ratio_align = workbook.add_format()
        self.default_ratio_align.set_align("right")

        self.group = {}

        self._default_group_format = AddinGroupFormats(self)

    def delve(self, depth):
        if depth in self.group:
            return self.group[depth]
        return self._default_group_format


class AddinGroupFormats():

    def __init__(self, base):
        self.header = base.default_text
        self.account = base.code
        self.footer = base.default_text
        self.footer_cell = base.default_dollar

        self.footer_dollar = base.default_dollar
        self.footer_percent = base.default_percent
        self.ratio_align = base.default_ratio_align
