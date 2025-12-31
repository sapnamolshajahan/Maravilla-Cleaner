# -*- coding: utf-8 -*-

{
    "name": "GST Functionality",
    "version": "1.0",
    "category": "Accounting",
    "depends": [
        "account",
        "base_generic_changes",
    ],
    "author": "Optimysme Limited",
    "license": "Other proprietary",
    "description": """
        Allow incl GST code to be set at a journal line and auto-create the line, plus GST reporting for NZ
    """,
    "data": [
        "wizard/gst_data.xml",
        "security/account_gst.xml",
        "data/account_tax_report_data.xml"
    ],
    "installable": True,
}
