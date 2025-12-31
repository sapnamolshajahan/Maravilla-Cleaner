# -*- coding: utf-8 -*-
{
    "name": "Operations Courier Integration",
    "version": "19.0.1.0.0",
    "depends": [
        "sale_alternate_shipping_address",  # references: sale.order:alt_street*
        "delivery",
        "remote_print_mqtt",
        'stock',
        'stock_delivery',
        'base_generic_changes',
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "category": "Delivery",
    "description": "Common features and changes for delivery (shipping)",
    "data": [
        "views/warehouse.xml",
        "views/warehouse_box.xml",
        "views/stock_picking.xml",
        "views/res_partner.xml",
        "views/carrier_shipment.xml",
        "views/delivery_carrier_views.xml",
        "wizard/carrier_shipment_wizard_view.xml",
        "security/security.xml",
    ],
    "installable": True,
}
