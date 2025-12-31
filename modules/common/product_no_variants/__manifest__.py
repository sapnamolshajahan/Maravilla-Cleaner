# -*- coding: utf-8 -*-

{
    "name": "Product No Variants",
    "version": "1.0",
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "description": """
        A number of changes to the standard product and product templates views and objects.
        The key users of this module should be businesses that do not require variants
        as this module hides that complexity. As far as these business are concerned
        a product is a product. """,
    "images": [],
    "depends": [
        "product",
        "stock",
        "purchase"
    ],
    "category": "Operations",
    "demo": [],
    "data": [
        "views/product_view_extensions.xml",
        # "views/purchase_view.xml"
    ],
    "auto_install": False,
    "installable": True,
}
