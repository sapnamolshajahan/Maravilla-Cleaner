# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LesserAttachment(models.Model):
    """
    A selection of fields from ir.attachment that does not include the BLOB field.
    """
    _name = "ir.attachment.lesser"
    _description = __doc__
    _auto = False

    ################################################################################
    # Fields
    ################################################################################
    create_date = fields.Datetime(string='Date', readonly=True)
    create_uid = fields.Many2one("res.users", readonly=True)
    name = fields.Char("Name", required=True)
    description = fields.Text("Description")
    res_model = fields.Char("Resource Model", readonly=True,
                            help="The database object this attachment will be attached to.")
    res_field = fields.Char("Resource Field", readonly=True)
    res_id = fields.Many2oneReference("Resource ID", model_field="res_model",
                                      readonly=True, help="The record id this is attached to.")
    company_id = fields.Many2one("res.company", string="Company", change_default=True,
                                 default=lambda self: self.env.company)
    type = fields.Selection([("url", "URL"), ("binary", "File")],
                            string="Type", required=True, default="binary", change_default=True,
                            help="You can either upload a file from your computer or copy/paste an internet link to your file.")
    url = fields.Char("Url")
    public = fields.Boolean("Is public document")
    mimetype = fields.Char('Mime Type', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """create view %s as (select %s from ir_attachment)""" % (self._table, ",".join(self.lesser_fields())))

    def lesser_fields(self):
        """
        :return: list of fields for the view, depending on fields defined.
        """
        fields = ["id"]
        for name, field in self._fields.items():
            if not hasattr(field, "automatic") or not hasattr(field, "compute"):
                continue
            if not field.automatic and not field.compute:
                fields.append(name)
        return fields

    @api.model_create_multi
    def create(self, vals_list):
        raise UserError("Can't do this. Use ir.attachment instead")

    def button_download(self):
        """
        Download attachment on ir.attachment
        :return: action-url for downloading attachment.
        """
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/{}?download=true".format(self.id),
            "target": "self",
        }

    def action_delete_attachment(self):
        """Deletes the selected attachments from ir.attachment with sudo"""
        attachment_ids = self.mapped("id")
        if attachment_ids:
            self.env["ir.attachment"].browse(attachment_ids).sudo().unlink()
