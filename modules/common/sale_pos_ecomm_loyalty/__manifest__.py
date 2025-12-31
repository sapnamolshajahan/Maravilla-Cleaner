# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "Website and POS Loyalty and Reward Redemption",
    "version": "19.0.0.0",
    "category": "eCommerce",
    "depends": ['base', 'sale_management', 'point_of_sale', 'website', 'website_sale', 'delivery','website_sale_stock', 'sale_generic_changes', 'operations_auto_invoice'],
    "author": "OptimySME",
    'summary': 'Loyalty Program for Odoo, allowing accumulation of loyalty points and redemption of loyalty points for rewards.',
    "description": """
	Loyalty Program for Odoo, allowing accumulation of loyalty points and redemption of loyalty points for rewards.
	""",
    "data": [
        'security/ir.model.access.csv',
        'security/access.xml',
        'wizards/reedem_loyalty.xml',
        'wizards/prezzy_redemption_wizard.xml',
        'views/template.xml',
        'views/loyalty_view.xml',
        'views/product_view.xml',
        'views/res_partner.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            "sale_pos_ecomm_loyalty/static/src/js/pos.js",
            "sale_pos_ecomm_loyalty/static/src/js/OrderWidgetExtended.js",
            "sale_pos_ecomm_loyalty/static/src/js/LoyaltyButtonWidget.js",
            "sale_pos_ecomm_loyalty/static/src/js/LoyaltyPopupWidget.js",
            "sale_pos_ecomm_loyalty/static/src/js/PaymentScreen.js",
            "sale_pos_ecomm_loyalty/static/src/xml/pos.xml",

        ],
        'web.assets_frontend': [
            'sale_pos_ecomm_loyalty/static/src/js/custom.js',
            'sale_pos_ecomm_loyalty/static/src/js/open_redeem_modal.js',
        ],
    },
    "auto_install": False,
    "installable": True,
    "images": ['static/description/Banner.gif'],
    "live_test_url": 'https://www.browseinfo.com/demo-request?app=sale_pos_ecomm_loyalty&version=18&edition=Community',
    'license': 'OPL-1',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
