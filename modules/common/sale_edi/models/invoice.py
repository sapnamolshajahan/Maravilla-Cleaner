# -*- coding: utf-8 -*-
import base64
import logging
from datetime import timedelta

from odoo.tools.config import config

from odoo import fields, models, _
from .ftp_dispatcher import FtpDispatcher
from .sftp_dispatcher import SftpDispatcher

_logger = logging.getLogger(__name__)

class Invoice(models.Model):
    _inherit = "account.move"

    ################################################################################
    # Fields
    ################################################################################
    edi_sent = fields.Datetime("EDI Sent", readonly=True)
    edi_confirmed = fields.Datetime(string="EDI Confirmed", readonly=True)
    unconfirmed_email_sent = fields.Boolean("Email for no EDI confirmation sent", default=False)

    def action_post(self):
        """
        Send EDI documents during validation.
        """
        res = super(Invoice, self).action_post()
        for invoice in self:
            partner = invoice.partner_id
            if invoice.partner_id.is_bunnings_partner():
                try:
                    self.env["bunnings.edi"].send_edi(partner, invoice, message_type="INV")
                    _logger.info(
                        f"EDI Invoice sent for Invoice {self.id} (Partner {partner.id})",
                    )
                except Exception as e:
                    _logger.exception(f"EDI Invoice failed for Invoice {invoice.id} (Partner {invoice.partner_id.id}). Error: {e}")
            else:
                # keep the existing FTP/SFTP flow intact
                invoice.action_send_edi_ftp()
        return res

    def action_resend_edi(self):
        """
        Send out EDI, grouped by invoice.partner_id
        """
        partner_invoice = {}
        for invoice in self:
            if not invoice.partner_id.edi_generator and not invoice.invoice_address.edi_generator:
                continue

            if invoice.invoice_address.edi_generator:
                if invoice.invoice_address in partner_invoice:
                    partner_invoice[invoice.invoice_address].append(invoice)
                else:
                    partner_invoice[invoice.invoice_address] = [invoice]
            elif invoice.partner_id.edi_generator:
                if invoice.partner_id in partner_invoice:
                    partner_invoice[invoice.partner_id].append(invoice)
                else:
                    partner_invoice[invoice.partner_id] = [invoice]

        # Generate (and send) EDI for each partner
        for partner, invoices in partner_invoice.items():
            for invoice in invoices:
                partner.with_delay(
                    channel=self.light_job_channel(),
                    description="Submit EDI Email for {}".format(invoice.name)
                ).generate_edi(invoice)
                invoice.write({'edi_sent': fields.Datetime.now()})

    def action_send_edi_ftp(self):
        partner_invoice = {}
        for invoice in self:
            if not invoice.partner_id.edi_generator and not invoice.invoice_address.edi_generator:
                continue

            if invoice.invoice_address.edi_generator:
                if invoice.invoice_address in partner_invoice:
                    partner_invoice[invoice.invoice_address].append(invoice)
                else:
                    partner_invoice[invoice.invoice_address] = [invoice]
            elif invoice.partner_id.edi_generator:
                if invoice.partner_id in partner_invoice:
                    partner_invoice[invoice.partner_id].append(invoice)
                else:
                    partner_invoice[invoice.partner_id] = [invoice]
            invoice.write(
                {'unconfirmed_email_sent': False}
            )

        # Generate (and send) EDI for each partner
        for partner, invoices in partner_invoice.items():
            for invoice in invoices:
                if partner.edi_generator == 'itm':
                    dispatcher = FtpDispatcher()
                elif partner.edi_generator == 'buildlink':
                    dispatcher = SftpDispatcher()
                else:
                    dispatcher = None
                edi_generator = partner.get_generator()
                file_name = edi_generator.get_edi_filename(partner, invoice)
                edi_content = edi_generator.create_edi(invoice.partner_id, invoice)
                if not edi_content:
                    continue

                if dispatcher:
                    send_ok = dispatcher.send(base64.b64decode(edi_content), file_name)
                    dispatcher.close()
                    msg = _('EDI file {} for this invoice has been sent.'.format(file_name))
                    invoice.message_post(body=msg)
                    invoice.write(
                        {'edi_sent': fields.Datetime.now()}
                    )

    def check_edi_confirmations(self):
        dispatcher = FtpDispatcher()
        control_documents_list = dispatcher.list_orders()
        for filename in control_documents_list:
            existing_control_document = self.env['itm.control.document'].sudo().search([('filename', '=', filename)])
            if not existing_control_document:
                output = dispatcher.fetch_by_file_name(filename)
                identifier_index = output.find("'UCI+")
                invoice_id = int(output[identifier_index + 5:].split('+')[0])
                associated_invoice = self.env['account.move'].sudo().search([('id', '=', invoice_id)])
                if associated_invoice:
                    associated_invoice.write({
                        'edi_confirmed': fields.Datetime.now()
                    })
                    associated_invoice.message_post(body=_('Invoice EDI Document has been confirmed.'))
                    self.env['itm.control.document'].sudo().create({
                        'filename': filename,
                        'associated_invoice': invoice_id,
                        'content': output
                    })

    def check_sftp_edi_confirmations(self):
        dispatcher = SftpDispatcher()
        control_documents_list = dispatcher.list_orders()
        for filename in control_documents_list:
            existing_control_document = self.env['itm.control.document'].sudo().search([('filename', '=', filename)])
            if not existing_control_document:
                try:
                    output = dispatcher.fetch_by_file_name(filename)
                except OSError as e:
                    continue
                if not isinstance(output, str):
                    output  = output.decode("utf-8")
                identifier_index = output.find("'UCI+")
                invoice_id = int(output[identifier_index + 5:].split('+')[0])
                associated_invoice = self.env['account.move'].sudo().search([('id', '=', invoice_id)])
                if associated_invoice:
                    associated_invoice.write({
                        'edi_confirmed': fields.Datetime.now()
                    })
                    associated_invoice.message_post(body=_('Invoice EDI Document has been confirmed.'))
                    self.env['itm.control.document'].sudo().create({
                        'filename': filename,
                        'associated_invoice': invoice_id,
                        'content': output
                    })
                    dispatcher.archive_by_file_name(filename)

    def check_unconfirmed_edi_invoices(self):
        result = self.env['res.config.settings'].sudo().search([], order="id desc", limit=1)
        if result.unconfirmed_edi_notify_email and result.unconfirmed_edi_period:
            unconfirmed_invoices = self.env['account.move'].search([('unconfirmed_email_sent', '=', False),
                                                                    ('edi_sent', '!=', False)])
            for invoice in unconfirmed_invoices:
                confirmation_cutoff = invoice.edi_sent + timedelta(hours=result.unconfirmed_edi_period)
                if fields.Datetime.now() > confirmation_cutoff:
                    mail_template = self.env.ref('sale_edi.edi_confirmation_not_received_template').sudo()
                    mail_vals = {
                        'email_to': result.unconfirmed_edi_notify_email,
                        'period': result.unconfirmed_edi_period
                    }
                    mail_template.with_context(mail_vals).send_mail(invoice.id, force_send=True)
                    invoice.write({
                        'unconfirmed_email_sent': True
                    })
                    invoice.message_post(body=_('Invoice EDI has not been confirmed after a period of {} hours.'.format(result.unconfirmed_edi_period)))
