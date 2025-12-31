# -*- coding: utf-8 -*-
{
    "name": "Mail Block Internal Notification ",
    "version": "19.0.1.0",
    "category": "Mail",
    "depends": [
        "mail", "base"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": """
    Sets a flag on the model - if true, then do not create any mail.notification records for this model for 
    internal users. 
    Purpose is to reduce spam.
    Send message or log activities is unaffected.
    """,
    "data": [
        "views/ir_model.xml"
    ],
    "demo": [],
    "test": [],
    "installable": True,
}
