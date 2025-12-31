# -*- coding: utf-8 -*-
{
    "name": "Odoo Remittance Advice Reports from Account Payment",
    "version": "1.0",
    "category": "Reporting",
    "depends": [
        "account",
        "account_basic_invoice_reports",  # res.partner:invoice_display_address()
        "jasperreports_viaduct",
    ],
    "author": "Optimysme Limited",
    "description": """Various reports associated with payments and remittance advice""",
    "license": "Other proprietary",
    "data": [
        "reports/reports.xml",
        "views/account_payment.xml",
        "wizards/choose_partner.xml",
        "security/security.xml",
    ],
    "installable": True,
}
