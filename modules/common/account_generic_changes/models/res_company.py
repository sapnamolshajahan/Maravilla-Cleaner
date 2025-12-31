# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    supplier_partner_check = fields.Boolean("Purchase Partner Check")
    journal_set_counts_zero = fields.Boolean(string='Override Journal Counts on Partner Form')
    invoiced_set_counts_zero = fields.Boolean(string='Override Total Invoice Value on Partner Form')
    fiscal_year_last_lock_date = fields.Date(string="End Lock Date",
                                             help="Set maximum date you want transactions "
                                                  "to be able to dated to avoid typo issues")

    @api.model
    def _module_set_onboarding_done(self):
        companies = self.env['res.company'].search([])
        companies.write({
            # 'account_dashboard_onboarding_state': 'closed',
            # 'account_invoice_onboarding_state': 'closed',
            # 'account_setup_bank_data_state': 'done',
            # 'account_setup_fy_data_state': 'done',
            # 'account_setup_coa_state': 'done',
            # 'account_onboarding_invoice_layout_state': 'done',
            # 'account_onboarding_create_invoice_state': 'done',
            # 'account_onboarding_sale_tax_state': 'done',
            # 'account_setup_bill_state': 'done'
        })


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    supplier_partner_check = fields.Boolean("Purchase Partner Check",
                                            default=lambda self: self.env.company.supplier_partner_check)
    journal_set_counts_zero = fields.Boolean(string='Override Journal Counts on Partner Form')
    invoiced_set_counts_zero = fields.Boolean(string='Override Total Invoice Value on Partner Form')
    fiscal_year_last_lock_date = fields.Date(string="End Lock Date",
                                             help="Set maximum date you want transactions "
                                                  "to be able to dated to avoid typo issues",
                                             default=lambda self: self.env.company.fiscal_year_last_lock_date)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "supplier_partner_check": self.supplier_partner_check,
                "journal_set_counts_zero": self.journal_set_counts_zero,
                "invoiced_set_counts_zero": self.invoiced_set_counts_zero,
                "fiscal_year_last_lock_date": self.fiscal_year_last_lock_date,

            }
        )
