# -*- coding: utf-8 -*-
{
    "name": "Packing Slip Reports",
    "version": "1.0",
    "category": "Reporting",
    "depends": [
        "delivery",
        "stock_delivery",
        "jasperreports_viaduct",
        "sale_alternate_shipping_address",
        "operations_generic_changes"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": " Customised Packing Slip",
    "data": [
        "reports/reports.xml",
        "views/partner.xml",
        "views/picking.xml",
    ],
    "installable": True,
    "active": False,
}
