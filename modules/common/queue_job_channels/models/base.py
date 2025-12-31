# -*- coding: utf-8 -*-
from odoo import api, models


class Base(models.AbstractModel):
    """
    The base model, which is implicitly inherited by all models.

    Add methods accessing channel-name for use with queue_job's: with_delay(channel=).
    """
    _inherit = "base"

    @api.model
    def _named_job_channel(self, xmlid):
        """
        We can't use self.env.ref directly, as the user will not have access to queue.job.channel
        """
        res_model, res_id = self.env["ir.model.data"]._xmlid_to_res_model_res_id(xmlid, raise_if_not_found=True)
        return self.env[res_model].sudo().browse(res_id).complete_name

    @api.model
    def light_job_channel(self):
        """
        queue.job channel for light jobs.
        """
        return self._named_job_channel("queue_job_channels.light_job_channel")

    @api.model
    def heavy_job_channel(self):
        """
        queue.job channel for heavy jobs.
        """
        return self._named_job_channel("queue_job_channels.heavy_job_channel")
