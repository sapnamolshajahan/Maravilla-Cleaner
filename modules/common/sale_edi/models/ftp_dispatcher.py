# -*- coding: utf-8 -*-
import re
import logging

from io import BytesIO as StringIO
from ftplib import FTP

from odoo.addons.base_generic_changes.utils.config import configuration

_logger = logging.getLogger(__name__)

SECTION_NAME = "ftp-edi-credentials"

ftp_host = configuration.get(SECTION_NAME, "host", fallback="")
ftp_port = int(configuration.get(SECTION_NAME, "port", fallback="22"))
ftp_username = configuration.get(SECTION_NAME, "username", fallback="")
ftp_password = configuration.get(SECTION_NAME, "password", fallback="")

ftp_incoming = configuration.get(SECTION_NAME, "incoming", fallback=".")
ftp_outgoing = configuration.get(SECTION_NAME, "outgoing", fallback=".")


class FtpDispatcher(object):
    """
    Simple wrapper to dispatch XML content
    """

    def __init__(self):
        try:
            # Create Transport object using supplied method of authentication.
            transport = FTP(ftp_host, ftp_username, ftp_password)
            transport.encoding = "utf-8"

            self.ftp = transport
            _logger.info("connected ftp {}@{}".format(ftp_username, ftp_host))

            self.ftp.cwd(".")
            self.home = '/'
            _logger.debug("home={}".format(self.home))

        except Exception as e:
            _logger.error("Error establishing FTP connection")
            _logger.error(e)
            self.ftp = None

    def send(self, content, dest_filename):
        """
        @param content string to transfer
        @param dest_filename name of destination remote file
        """
        if not self.ftp:
            _logger.warning("No FTP connection for send")
            return False

        dest_filename = re.sub(r'[^\w\s]', '_', dest_filename).replace(' ', '_')

        self.ftp.cwd(self.home)
        self.ftp.cwd(ftp_incoming)
        bio = StringIO(content)
        self.ftp.storbinary('STOR {}'.format(dest_filename), bio)
        _logger.info("EDI uploaded " + dest_filename)
        return True

    def list_orders(self):

        if not self.ftp:
            _logger.warning("No ftp connection for pickup")
            return []

        self.ftp.cwd(self.home)
        # testout directory does not have any confirmation control documents
        self.ftp.cwd('out')
        return self.ftp.nlst()

    def fetch_by_file_name(self, pickup_file):

        if not self.ftp:
            _logger.warning("No ftp connection for pickup")
            return None

        # Iterate through file and write each character to a list, before returning the string
        output = []
        self.ftp.cwd(self.home)
        # testout directory does not have any confirmation control documents
        self.ftp.cwd('out')
        self.ftp.retrlines('RETR ' + pickup_file, callback=output.append)

        return output[0]

    def remove_pickup(self, pickup_file):

        if not self.ftp:
            _logger.warning("No ftp connection for removal")
            return

        self.ftp.cwd(self.home)
        self.ftp.cwd(ftp_incoming)
        self.ftp.remove(pickup_file)
        _logger.debug("ftp removed={}".format(pickup_file))

    def close(self):

        if self.ftp:
            self.ftp.close()
            _logger.info("closed ftp connection {}@{}".format(ftp_username, ftp_host))
