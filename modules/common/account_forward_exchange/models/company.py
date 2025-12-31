from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    fec_mode = fields.Selection([('ibr', "Invoice First"),
                                 ('rbi', "Receipt First")],
                                "FEC Operation Mode",
                                default='ibr'
                                )

    alternative_currency = fields.Integer(string='Obsolete')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fec_mode = fields.Selection([('ibr', "Invoice First"),
                                 ('rbi', "Receipt First")],
                                "FEC Operation Mode",
                                default=lambda self: self.env.company.fec_mode
                                )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "fec_mode": self.fec_mode,

            }
        )

