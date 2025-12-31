# -*- coding: utf-8 -*-
from odoo import models


class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    def _insert_followers(self, res_model, res_ids,
                          partner_ids, subtypes=None,
                          customer_ids=None, check_existing=True, existing_policy='skip'):
        partners_to_remove = []
        if partner_ids:
            for i in range(0, len(partner_ids)):
                partner_id = partner_ids[i]
                partner = self.env['res.users'].sudo().search([('partner_id', '=', partner_id)])

                if partner:
                    partners_to_remove.append(partner_ids[i])

            if partners_to_remove:
                for i in reversed(range(0, len(partner_ids))):
                    partner_ids.pop(i)

        return super(MailFollowers, self)._insert_followers(
            res_model, res_ids, partner_ids, subtypes=subtypes, customer_ids=customer_ids,
            check_existing=check_existing, existing_policy=existing_policy)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_get_recipients(self, message, msg_vals=False, **kwargs):
        recipient_data = super(MailThread, self)._notify_get_recipients(message, msg_vals, **kwargs)
        if not recipient_data:
            return recipient_data

        for i in reversed(range(0, len(recipient_data))):
            if self.env.company.exclude_internal and not message.subtype_id.internal:
                if recipient_data and recipient_data[i]['type'] == 'user':
                    recipient_data.pop(i)
                    continue
            if self.env.company.exclude_external:
                if recipient_data and recipient_data[i]['type'] == 'customer':
                    if recipient_data[i]['id'] not in [x.id for x in message.partner_ids]:
                        recipient_data.pop(i)

        return recipient_data
