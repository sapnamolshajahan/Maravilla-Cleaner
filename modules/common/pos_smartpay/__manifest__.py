# -*- coding: utf-8 -*-
{
    "name": "Smartpay POS integration",
    "version": "19.0.1.0",
    "category": "POS",
    "depends": [
        "base_generic_changes",
        "point_of_sale",
        "website",  # to handle multi-website configurations
    ],
    "author": "OptimySME Limited",
    "data": [
        "views/pos-dashboard.xml",
        "wizards/smartpay_pairing.xml",
        "wizards/smartpay_tx.xml",
    ],

    'assets': {
        'point_of_sale._assets_pos': [
            'pos_smartpay/static/src/js/payment-smartpay.js',
            'pos_smartpay/static/src/js/models.js',
        ],
    },

    "installable": True,
    "active": False
}
