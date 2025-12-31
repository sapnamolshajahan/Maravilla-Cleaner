# -*- coding: utf-8 -*-
{
    "name": "Website Google Hide Pricing",
    "version": "1.0",
    "category": "Custom",
    "depends": [
        "sale",
        "base",
        "website_sale",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "http://www.optimysme.co.nz",
    "description": "Odoo has an issue on websites where pricing is only visible when the user is logged in."
                   "  The price is still visible in the HTML and when the Google search indexing engine indexes the page, it includes the price in the search results."
                   " This module adds a 'data-nosnippet' attribute to the class, preventing the price coming through into the HTML.",
    "data": [
        "views/website_changes.xml",
    ],
    "installable": True,
    "active": False,
}
