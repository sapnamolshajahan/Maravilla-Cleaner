# -*- coding: utf-8 -*-
import base64

from odoo import fields, models


class PrintTest(models.TransientModel):
    """
    Test the Remote Print
    """
    _name = "remote.print.mqtt.test"
    _description = __doc__

    ################################################################################
    # Fields
    ################################################################################
    queue = fields.Char("Queue name", required=True)
    content = fields.Binary("File to print", attachment=False, required=True)
    filename = fields.Char("Filename")

    ################################################################################
    # Methods
    ################################################################################
    def button_print(self):
        self.env["remote.print.mqtt.job"].submit_print(self.queue, [base64.b64decode(self.content)])
        return {'type': 'ir.actions.act_window_close'}
