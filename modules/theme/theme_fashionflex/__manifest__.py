# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Theme Fashionflex',
    'category': 'Theme/Corporate',
    'version': '19.0.0.0',
    'sequence': 1,
    'author': 'Bizople Solutions Pvt. Ltd.',
    'website': 'http://www.bizople.com',
    'summary': '''Theme Fashionflex is featured with eCommerce functionalities and is fully responsive to all devices.''',

    'depends': [
	    'website',
        'html_editor',
        'website_sale',
    ],

    'data': [
        "views/theme_fashionflex_inherited.xml",
        # homepage
        "views/homepage/s_home_banner.xml",
        "views/homepage/s_product_list.xml",
        "views/homepage/s_striped_top.xml",
        "views/homepage/s_left_content.xml",
        "views/homepage/s_carousel_wrapper.xml",

        # About us
        "views/aboutus/s_about_banner.xml",
        "views/aboutus/s_numbers_showcase.xml",
        "views/aboutus/s_unveil.xml",
        "views/aboutus/s_contact_info.xml",
    ],

    'assets': {
        'web._assets_primary_variables':[
            ('before', 'website/static/src/scss/options/colors/user_color_palette.scss', '/theme_fashionflex/static/src/scss/user_color_palette.scss'),
            ('before', 'website/static/src/scss/options/user_values.scss', '/theme_fashionflex/static/src/scss/user_values.scss'),
        ],
    },

    'images': [
        'static/description/fashionflex_cover.jpg',
        'static/description/fashionflex_screenshot.gif',

    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'OPL-1',
}
