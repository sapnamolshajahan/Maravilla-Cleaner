# -*- coding: utf-8 -*-
{
    "name": "Lesser Attachments",
    "version": "1.0",
    "category": "Utilities",
    "depends": [
        "base",
    ],
    "author": "OptimySME Limited",
    "website": "https://www.optimysme.co.nz",
    "description": """
Attachments without the BLOB
============================

This module creates a view of ir.attachment that contains
a minimal set of fields, but especially *NOT* the BLOB field.
This allows the ORM to use this lesser-view without killing the
backend process if the multiple records with big attachments
are manipulated.
    """,
    "data": [
        "security/access.xml",
    ],
    "installable": True,
    "active": False,
    "license": "Other proprietary",
}
