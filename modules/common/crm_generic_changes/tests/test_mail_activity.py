# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "crm_generic_changes")
class TestCrmMailActivity(common.TransactionCase):
    """Class to test crm generic changes"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.crm_lead = self.env.ref('crm.crm_case_1')
        self.partner = self.env.ref('base.res_partner_12')
        self.activity_type = self.env['mail.activity.type'].create({
            'name': 'test_activity_type',
            'category': 'upload_file',
        })

    def test_crm_mail_activity(self):
        """
         Check different functionalities of crm_mail_activity
        """
        activity_1 = self.env['mail.activity'].create({
            'activity_type_id': self.activity_type.id,
            'res_model_id': self.env['ir.model']._get('crm.lead').id,
            'res_id': self.crm_lead.id,
        })
        self.assertEqual(activity_1.status, 'open')
        self.assertEqual(activity_1.date, datetime.now().date())
        # partner in mail activity check
        activity_1._get_partner()
        self.assertFalse(activity_1.partner_id)
        self.crm_lead.write({
            'partner_id':self.partner.id})
        activity_1._get_partner()
        self.assertEqual(activity_1.partner_id, self.crm_lead.partner_id)
        # Status in 'done'
        activity_1.action_done()
        self.assertEqual(activity_1.status, 'closed')
        self.assertEqual(activity_1.date_done, datetime.now().date())
