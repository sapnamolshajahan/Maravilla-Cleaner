# -*- coding: utf-8 -*-

import base64
import logging

from odoo import api, models, fields

_logger = logging.getLogger(__name__)

TEMPLATE_NAME = 'audit_logging.audit_logging_report_email_template'


class AuditTrailPrint(models.TransientModel):
    _name = "audit.log.print"

    # Fields
    start = fields.Datetime(string="From", default=lambda self: fields.Datetime.now(), required=True)
    finish = fields.Datetime(string="Until", default=lambda self: fields.Datetime.now(), required=True)
    model_ids = fields.Many2many(comodel_name="ir.model", string="Models", required=True,
                                 domain=[('audit_logging', '=', True)])
    run_as_task = fields.Boolean(string='Run as Task')
    group_by = fields.Many2one(comodel_name='audit.logging.group', string='Report Group By')
    report_name = fields.Char(size=64, string="Report Name", readonly=True, default="Audit Report")
    data = fields.Binary(string="Download File", readonly=True)
    output_type = fields.Selection(selection=[("xlsx", "Excel"), ("pdf", "PDF"), ],
                                   string="Output format", default='xlsx')

    # Methods

    def print_report(self):
        if self.run_as_task:
            return self.run_report_as_task(
                wizard_ids=self.ids,
                email=self.env.user.partner_id.email
            )

        else:
            result = self.env['audit.log.report'].run_report(self.ids[0])
            if not result:
                return {"type": "ir.actions.act_window_close"}

            _name, file_name, _desc, data = result

            data.seek(0)
            output = base64.encodebytes(data.read())
            self.write(
                {
                    "data": output,
                    "report_name": file_name,
                })

        view = self.env.ref("audit_logging.audit_report_download_view")
        return {
            "name": view.name,
            "type": "ir.actions.act_window",
            "res_model": "audit.log.print",
            "view_mode": "form",
            "view_type": "form",
            "view_id": view.id,
            "res_id": self.id,
            "target": "new",
        }

    def run_report_as_task(self, wizard_ids, email):
        self.with_delay(
            channel=self.light_job_channel(),
            description="Generate Audit Logging Report").create_audit_report_from_task(wizard_ids, email)

    @api.model
    def create_audit_report_from_task(self, wizard_ids, email):
        wizard_ids = [int(i) for i in wizard_ids]
        result = self.env['audit.log.report'].run_report(wizard_ids[0])
        if not result:
            return

        _name, file_name, _desc, data = result

        data.seek(0)
        output = base64.encodebytes(data.read())

        attach = self.env['ir.attachment'].create({
            'name': file_name,
            'datas': output
        })

        print(self.env.ref(TEMPLATE_NAME), self._name, wizard_ids[0])

        mail_obj = self.env['mail.mail'].create({
            'email_to': email,
            'email_from': self.env.company.partner_id.email,
            'subject': _name,
            'attachment_ids': [(6, 0, attach.ids)],
            'body_html': self.env['mail.template']._render_template(
                self.env.ref(TEMPLATE_NAME).body_html,
                self._name, wizard_ids
            )[wizard_ids[0]]
        })

        # Send email and mark record
        self.env['mail.mail'].send([mail_obj])
