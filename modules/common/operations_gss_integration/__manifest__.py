# -*- coding: utf-8 -*-

{
    "name": "GoSweetSpot Integration",
    "version": "19.0.1.0.1",
    "depends": [
        "stock",
        "delivery",
        "operations_courier_integration"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.nz",
    "category": "Delivery",
    "description": """
Integration with GoSweetSpot API. This module will add a 'Validate and ship' button on outgoing pickings.

* Before this can be used you must set up new shipping methods and mark these with Enable GoSweetSpot Integration. 
    Under the Carrier Services tab, use the 'POPULATE CARRIER SERVICES' button to query GSS for available carrier 
    services. The services are queried by using the name you specified. If no services found make sure the name is 
    correct and that the carrier is supported by GSS.
* Also under Inventory configuration menu, add the standard boxes/bags used by the company for parcels.
* Specify label printers under each warehouse. This is not mandatory if you print the courier labels manually. The
    labels can be found under attachments once the GSS order has been placed.
* Under outgoing pickings there is a new tab called 'GoSweetSpot'. This is where detailed information can be found
    for the GSS shipment order.
* Finally you need this in the Odoo configuration file:

::

    [go-sweet-spot-integration]
    api_key = The API key given to you by GSS
    email_id = the-system-admin@company.co.nz
    api_endpoint = https://api.gosweetspot.com/api
    dev_mode = True # Set False for production
""",
    "data": [
        "views/delivery_carrier_view.xml",
        "views/gss_carrier_shipment.xml",
        "views/gss_dangerous_goods_preset.xml",
        "views/gss_package_code_views.xml",
        "views/warehouse_box.xml",
        "wizard/carrier_shipment_wizard_view.xml",
        "security/security.xml",
    ]
}
