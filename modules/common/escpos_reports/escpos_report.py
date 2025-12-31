# -*- coding: utf-8 -*-
from .escpos.printer import Dummy
from .xmlescpos_generator import XmlEscPosGenerator

ESCPOS_PROFILE = "escpos_reports.escpos_profile"


class EscPosReport(object):
    """
    Render an ESC/POS report using ESC/POS XML.
    """

    def __init__(self, report):
        self.env = report.env
        self.report = report
        self.profile = self.env.context.get(ESCPOS_PROFILE, None)

    def generate(self, docids, data):
        if not data:
            data = {}

        data.setdefault("report_type", "text")
        data = self.report._get_rendering_context(self.report, docids, data)
        xml_data = self.report._render_template(self.report.sudo().report_name, data).decode("utf-8")

        buffer = Dummy(profile=self.profile)
        generator = XmlEscPosGenerator(buffer)
        generator.generate(xml_data)

        return (buffer.output, "text")
