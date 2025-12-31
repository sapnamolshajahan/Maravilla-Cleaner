from odoo import models, fields, api


class BhagReportWizard(models.TransientModel):
    _name = 'bhag.report.wizard'
    _description = 'BHAG Report Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    def action_print_report(self):
        return self.env.ref('adv_bhag.bhag_xlsx_report_action').report_action(self)
