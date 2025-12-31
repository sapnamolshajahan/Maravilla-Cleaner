#  -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2019-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
{
  "name"          : "POS Linkly/EFTPOS Payment Terminal Integration",
  "summary"       : """The POS Linkly/EFTPOS Payment Terminal Integration module enables seamless connection between your POS system and the Linkly/EFTPOS Payment Terminal. This integration allows for smooth payment processing through the EFTPOS/Linkly terminal, enhancing the efficiency of transactions.
Keywords: Linkly POS Integration | EFTPOS Payment Terminal | Linkly Payment Terminal | EFTPOS Terminal Integration | Linkly Terminal Payment | EFTPOS Payment Processing | POS Payment with Linkly | Terminal Payment Linkly | Linkly EFTPOS Integration | EFTPOS/Linkly Terminal | POS EFTPOS Payment | Payment Terminal Integration | EFTPOS Terminal Payment | Linkly Payment for Odoo | Odoo Linkly Integration | Linkly Terminal Connection | EFTPOS Terminal for Odoo | Linkly Terminal Integration | EFTPOS Linkly Payment | POS Linkly Integration | EFTPOS Linkly Terminal Integration | EFTPOS Payment for Odoo | EFTPOS/Linkly Integration Solution | Linkly Payment Gateway | Odoo EFTPOS Integration | EFTPOS Payment for Point of Sale | EFTPOS Integration for Odoo | Linkly POS Payment Gateway | Odoo Linkly Payment | EFTPOS Linkly Payment Terminal Integration | Linkly EFTPOS Solution | Linkly Terminal for Odoo | EFTPOS Terminal for POS | Secure EFTPOS Payments | Odoo Payment Terminal Integration | Linkly Payment Processing Solution | POS Payment with EFTPOS | EFTPOS Integration for Odoo""",
  "category"      : "Point Of Sale",
  "version"       : "1.1.1",
  "sequence"      : 1,
  "author"        : "Webkul Software Pvt. Ltd.",
  "license"       : "Other proprietary",
  "website"       : "https://store.webkul.com/odoo-pos-linkly-eftpos-payment-terminal-integration.html",
  "description"   : """Integrate your POS with a Linkly/EFTPOS Payment Terminal""",
  "depends"       : ['point_of_sale'],
  "data"          : [
                      'security/ir.model.access.csv',
                      'views/linkly_transaction_views.xml',
                      'views/pos_payment_method_views.xml',
                      'views/pin_pad_pairing_views.xml',
                      'wizard/wizard_message_view.xml',
                    ],
  "assets"        : {
                      'point_of_sale._assets_pos': [
                        "pos_linkly_terminal_integration/static/src/js/payment_linkly.js",
                        "pos_linkly_terminal_integration/static/src/js/main.js",
                        "pos_linkly_terminal_integration/static/src/xml/pos.xml",
                      ],
                    },
  "application"   : True,
  "installable"   : True,
  "auto_install"  : False,
  "images"        : ['static/description/banner.png'],
  "price"         : 499,
  "currency"      : "USD",
  "pre_init_hook" : "pre_init_check",
}
