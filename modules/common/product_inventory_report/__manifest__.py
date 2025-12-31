# -*- coding: utf-8 -*-
{
    "name": "Product Inventory Report",
    "version": "1.0",
    "category": "Reporting",
    "depends": [
        "base",
        "stock",
        "queue_job",
        "account",
        "queue_job_channels",
        "queue_job_notifications"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": ("Produce download for Stock on Hand and cost value "
                    "information."),
    "data": [
        "security/ir.model.access.csv",
        "wizard/product_inventory_report_view.xml"
    ],
    "update_xml": [],
    "demo": [],
    "test": [],
    "installable": True,
    "active": False,
}
