# -*- coding: utf-8 -*-
import base64
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ViaductImage(models.TransientModel):
    """
    Viaduct Session Images
    """
    _name = "viaduct.session.image"
    _description = __doc__
    _sql_constraints = [
        ("unique_name", "unique(session, name)", "Images must be unique per session")
    ]

    ################################################################################
    # Fields
    ################################################################################
    session = fields.Many2one("viaduct.session", "Session Image", ondelete="cascade", required=True)
    name = fields.Char("Image Key", required=True)
    content = fields.Binary("Image Content", attachment=False)

    @api.model
    def construct(self, session, record, field):
        """
        Make a copy of the image onto the session.
        """
        image_key = f"{record._name}-{field}-{record.id}"
        images = self.search(
            [
                ("session", "=", session.id),
                ("name", "=", image_key),
            ])
        for image in images:
            return image

        values = {
            "session": session.id,
            "name": image_key,
        }
        if record[field]:
            values["content"] = base64.b64decode(record[field])
        created = self.create([values])
        _logger.debug(f"created session={session.id}, name={image_key}")
        return created
