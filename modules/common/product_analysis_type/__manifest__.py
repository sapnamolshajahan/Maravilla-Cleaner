# -*- coding: utf-8 -*-
{
    "name": "Product Analysis Type",
    "version": "1.0",
    "depends": [
        "account",
        "stock",
        "stock_account",
        "sale",
        # "account_generic_changes", # test
        # "account_asset" # test
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "category": "Product",
    "description": "Add an extra analysis type onto products and includes in sales and revenue reporting.",
    "data": [
        "security/product-analysis.xml",
        "views/product_analysis.xml",
        "views/analysis_code_view.xml",
        "views/account_move_line.xml",
        "report/account_invoice_report.xml"
    ],
    "installable": True,
    "active": False,
}
