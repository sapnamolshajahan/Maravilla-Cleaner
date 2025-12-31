# -*- coding: utf-8 -*-
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class GenericMailThread(models.AbstractModel):
    _inherit = "mail.thread"

    ###########################################################################
    # Functions
    ###########################################################################
    def _message_compute_author(self, author_id=None, email_from=None):
        """
        Replace Odoo default logic of figuring out author_id based on email_from in the email template
        As sometimes this causes unpredictable results if there are several partners with the same email.
        Let's simplify this & just use the current user's partner_id instead.

        """
        author_id, email_from = super(GenericMailThread, self)._message_compute_author(author_id=author_id,
                                                                                       email_from=email_from)

        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")
        if author_id != odoobot_id:
            author_id = self.env.user.partner_id.id

        return author_id, email_from
