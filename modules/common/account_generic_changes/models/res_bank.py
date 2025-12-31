# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResBank(models.Model):
    _inherit = "res.partner.bank"

    swift = fields.Char('SWIFT Code', size=12)

    # Remove bank-account constraint by redefining to null-op
    _sql_constraints = [
        ("unique_number", "check (1 = 1)", "Disabled"),
    ]

    def write(self, vals):
        self.partner_id.write({'has_bank_account': True})
        return super(ResBank, self).write(vals)

    def unlink(self):
        for rec in self:
            if len(rec.partner_id.bank_ids) == 1:
                self.partner_id.write({'has_bank_account': False})
        return super(ResBank, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                partner.write({'has_bank_account': True})
            return super(ResBank, self).create(vals_list)



