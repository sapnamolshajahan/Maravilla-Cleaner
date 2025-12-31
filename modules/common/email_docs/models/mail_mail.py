from odoo import models, tools


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _get_account_move_email(self, partner=None):
        move_doc_type_dict = {
            'out_invoice': 'invoice',
            'out_refund': 'credit-note',
        }
        move = self.env['account.move'].sudo().browse(self.mail_message_id.res_id)
        doc_type_name = move_doc_type_dict.get(move.move_type)
        if doc_type_name:
            domain = [
                ('disabled', '=', False),
                ('partner', '=', partner.id),
                ('email_doc_type.model_name', '=', 'account.move'),
                ('email_doc_type.name', '=', doc_type_name),
            ]
            email = self.env['partner.document.email'].search(domain, limit=1)

        return email


    def _prepare_outgoing_list(self, mail_server=False, recipients_follower_status=None):
        res = super()._prepare_outgoing_list(mail_server=mail_server,
                                                 recipients_follower_status=recipients_follower_status)
        for email_vals in res:
            partner_id = email_vals['partner_id']
            if partner_id and partner_id.email_documents and self.mail_message_id.model == 'account.move':
                doc_email = self._get_account_move_email(partner_id)
                if doc_email:
                    email_vals['email_to'] = [
                        tools.formataddr((partner_id.name or 'False', doc_email.email or 'False'))]
        return res





