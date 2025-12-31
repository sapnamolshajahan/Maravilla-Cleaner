# -*- coding: utf-8 -*-
{
    "name": "Account Generic View Modifications",
    "version": "19.0.1.0",
    "depends": [
        "account",
        "base_generic_changes"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.nz",
    "category": "Account",
    "data": [
        "data/cron.xml",
        "data/journal-sequence.xml",
        "data/menu-security.xml",
        "wizards/account_journal_export.xml",
        "views/menus.xml",
        "views/bank.xml",
        "views/account_journal.xml",
        "views/account.xml",
        "views/res_config_settings.xml",
        "views/account_move.xml",
        "security/security.xml",
        "views/res_partner.xml",
    ],
    "installable": True,
    "active": False,
    'post_init_hook': '_account_account_post_init'
}
