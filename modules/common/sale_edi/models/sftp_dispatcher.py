# -*- coding: utf-8 -*-
import re
import paramiko
import logging

from io import BytesIO as StringIO

from odoo.addons.base_generic_changes.utils.config import configuration

_logger = logging.getLogger(__name__)

SECTION_NAME = "sftp-edi-credentials"
sftp_host = configuration.get(SECTION_NAME, "host", fallback=None)
sftp_port = int(configuration.get(SECTION_NAME, "port", fallback="22"))
sftp_username = configuration.get(SECTION_NAME, "username", fallback=None)
sftp_password = configuration.get(SECTION_NAME, "password", fallback=None)

sftp_incoming = configuration.get(SECTION_NAME, "incoming", fallback=".")
sftp_outgoing = configuration.get(SECTION_NAME, "out going", fallback=".")
archive_path = configuration.get(SECTION_NAME, "archive", fallback=".")


class SftpDispatcher(object):
    """
    Simple wrapper to dispatch XML content
    """

    def __init__(self):
        try:
            private_key = None

            # Create Transport object using supplied method of authentication.
            transport = paramiko.Transport((sftp_host, sftp_port))
            transport.connect(None, sftp_username, sftp_password, private_key)

            self.sftp = paramiko.SFTPClient.from_transport(transport)
            _logger.info("connected SFTP {}@{}".format(sftp_username, sftp_host))

            self.sftp.chdir(".")
            self.home = self.sftp.getcwd()
            _logger.debug("home={}".format(self.home))

        except Exception as e:
            _logger.error(e)
            self.sftp = None

    def send(self, content, dest_filename):
        """
        @param content string to transfer
        @param dest_filename name of destination remote file
        """
        if not self.sftp:
            _logger.warning("No SFTP connection for send")
            return False

        dest_filename = re.sub(r'[^\w\s]', '_', dest_filename).replace(' ', '_') + '.xml'

        self.sftp.chdir(self.home)
        dest_path = sftp_outgoing + "/" + dest_filename
        self.sftp.putfo(StringIO(content), dest_path)
        _logger.info("EDI uploaded " + dest_path)
        return True

    def list_orders(self):

        if not self.sftp:
            _logger.warning("No SFTP connection for pickup")
            return []

        self.sftp.chdir(self.home)
        self.sftp.chdir(sftp_incoming)
        return self.sftp.listdir()

    def fetch_by_file_name(self, pickup_file):

        if not self.sftp:
            _logger.warning("No SFTP connection for pickup")
            return None

        output = StringIO()
        self.sftp.chdir(self.home)
        self.sftp.chdir(sftp_incoming)
        self.sftp.getfo(pickup_file, output)
        result = output.getvalue()
        output.close()

        return result

    def remove_pickup(self, pickup_file):

        if not self.sftp:
            _logger.warning("No SFTP connection for removal")
            return

        self.sftp.chdir(self.home)
        self.sftp.chdir(sftp_incoming)
        self.sftp.remove(pickup_file)
        _logger.debug("SFTP removed={}".format(pickup_file))

    def archive_by_file_name(self, pickup_file):
        if not self.sftp:
            _logger.warning("No SFTP connection for archival")
            return

        self.sftp.chdir(self.home)
        self.sftp.chdir(sftp_incoming)
        self.sftp.rename(pickup_file, archive_path + pickup_file)
        _logger.debug("File {} has been moved to archive directory.".format(pickup_file))

    def close(self):

        if self.sftp:
            self.sftp.close()
            _logger.info("closed SFTP connection {}@{}".format(sftp_username, sftp_host))
