# -*- coding: utf-8 -*-
import base64
import logging

from odoo import api, models, fields
from odoo.tools.safe_eval import safe_eval, time

_logger = logging.getLogger(__name__)


class AsyncEmail(models.TransientModel):
    """
    Engine that drives the auto email delivery.
    """
    _name = "email.async.send"
    _description = __doc__

    ################################################################################
    # Fields
    ################################################################################
    partner = fields.Many2one("res.partner", "Partner", required=True, ondelete="cascade")
    doc_type_name = fields.Char("Doc Type", required=True)
    res_ids = fields.Char("List of record ids", required=True)
    forced = fields.Boolean("Ignore email.doc.type enabled")
    callback = fields.Char("Optional Callback method name")

    ################################################################################
    # Methods
    ################################################################################
    @api.model
    def send(self, doc_type_name, res_ids, partner, callback=None):
        """
        Standard entry-point to submit reports onto the task queue to be sent.

        @param doc_type_name a selection for email.doc.type.name
        @param res_ids list of ids to be handed to the report associated with doc_type_name
        @param partner res.partner record
        @param callback optional method name that will be invoked against records browsed by res-id, with no args
        """
        doc_type = self.env["email.doc.type"].search([("name", "=", doc_type_name)])
        if not doc_type.enabled:
            _logger.debug("doc-type={} disabled".format(doc_type_name))
            return

        self.send_doc(doc_type, False, res_ids, partner, callback)

    @api.model
    def force_send(self, doc_type_name, res_ids, partner, callback=None):
        """
        Ignore email.doc.type and submit reports onto the task queue to be sent.

        @param doc_type_name a selection for email.doc.type.name
        @param res_ids list of ids to be handed to the report associated with doc_type_name
        @param partner res.partner record
        @param callback optional method name that will be invoked against records browsed by res-id, with no args
        """
        doc_type = self.env["email.doc.type"].search([("name", "=", doc_type_name)])
        self.send_doc(doc_type, True, res_ids, partner, callback)

    @api.model
    def send_doc(self, doc_type, forced, res_ids, partner, callback):

        if isinstance(partner, int):
            # Has partner disabled doc-type specified?
            partner = self.env['res.partner'].browse(partner)

        docs = partner.email_documents.filtered(lambda d: d.email_doc_type.id == doc_type.id)
        if not docs:
            return

        elif docs:
            for doc in docs:
                if doc.disabled:
                    _logger.debug("doc-type={} disabled for partner={}".format(doc_type.name, partner.name))
                    return None
        elif not partner.email:
            _logger.info("partner={} has no email".format(partner.name))
            return None

        send_object = self.create(
            [{
                "partner": partner.id,
                "doc_type_name": doc_type.name,
                "res_ids": str(res_ids),
                "forced": forced,
                "callback": callback,
            }])

        self.with_delay(
            channel=self.light_job_channel(),
            description="Email Docs for {}".format(partner.name)
        )._send(self.env.uid, send_object.id)

        return send_object

    @api.model
    def _send(self, uid, async_id):
        """
        Entry point for Job Queue.
        """
        user = self.env["res.users"].browse(uid)
        async_obj = self.with_user(user).browse(async_id)
        async_obj.send_email()

    def send_email(self):

        self.ensure_one()

        doc_type = self.env["email.doc.type"].search([("name", "=", self.doc_type_name)])
        if not self.forced and not doc_type.enabled:
            _logger.info(f"doc-type={self.doc_type_name} disabled")
            return

        res_ids = safe_eval(self.res_ids)

        docs = self.partner.email_documents.filtered(lambda d: d.email_doc_type.id == doc_type.id)
        if docs:
            for doc in docs:
                if doc.disabled:
                    _logger.info(f"doc-type={self.doc_type_name} disabled for partner={self.partner.name}")
                    return
                if doc.email:
                    self.render_and_send(doc_type, res_ids, doc.email)
                else:
                    _logger.warning(f"no email address for doc-type={self.doc_type_name}, partner={self.partner.name}")
        elif self.partner.email:
            # Use default
            self.render_and_send(doc_type, res_ids, self.partner.email)
        else:
            _logger.warning(f"no email address for partner={self.partner.name}")
            return

        if self.callback:
            model = self.env[doc_type.model_name]
            if hasattr(model, self.callback):
                getattr(model.browse(res_ids), self.callback)()
            else:
                _logger.error(f"non-existent callback={self.callback} on model={model}")

    def render_and_send(self, doc_type, res_ids, email):
        """
        :param doc_type document type to generate
        :param res_ids list of record ids to generate and send
        :param email destination email
        """
        attachment_model = self.env["ir.attachment"].sudo()
        mail_model = self.env["mail.mail"].sudo()

        for res_obj in self.env[doc_type.model_name].browse(res_ids):

            report = res_obj.email_doc_report()
            if not report:
                _logger.error(f"report not found: model={res_obj._name}, report={res_obj.email_doc_report()}")
                continue

            if doc_type.template:
                values = doc_type.template._generate_template(
                    [res_obj.id], self.env['mail.template.preview']._MAIL_TEMPLATE_FIELDS)

                mail_values = values.get(res_obj.id, {})
                if "attachments" in mail_values:
                    del mail_values["attachments"]
            else:
                mail_values = {}
            mail_values.update({"email_to": email})
            mail_values = self.update_mail_values(mail_values, res_obj)

            if report.print_report_name:
                report_name = safe_eval(report.print_report_name, {"object": res_obj, "time": time})
            else:
                report_name = report.report_name
            result, rpt_format = report._render(report, [res_obj.id])

            attachment = attachment_model.create(
                [{
                    "name": report_name + "." + rpt_format,
                    "datas": base64.b64encode(result),
                    "description": report.report_name,
                }])

            mail_values.update(
                {
                    "attachment_ids": [(6, 0, [attachment.id])],
                })
            mail_created = mail_model.create(mail_values)

            attachment.write(
                {
                    "res_model": mail_created._name,
                    "res_id": mail_created.id,
                })
            _logger.debug("sent email={}, report={}, template={}".format(email, report_name, doc_type.template.name))

    def update_mail_values(self, mail_values, res_obj):
        """
        Give subclasses the opportunity to override mail values prior to creation.

        :param mail_values: current mail_values to be used for mail.mail
        :param res_obj: browse record for the mail values
        :return:
        """
        return mail_values
