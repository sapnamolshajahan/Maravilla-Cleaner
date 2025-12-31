# -*- coding: utf-8 -*-
import logging

from odoo.exceptions import UserError

from odoo import fields

_logger = logging.getLogger(__name__)


class EDIGenerator(object):
    """
    Base class for all EDI generators; simply sub-class and override build_edi()
    """

    def __init__(self, env, **kwargs):
        """
        @param env - odoo-env object
        """
        self.env = env

    def send_email(self, partner, invoices):
        """
        Build and send out the documents.
        """
        attachment_model = self.env["ir.attachment"]
        mail_model = self.env["mail.mail"]

        doc = self.build_edi(partner, invoices)

        if not doc.data:
            _logger.info(f"No data for this invoice, not sending anything")
            return

        ctx = dict(self.env.context)
        if 'default_type' in ctx:
            del ctx['default_type']
        if 'type' in ctx:
            del ctx['type']
        attachment = attachment_model.with_context(ctx).create(
            {
                "name": "{} - {}".format(partner.name, doc.filename),
                "datas": doc.data,
                "description": "EDI file"
            })
        mail_model.create(
            {
                "email_to": partner.edi_email,
                "subject": doc.subject,
                "body_html": "<pre>{}</pre>".format(doc.body),
                "attachment_ids": [(6, 0, [attachment.id])]
            })
        invoices.write(
            {
                "edi_sent": fields.Datetime.now(),
                "is_move_sent": True
            })
        _logger.debug("sent EDI for {}, {} invoices".format(partner.name, len(invoices)))

    def build_edi(self, partner, invoices):
        """
        Sub-classes are expected to override this.
        @return populated EDIDoc object.
        """
        raise UserError("Builder not written")


class EDIDoc(object):
    """
    Simple data container.
    """

    def __init__(self):
        self.filename = "file name"
        self.subject = "mail subject"
        self.body = "mail body"
        self.data = None
