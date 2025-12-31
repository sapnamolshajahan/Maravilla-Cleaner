# -*- coding: utf-8 -*-
{
    "name": "Account Forward Exchange",
    "version": "1.0",
    "depends": [
        "account",
        "base_generic_changes",
        "purchase",
        "account",
    ],
    "author": "OptimySME Limited",
    "website": "http://www.optimysme.co.nz",
    "license": "Other proprietary",
    "category": "Account",
    "description": "Provides ability to record Forward Exchange Contracts and use in various other modules."
                   "Plus on an invoice, ability to set a rate",
    "data": [
        "security/forward-exchange.xml",
        "views/account_move.xml",
        "views/res_config_settings.xml",
        "views/forward_exchange.xml",
        "data/forward_exchange.xml",
        "views/purchase_order.xml",
        "views/account_bank_statement.xml"
    ],
    "demo": [
        "demo/account.xml",
    ],
    "installable": True,
    "active": False,
}
