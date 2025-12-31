# -*- coding: utf-8 -*-
import uuid
from datetime import timedelta

from odoo import api, fields, models

JOB_TOKEN_EXPIRY = 10  # validity period for job-tokens in minutes


class JobToken(models.TransientModel):
    """
    Job Request Token
    """
    _name = "remote.print.mqtt.token.job"
    _description = __doc__

    ##################################################################################
    # Fields
    ##################################################################################
    job = fields.Many2one("remote.print.mqtt.job", required=True, ondelete="cascade")
    token = fields.Char("Token", required=True)
    expires = fields.Datetime("Expires", required=True)

    @api.model
    def create_for_job(self, job):
        """
        :param job: remote.print.mqtt.job
        """
        expires = fields.Datetime.now() + timedelta(minutes=JOB_TOKEN_EXPIRY)
        return self.create(
            [{
                "job": job.id,
                "token": str(uuid.uuid4()),
                "expires": expires,
            }])

    @api.model
    def job_by_token(self, token):
        job_tokens = self.search(
            [
                ("token", "=", token),
                ("expires", ">", fields.Datetime.now()),
            ])
        for job_token in job_tokens:
            return job_token.job
        return None
