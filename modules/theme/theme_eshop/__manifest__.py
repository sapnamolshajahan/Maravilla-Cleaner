# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Theme Eshop',
    'category': 'Theme/Corporate',
    'version': '19.0.0.0',
    'sequence': 1,
    'author': 'Bizople Solutions Pvt. Ltd.',
    'website': 'http://www.bizople.com',
    'summary': '''Theme Eshop is featured with eCommerce functionalities and is fully responsive to all devices.''',

    'depends': [
	    'website',
        'html_editor',
        'website_sale',
    ],

    'data': [
        "views/theme_eshop_inherited.xml",
        # homepage
        "views/homepage/s_home_banner.xml",
        "views/homepage/s_product_list.xml",
        "views/homepage/s_dynamic_snippet_one.xml",
        "views/homepage/s_image_block.xml",
        "views/homepage/s_dynamic_snippet_two.xml",
        "views/homepage/s_image_text.xml",
        "views/homepage/s_title_text.xml",
        "views/homepage/s_three_image_block.xml",
        "views/homepage/s_references.xml",
        "views/homepage/s_quotes_carousel.xml",
    ],

    'assets': {
        'web._assets_primary_variables':[
            ('before', 'website/static/src/scss/options/colors/user_color_palette.scss', '/theme_eshop/static/src/scss/user_color_palette.scss'),
            ('before', 'website/static/src/scss/options/user_values.scss', '/theme_eshop/static/src/scss/user_values.scss'),
        ],
    },

    'images': [
       'static/description/eshop_cover.png',
       'static/description/eshop_screenshot.gif',

    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'OPL-1',
}
