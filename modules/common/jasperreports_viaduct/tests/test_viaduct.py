# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import tagged, TransactionCase
from odoo.tools import config
from ..config import CONFIG_VIADUCT_URL, CONFIG_ODOO_URL
from ..controllers.viaduct_service import SERVICE_URL
from ..viaduct import ViaductReport


@tagged("common", "jasperreports_viaduct")
class ViaductTest(TransactionCase):

    def test_init(self):
        report = self.env["ir.actions.report"].new(
            {
                "name": "Test",
                "report_type": "qweb-pdf",
            })
        viaduct = ViaductReport(report)
        self.assertEqual(report, viaduct.report, "Mismatched Viaduct report name")

    def test_proxy_args(self):
        report = self.env["ir.actions.report"]
        viaduct = ViaductReport(report)
        proxy_url, odoo_config, pg_config = viaduct._get_proxy_args()

        self.assertEqual(f"{CONFIG_VIADUCT_URL}/jasperreports-viaduct18/api", proxy_url, "Proxy URL mismatched")

        self.assertEqual(self.cr.dbname, pg_config["db"], "Mismatched db-name")
        self.assertEqual(config["db_user"], pg_config["login"], "Mismatched db user")
        self.assertEqual(
            f"{CONFIG_ODOO_URL}{SERVICE_URL}{self.env.cr.dbname}",
            odoo_config["url"],
            "Mismatched url")

    def test_find_jrxml_file(self):
        report_file = "jasperreports_viaduct/reports/viaduct-test-report.jrxml"
        report = self.env["ir.actions.report"].new(
            {
                "name": "Test",
                "report_type": "qweb-pdf",
                "report_file": report_file,
            })
        viaduct = ViaductReport(report)
        path = viaduct._find_jrxml_file()
        self.assertTrue(path.endswith(report_file), "Didn't find " + report_file)

    def test_find_jrxml_file_fail(self):
        report_file = "non-existent"
        report = self.env["ir.actions.report"].new(
            {
                "name": "Test",
                "report_type": "qweb-pdf",
                "report_file": report_file,
            })
        viaduct = ViaductReport(report)
        with self.assertRaises(UserError) as ex:
            viaduct._find_jrxml_file()
            self.assertTrue(str(ex).endswith(report_file))

    def test_create_fail(self):
        report_file = "jasperreports_viaduct/reports/viaduct-test-report.jrxml"
        report = self.env["ir.actions.report"].new(
            {
                "name": "Test",
                "report_type": "qweb-pdf",
                "report_file": report_file,
            })
        viaduct = ViaductReport(report)
        result = viaduct.create([], {})
        self.assertEqual((False, False), result, "expected empty result")
