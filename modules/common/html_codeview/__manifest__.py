{
    'name': 'HTML Field Codeview',
    'version': '1.0',
    'category': 'Web',
    'summary': 'Enable codeview by default for HTML fields',
    'description': """
        This module modifies the HTML field to enable codeview by default.
        The codeview button will be available for all HTML fields unless explicitly disabled.
    """,
    'depends': ['html_editor'],
    "author": "OptimySME Ltd",
    "license": "Other proprietary",
    "website": "http://www.optimysme.co.nz",
    'data': [
    ],
    'assets': {
            'web.assets_backend': [
                'html_codeview/static/src/js/fields/html_field.js',
            ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}