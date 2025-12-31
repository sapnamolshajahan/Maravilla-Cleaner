# -*- coding: utf-8 -*-
{
    "name": "Operations - Document Emailing",
    "version": "1.0",
    "depends": [
        "email_docs",
        "sale",
        "stock",
        "queue_job_channels",
        "operations_packing_slip_reports", #get_delivery_report()
        "sale_order_reports" # get_sale_order_report()
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "category": "Bulk Email",
    "description": """
        Extends email_docs module to provide for sale orders and packing slips
""",
    "data": [
        "data/email-templates.xml",
        "data/email-doc-type.xml",
    ],
    "installable": True,
    "active": False,
}
