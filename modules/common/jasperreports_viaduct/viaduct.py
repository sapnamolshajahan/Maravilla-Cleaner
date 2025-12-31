# -*- coding: utf-8 -*-
import base64
import json
import logging
import os

import urllib3
from urllib3.exceptions import HTTPError

import odoo.release
from odoo.api import Environment
from odoo.exceptions import UserError
from odoo.modules.registry import Registry
from odoo.tools import config
from .config import CONFIG_VIADUCT_URL, CONFIG_DB_USER, CONFIG_DB_HOST, CONFIG_DB_PORT, CONFIG_DB_PASSWORD, \
    CONFIG_ODOO_URL
from .controllers import viaduct_service

DEFAULT_OUTPUT_TYPE = "pdf"

VIADUCT_DATA_PARAMETERS = "viaduct-parameters"

_logger = logging.getLogger(__name__)

addons_paths = config["addons_path"]
if isinstance(addons_paths, str):
    ADDONS_PATHS = addons_paths.split(",")
else:
    ADDONS_PATHS = addons_paths


class ViaductReport(object):

    def __init__(self, report):
        self.env = report.env
        self.report = report

    def _get_proxy_args(self):
        """Return the arguments needed by Viaduct server proxy.

        @return: Tuple with:
            [0]: Has the url for the Viaduct server.
            [1]: Has dict with basic arguments to pass to Viaduct server. This
                 includes the connection settings and report definition but does
                 not include any report parameter values.
        """
        odoo_config = {
            "url": f"{CONFIG_ODOO_URL}{viaduct_service.SERVICE_URL}{self.env.cr.dbname}",
        }
        postgres_config = {
            "host": CONFIG_DB_HOST,
            "port": CONFIG_DB_PORT,
            "db": self.env.cr.dbname,
            "login": CONFIG_DB_USER,
            "password": CONFIG_DB_PASSWORD,
        }
        return f"{CONFIG_VIADUCT_URL}/jasperreports-viaduct{odoo.release.version_info[0]}/api", odoo_config, postgres_config

    def _find_jrxml_file(self):
        """
        :return: absolute-path of report file
        """
        for addons_path in ADDONS_PATHS:
            try:
                path = addons_path + os.sep + self.report.report_file
                os.stat(path)
                return os.path.abspath(path)
            except Exception:
                pass
        raise UserError(f"Could not locate path for file {self.report.report_file}")

    def session_setup(self, jrxml_path, report_ids, data):
        """
        Set up the session with new env so that results are committed
        and available for the viaduct web-app
        """
        with Registry.new(self.env.cr.dbname).cursor() as cr:
            env = Environment(cr, self.env.uid, self.env.context)
            viaduct_report = env["viaduct.resource"].inspect(jrxml_path)
            session = env["viaduct.session"].construct(
                self.report, viaduct_report, report_ids,
                data and data.get(VIADUCT_DATA_PARAMETERS, {}))
            cr.commit()
            return session.id

    def create(self, res_ids, data):
        """
            Entry point for report-execution

            @return: (rendered-report, format)
        """
        # Look for report-ids in:
        # 1. data dictionary {ids:...}
        # 2. context {active_ids: ...}
        # 3. doc_ids
        if data and "ids" in data:
            report_ids = data["ids"]
        elif "active_ids" in self.env.context and len(self.env.context["active_ids"]) > len(res_ids or []):
            report_ids = self.env.context["active_ids"]
        else:
            report_ids = res_ids

        if not report_ids:
            _logger.warning("no data-ids found for report-id={0}?".format(self.report.id))
            return (False, False)

        jrxml_path = self._find_jrxml_file()
        proxy_url, odoo_config, postgres_config = self._get_proxy_args()

        output_type = data and data.get("output-type", False) or DEFAULT_OUTPUT_TYPE

        # Add the rest of the parameters for JasperReports
        report_parameters = {}
        report_parameters["viaduct-report-ids"] = report_ids
        _logger.debug("using id-list: " + str(report_ids))
        if data and data.get(VIADUCT_DATA_PARAMETERS, None):
            report_parameters.update(data.get(VIADUCT_DATA_PARAMETERS))

        # Create and store session info
        session_id = self.session_setup(jrxml_path, report_ids, data)
        odoo_config["session"] = session_id
        _logger.debug(f"viaduct name={self.report.name}, session={session_id}")

        jasper_result = {}
        try:
            json_data = {
                "format": output_type,
                "dbParams": postgres_config,
                "odooParams": odoo_config,
                "reportParams": report_parameters,
            }
            encoded_json = json.dumps(json_data).encode("utf_8")

            http = urllib3.PoolManager()
            response = http.request(
                "POST", proxy_url, body=encoded_json,
                headers={"Content-Type": "application/json"})

            jasper_result = json.loads(response.data.decode("utf-8"))

        except HTTPError:
            raise UserError(f"Network error; jasperreports-viaduct web-app is not running at {proxy_url}?")
        except Exception as e:
            message = (hasattr(e, "message") and e.message) or e  # Sometimes error has no message
            raise UserError(f"{e}: {message}")
        finally:
            self.env["viaduct.session"].cleanup(session_id)

        _logger.debug("viaduct status={0}".format(jasper_result.get("status", "?")))
        if "output" not in jasper_result or not jasper_result["output"]:
            raise UserError(
                f"Viaduct returned no output for the report '{self.report.name}'.\n\n"
                f"State was '{jasper_result.get('status', '?')}'.")

        return (base64.b64decode(jasper_result["output"]), output_type)
