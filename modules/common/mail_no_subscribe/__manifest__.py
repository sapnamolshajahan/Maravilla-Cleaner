# -*- coding: utf-8 -*-
{
    "name": "Turn Off Subscriber Updates ",
    "version": "1.0",
    "category": "Mail",
    "depends": [
        "mail",
    ],
    "author": "Optimysme Limited",
    "license": "Other proprietary",
    "description": """
    Overrides auto-adding subscribers when mail is sent on a record.
    BASED ON CONFIG SETTINGS:
        If email to is a user, then remove from the list.
        If follower is external, then remove from list.
        
        So only send to specified receipients
        
    """,
    "data": [
        "views/res_config_settings.xml",
    ],
    "demo": [],
    "test": [],
    "installable": True,
}
