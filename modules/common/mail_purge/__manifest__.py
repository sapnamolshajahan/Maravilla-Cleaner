# -*- coding: utf-8 -*-
{
    "name": "Mail Purge",
    "version": "1.0",
    "category": "Social Network",
    "depends": ["mail"],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "description": """Purge emails on a regular basis.
To Use:
     - Install and then configure System Parameter mail_purge.purge_days to a number > zero.
     - Configure mail purge scheduled task frequency and time.
    """,
    "data": [
        "data/mail.xml",
    ],
    "installable": True,
    "active": False
}
