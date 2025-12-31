# -*- coding: utf-8 -*-
import json

from odoo.http import content_disposition, request, serialize_exception as _serialize_exception
from odoo.tools import html_escape
from odoo.tools.safe_eval import safe_eval, time
from werkzeug.urls import url_decode

from odoo import http
from odoo.addons.web.controllers.report import ReportController


class ViaductReportController(ReportController):

    @http.route(["/report/download"], type="http", auth="user")
    def report_download(self, data, token):
        """
        Override ReportController.

        Copied in most part from web/controllers/main.py: def report_download.
        The only difference is the construction of the filename
        """
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        if type != "qweb-pdf":
            return super(ViaductReportController, self).report_download(data, token)

        try:
            reportname = url.split("/report/pdf/")[1].split("?")[0]

            docids = None
            if "/" in reportname:
                reportname, docids = reportname.split("/")

            suffix = "pdf"
            if docids:
                # Generic report:
                response = self.report_routes(reportname, docids=docids, converter="pdf")
            else:
                # Particular report:
                data = url_decode(url.split("?")[1]).items()  # decoding the args represented in JSON
                dd = dict(data)
                response = self.report_routes(reportname, converter="pdf", **dd)
                if "options" in dd:
                    dd_opts = json.loads(dd["options"])
                    if "output-type" in dd_opts:
                        suffix = dd_opts["output-type"]

            report = request.env["ir.actions.report"]._get_report_from_name(reportname)
            filename = "{}.{}".format(report.name, suffix)
            if docids:
                ids = [int(x) for x in docids.split(",")]
                obj = request.env[report.model].browse(ids)
                if report.print_report_name and not len(obj) > 1:
                    report_name = safe_eval(report.print_report_name, {"object": obj, "time": time})
                    filename = "{}.{}".format(report_name, suffix)
            response.headers.add("Content-Disposition", content_disposition(filename))
            if filename.endswith('.docx'):
                response.headers.set("Content-Type",
                                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            response.set_cookie("fileToken", token)
            return response

        except Exception as e:

            se = _serialize_exception(e)
            error = {
                "code": 200,
                "message": "Odoo Server Error",
                "data": se
            }
            return request.make_response(html_escape(json.dumps(error)))
