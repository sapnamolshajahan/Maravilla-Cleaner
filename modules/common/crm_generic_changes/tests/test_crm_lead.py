# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "crm_generic_changes")
class TestCrmLead(common.TransactionCase):
    """Class to test crm generic changes"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.crm_lead = self.env.ref('crm.crm_case_1')
        self.crm_lead_2 = self.env.ref('crm.crm_case_13')
        self.partner = self.env.ref('base.res_partner_12')

    def test_crm_lead_setups(self):
        """
         Check different functionalities of crm
        """
        # Check primary_contact in crm
        self.assertNotIn(self.crm_lead.primary_contact, self.crm_lead.contact_ids)
        self.crm_lead.write({
            'contact_ids': [(6,0, self.partner.ids)]
        })
        self.assertIn(self.crm_lead.primary_contact, self.crm_lead.contact_ids)
        # Action add crm contact
        crm_contact = self.crm_lead.action_add_contact()
        crm_lead_new_partner = self.env['crm.lead.new.partner'].browse(crm_contact['res_id'])
        self.assertEqual(crm_lead_new_partner.lead.id,  self.crm_lead.id)
        crm_lead_new_partner.write({
            "name": 'Test Contact',
            "position": 'Lead',
            "email": 'test@123.com',
            "mobile": '+915678934',
            "phone": '08902345677',
        })
        crm_lead_new_partner.action_save_another()
        partner = self.env['res.partner'].search([('mobile', '=', '+915678934')],limit=1)
        self.assertIn(partner, self.crm_lead.contact_ids)
        # partner_activity
        self.partner._compute_activity_count()
        self.assertEqual(self.partner.activity_count, 0)

    def test_crm_lead_mail_activity(self):
        # Check mail_activity setup in crm
        mail_activity = self.crm_lead.action_mail_activity()
        self.assertEqual(mail_activity['context']['default_res_id'], self.crm_lead.id)
        self.assertEqual(mail_activity['context']['default_name'], self.crm_lead.name)
        self.assertEqual(mail_activity['context']['default_opportunity_id'], False) # type = lead
        mail_activity = self.crm_lead_2.action_mail_activity()
        self.assertEqual(mail_activity['context']['default_res_id'], self.crm_lead_2.id)
        self.assertEqual(mail_activity['context']['default_name'], self.crm_lead_2.name)
        self.assertEqual(mail_activity['context']['default_opportunity_id'], self.crm_lead_2.id)  # type = opportunity
