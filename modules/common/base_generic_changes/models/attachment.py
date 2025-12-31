# -*- coding: utf-8 -*-
import logging

from odoo import api, models
from odoo.exceptions import AccessError
from ..utils.chunk_list import chunk_list

_logger = logging.getLogger(__name__)


class Attachments(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def force_db_storage(self):
        """
        Force storage to database.

        This is intended to be used with odoo-shell. Very useful for data-conversion
        with a huge set of attachments in file-store.

        :return:
        """
        if not self.env.is_admin():
            raise AccessError("Only administrators can execute this action.")

        key = self.env["ir.config_parameter"].search([("key", "=", "ir_attachment.location")])
        if key:
            if key.value != "db":
                key.write({"value": "db"})
                _logger.info("set ir_attachment.location=db")
                self.env.cr.commit()
        else:
            key.create(
                [{
                    "key": "ir_attachment.location",
                    "value": "db",
                }])
            _logger.info("created ir_attachment.location=db")
            self.env.cr.commit()

        attach_sql = "select id from ir_attachment where store_fname is not null"
        self.env.cr.execute(attach_sql)
        attach_ids = [x[0] for x in self.env.cr.fetchall()]

        # Commit changes in chunks
        for chunk_ids in chunk_list(attach_ids, 100):
            for attach in self.browse(chunk_ids):
                attach.write({'raw': attach.raw, 'mimetype': attach.mimetype})
            self.env.cr.commit()
            self.invalidate_model()
            _logger.debug(f"updated ids={chunk_ids}")
