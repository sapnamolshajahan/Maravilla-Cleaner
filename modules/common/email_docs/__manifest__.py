# -*- coding: utf-8 -*-
{
    "name": "Document Emailing",
    "version": "1.0",
    "depends": [
        "account_basic_invoice_reports",
        "mail",
        "queue_job",
        "base",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "category": "Bulk Email",
    "description": """
Summary
=======
Framework for sending Documents at various stages of workflow to the partner.
By default, all documents will be emailed to the default partner email address.
This can be overridden by specifying email addresses for each type. It can also be
disabled by type.

This base module will email invoices to customers if installed.

For customers who do not want invoices sent on validation, there is also a bulk
email-invoice functionality that will bulk send invoices to all customers. This:

	* *ignores* the enable/disable flag at the type level
	* *respects* the enable/disable flag at the partner level

However, the bulk-send can also be used to re-send invoices in bulk; useful if
the original send-out failed.
""",
    "data": [
        "security/permissions.xml",
        "data/email-templates.xml",
        "data/email-doc-type.xml",
        "views/email-doc-type.xml",
        "views/invoice.xml",
        "views/partner.xml",
        "wizards/bulk_customer_invoice.xml",
        "wizards/bulk_invoice.xml",
    ],
    "installable": True,
    "active": False,
}
