import base64
import json
import logging
import math
from datetime import date, datetime
import datetime
from math import ceil, floor

import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    xero_client_id = fields.Char('Client Id', copy=False, default=lambda self: self.env.company.xero_client_id)
    xero_client_secret = fields.Char('Client Secret', copy=False, default=lambda self: self.env.company.xero_client_secret)
    xero_redirect_url = fields.Char('Callback URL', default=lambda self: self.env.company.xero_redirect_url)
    skip_emails = fields.Char('Skip the following emails', default=lambda self: self.env.company.skip_emails)
    xero_auth_base_url = fields.Char('Authorization URL', default=lambda self: self.env.company.xero_auth_base_url)
    xero_tenant_id_url = fields.Char('Tenant ID URL', default=lambda self: self.env.company.xero_tenant_id_url)
    xero_access_token_url = fields.Char('Access Token URL', default=lambda self: self.env.company.xero_access_token_url)
    xero_tenant_name = fields.Char('Xero Company', copy=False, default=lambda self: self.env.company.xero_tenant_name)
    xero_country_name = fields.Char('Xero Country Name', default=lambda self: self.env.company.xero_country_name)
    export_invoice_without_product = fields.Boolean('Export Invoices with description only', copy=False,
                                                    default=lambda self: self.env.company.export_invoice_without_product)
    export_bill_without_product = fields.Boolean('Export Bills with description only', copy=False,
                                                 default=lambda self: self.env.company.export_bill_without_product)
    invoice_status = fields.Selection([('draft', 'DRAFT'), ('authorised', 'AUTHORISED')], 'Invoice/Bill Status',
                                      default=lambda self: self.env.company.invoice_status)
    non_tracked_item = fields.Boolean('Export Stock Product as Non Tracked Items', copy=False, default=lambda self: self.env.company.non_tracked_item)
    manual_journal = fields.Many2one(comodel_name='account.journal', help="Manual Journal",
                                     default=lambda self: self.env.company.manual_journal)
    revenue_default_account = fields.Many2one(comodel_name='account.account', default=lambda self: self.env.company.revenue_default_account,
                                      help='This Account will be attached to the invoice lines which does not contain quantity,unit price and account',
                                      string='Default Account')
    overpayment_journal = fields.Many2one(comodel_name='account.journal', help='Overpayment Journal',
                                          default=lambda self: self.env.company.overpayment_journal)
    prepayment_journal = fields.Many2one(comodel_name='account.journal', help='Prepayment Journal',
                                         default=lambda self: self.env.company.prepayment_journal)

    import_payments_from = fields.Date(string='Import payments from',
                                       help="""This date is updated each time the import runs. 
                                       Actual date used is this date -7 days to cover and back-dated receipts""")
    xero_integration_delay = fields.Integer(string="Delay between sending Xero documents",
                                            default=lambda self: self.env.company.xero_integration_delay)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "xero_client_id": self.xero_client_id,
                "xero_client_secret": self.xero_client_secret,
                "xero_redirect_url": self.xero_redirect_url,
                "skip_emails": self.skip_emails,
                "xero_auth_base_url": self.xero_auth_base_url,
                "xero_tenant_id_url": self.xero_tenant_id_url,
                "xero_access_token_url": self.xero_access_token_url,
                "xero_tenant_name": self.xero_tenant_name,
                "xero_country_name": self.xero_country_name,
                "export_invoice_without_product": self.export_invoice_without_product,
                "export_bill_without_product": self.export_bill_without_product,
                "invoice_status": self.invoice_status,
                "non_tracked_item": self.non_tracked_item,
                "manual_journal": self.manual_journal.id,
                "revenue_default_account": self.revenue_default_account.id,
                "overpayment_journal": self.overpayment_journal.id,
                "prepayment_journal": self.prepayment_journal.id,
                "import_payments_from": self.import_payments_from,
                "xero_integration_delay": self.xero_integration_delay,

            })

