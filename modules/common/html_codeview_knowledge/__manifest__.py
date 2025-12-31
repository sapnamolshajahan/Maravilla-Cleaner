{
    'name': 'HTML Field Codeview fix for Knowledge',
    'version': '1.0',
    'category': 'Web',
    'summary': 'HTML Field Codeview fix for Knowledge',
    'description': """
        HTML Field Codeview fix for Knowledge
    """,
    'depends': [
        'html_codeview',
        'knowledge',
    ],
    "author": "OptimySME Ltd",
    "license": "Other proprietary",
    "website": "http://www.optimysme.co.nz",
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            (
                'after',
                'knowledge/static/src/components/knowledge_html_field/knowledge_html_field.js',
                'html_codeview_knowledge/static/src/js/fields/knowledge_html_field.js',
            ),
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}