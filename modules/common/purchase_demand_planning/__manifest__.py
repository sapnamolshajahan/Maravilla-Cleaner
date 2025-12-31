# -*- coding: utf-8 -*-

{
    "name": "Demand Planning",
    "version": "1.0",
    "depends": [
        "base_generic_changes",
        "stock",
        "sale",
        "mrp",
        "operations_generic_changes",
        "purchase",
        "purchase_generic_changes",
        "product",
        # "stock_accounting"
    ],
    "author": "OptimySME Limited",
    "category": "Purchasing",
    "description": "Demand forecasting for purchasing, typically for situations where min-max logic is not sufficient",
    "data": [
        "security/forecast_data.xml",
        "data/sequence.xml",
        "views/company.xml",
        "views/forecast_data.xml",
        "views/product_category.xml",
        "views/supplierinfo.xml",
        "wizards/forecast_generate_purchase.xml",
        "views/partner.xml"
    ],
    "installable": True,
}
