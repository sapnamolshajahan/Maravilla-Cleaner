from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    adjustment_approver = fields.Many2one('res.users', string="Adjustment Approver",
                                    default=lambda self: self.env.company.adjustment_approver,
                                    readonly=False)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "adjustment_approver": self.adjustment_approver
            }
        )