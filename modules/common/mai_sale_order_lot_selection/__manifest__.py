{
    'name': 'Sale Order Lot Selection | Sales Lot Selection',
    'version': '19.0.1.1.1',
    'category': 'Sales Management',
    'summary': 'This module is automatically fetch lot number in inventory from sale order line',
    'description': """ Automatically lot number in inventory form Sale Order
    """,
    'price': 11,
    'currency': 'EUR',
    "author" : "MAISOLUTIONSLLC",
    'sequence': 1,
    "email": 'apps@maisolutionsllc.com',
    "website":'http://maisolutionsllc.com/',
    'license': 'OPL-1',
    'depends': ['sale_stock'],
    'data': [
            'views/sale_view.xml',
            'views/stock_view.xml'
             ],
    'qweb': [
        ],
    'images': ['static/description/main_screenshot.png'],
    "live_test_url" : "https://youtu.be/PUhfOXLvqhc",
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
