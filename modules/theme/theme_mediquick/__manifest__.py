# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Theme MediQuick',
    'category': 'Theme/Corporate',
    'version': '19.0.0.0',
    'sequence': 1,
    'author': 'Bizople Solutions Pvt. Ltd.',
    'website': 'http://www.bizople.com',
    'summary': '''Theme MediQuick is featured with eCommerce functionalities and is fully responsive to all devices.''',

    'depends': [
	    'website',
        'html_editor',
        'website_blog',
    ],

    'data': [
        "views/theme_mediquick_inherited.xml",
        # homepage
        "views/homepage/s_home_banner.xml",
        "views/homepage/s_choose_us.xml",
        "views/homepage/s_gallery.xml",
        "views/homepage/s_image_text.xml",
        "views/homepage/s_text_image.xml",
        "views/homepage/s_three_columns.xml",
        "views/homepage/s_teams.xml",
        "views/homepage/s_contact_us.xml",
        
        "views/aboutus/s_aboutus_banner.xml",
        "views/aboutus/s_contact.xml",
        "views/aboutus/s_faq.xml",
        "views/aboutus/s_image_texts.xml",
        "views/aboutus/s_product_list.xml",
        "views/aboutus/s_text_with_bg.xml",
        "views/aboutus/s_text.xml",

        "views/s_contactus.xml",
    ],

    'assets': {
        'web._assets_primary_variables':[
            ('before', 'website/static/src/scss/options/colors/user_color_palette.scss', '/theme_mediquick/static/src/scss/user_color_palette.scss'),
            ('before', 'website/static/src/scss/options/user_values.scss', '/theme_mediquick/static/src/scss/user_values.scss'),
        ],
    },

    'images': [
       'static/description/mediquick_cover.png',
       'static/description/mediquick_screenshot.gif',
    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'OPL-1',
}