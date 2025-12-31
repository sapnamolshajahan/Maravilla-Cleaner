# -*- coding: utf-8 -*-
{
    "name": "EDI for Sales",
    "version": "1.0",
    "category": "Accounting",
    "depends": [
        "account_generic_changes",
        "delivery",
        "sale_stock",
        "queue_job",
        "operations_courier_integration",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.nz",
    "description": """
EDI Generator
=============

Some partners prefer their invoices to be sent as an EDI document;
this module will generate a text-based EDI document as an attachment to send
to the specified edi-email address.

Currently this module has support for the following EDI generators:

   * Mitre 10
   * Independent Timber Merchants (ITM)
""",
    "data": [
        "data/cron.xml",
        "views/edi_not_confirmed_email_template.xml",
        "views/invoice.xml",
        "views/partner.xml",
        "views/res_config_settings.xml",
        "views/stock_picking.xml",
        "views/delivery_view.xml",
    ],
    "installable": True,
    "active": False
}
