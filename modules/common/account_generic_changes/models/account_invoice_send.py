# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _send_mail(self, move, mail_template, **kwargs):
        kwargs.update({
            'force_send': False,
        })
        res = super()._send_mail(move, mail_template, **kwargs)

        return res
