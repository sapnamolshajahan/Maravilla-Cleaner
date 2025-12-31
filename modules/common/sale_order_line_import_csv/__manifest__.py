# -*- coding: utf-8 -*-
{'name': 'Sale Order Line Import ',
 'version': '1.0',
 'depends': ["base", "sale","sale_stock"],
 "author": "OptimySME Limited",
 "license": "Other proprietary",
 'website': 'https://www.optimysme.co.nz',
 'category': 'Sales',
 'description': ("Provides a wizard to import sales order lines "
                 "from a CSV file."),
 'data': ["security/ir.model.access.csv",
          "wizard/sale_order_line_import_csv_view.xml"],
 'installable': True,
 "external_dependencies": {
     "python": ["openpyxl"],
 },
 'active': False,
 }
