# -*- coding: utf-8 -*-
import logging
import subprocess
import tempfile

from odoo import api, models
from ..config import BROKER, LP_CMD

_logger = logging.getLogger(__name__)


class PrintMixin(models.AbstractModel):
    _name = "remote.print.mixin"

    @api.model
    def lp_command(self, queue: str, data_list, copies=1) -> bool:
        """
        Print locally or remotely.

        :param queue: queue name
        :param data_list: bytes or bytes-list
        :param copies: number of copies to print
        :return: True if all jobs submitted successfully
        """

        def system_lp(lp_cmd, pathname):
            """
            :return: local print command
            """
            args = {
                "queue": queue,
                "copies": str(copies),
                "path": pathname,
            }
            for arg, value in args.items():
                placeholder = "{" + arg + "}"
                lp_cmd = lp_cmd.replace(placeholder, value)
            return lp_cmd.split()

        if type(data_list) == bytes:
            data_list = [data_list]
        if BROKER:
            return self.env["remote.print.mqtt.job"].submit_print(queue, data_list, copies)

        # Invoke system printer
        all_good = True
        for data in data_list:
            with tempfile.NamedTemporaryFile(delete=True, suffix=".remote_print_mqtt") as spoolfile:
                spoolfile.write(data)
                spoolfile.flush()
                command = system_lp(LP_CMD, spoolfile.name)
                _logger.debug(f"printing: {command}")
                done = subprocess.run(command, capture_output=True, text=True)
                info = f"printing: exit={done.returncode}"
                if done.stdout:
                    info += f", stdout=\"{done.stdout.strip()}\""
                if done.stderr:
                    info += f", stderr=\"{done.stderr.strip()}\""
                _logger.info(info)

                if all_good:
                    all_good = done.returncode == 0

        return all_good
