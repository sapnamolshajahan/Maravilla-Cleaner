# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _send_mail(self, move, mail_template, **kwargs):
        res = super()._send_mail(move, mail_template, **kwargs)

        res_id = self._context.get('default_res_id')
        res_model = self._context.get('default_model')

        if res_model == "account.move":
            self.env[res_model].browse(res_id).write({'sent': True})

        return res

