# -*- coding: utf-8 -*-
{
    "name": "POS Receipt Autoprint",
    "version": "1.0",
    "category": "Point Of Sale",
    "author": "OptimySME Limited",
    "website": "https://www.optimysme.co.nz",
    "depends": [
        "account_invoice_reports",
        "pos_receipt",
        "queue_job_channels",
    ],
    "data": [
        "data/label-template.xml",
        "views/pos_config.xml"
    ],
    "assets": {
        # Override of web-assets sent to the POS
        "point_of_sale._assets_pos": [
            "pos_auto_print_receipt/static/src/app/screens/payment_screen/payment_screen.js",
            "pos_auto_print_receipt/static/src/app/store/pos_store.js",
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}
