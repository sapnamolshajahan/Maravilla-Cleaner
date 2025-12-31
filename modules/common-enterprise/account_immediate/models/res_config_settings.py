from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    max_writeoff = fields.Integer(string='Maximum Write-Off', default=lambda self: self.env.company.max_writeoff)
    write_off_journal = fields.Many2one(comodel_name='account.journal',
                                        string='Write Off Journal', default=lambda self: self.env.company.write_off_journal)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "max_writeoff": self.max_writeoff,
                "write_off_journal": self.write_off_journal.id,
            }
        )
        return
