# -*- coding: utf-8 -*-
{
    "name": "Audit Logging",
    "version": "1.0",
    "depends": [
        "account",
        "report_pdf",
    ],
    "author": "OptimySME Limited",
    "website": "https://www.optimysme.co.nz",
    "category": "Utilities",
    "description": """Log data changes.
This is not a standalone module. In order to use this, a new module needs to be created
with this as a dependancy; and the create/write methods need to be overidden for models
that need to be tracked.""",
    "data": [
        "data/audit_report_email.xml",
        "views/audit_logging.xml",
        "wizard/audit_log_print.xml",
        "security/audit_logging.xml",
        "views/ir_model_view.xml",
    ],
    "installable": True,
    "active": False,
    "license": "Other proprietary",
}
