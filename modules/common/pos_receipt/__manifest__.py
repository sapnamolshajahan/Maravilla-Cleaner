# -*- coding: utf-8 -*-
{
    "name": "POS Receipt",
    "version": "19.0.1.0.1",
    "category": "Point Of Sale",
    "author": "OptimySME Limited",
    "depends": [
        "escpos_reports",
        "label_printer",
        "point_of_sale",
        "remote_print_mqtt",
    ],
    "data": [
        "security/pos_queue.xml",
        "reports/escpos-report.xml",
        "reports/label-template.xml",
        "views/company.xml",
        "views/pos_config.xml",
        "views/pos_order.xml",
        "views/pos_queue.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
