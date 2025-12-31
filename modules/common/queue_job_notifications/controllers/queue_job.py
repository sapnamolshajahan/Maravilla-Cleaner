# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class JobQueueController(http.Controller):

    @http.route('/get/job/link/<int:job_id>', type='http', auth='user', website=True)
    def get_job_link(self, job_id=False):
        if job_id:
            action_id = request.env.ref('queue_job.action_queue_job')
            return request.redirect('/web#id=%d&action=%d&model=queue.job&view_type=form' % (job_id, action_id))
