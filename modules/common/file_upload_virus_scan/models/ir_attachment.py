# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from io import BytesIO as StringIO

import pyclamd

from odoo import models, api
from odoo.tools import config

SECTION = "file_upload_virus_scan"
KEY_CLAMAV_HOST = "clamav_host"
KEY_CLAMAV_PORT = "clamav_port"

CLAMAV_HOST = config.get(KEY_CLAMAV_HOST, "")
CLAMAV_PORT = int(config.get(KEY_CLAMAV_PORT, 3310))

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    ###########################################################################
    # Business Methods
    ###########################################################################
    @api.model
    def scan_file(self, base64_content):
        """
        :param base64_content: base64 content of an uploaded file to check
        :return: (True, None) if no viruses found
        If there are viruses, it will return False along with res (virus details)
        """
        if not base64_content:
            return True, None

        start_time = datetime.now()

        try:
            if CLAMAV_HOST:
                scanner = pyclamd.ClamdNetworkSocket(host=CLAMAV_HOST, port=CLAMAV_PORT)
            else:
                scanner = pyclamd.ClamdUnixSocket()

            res = scanner.scan_stream(StringIO(base64_content))

        except (TypeError, Exception):
            res = {"stream": "Error Scanning file upload"}
            _logger.error("Error clamd scanning file", exc_info=True)

        elapsed = datetime.now() - start_time
        _logger.info(f"pyclamd scan result: {res}, elapsed: {elapsed}s")

        if res:
            return False, "{}: {}".format(res["stream"][0], res["stream"][1])

        return True, None
