# -*- coding: utf-8 -*-

{
    'name': 'Trial Balance Reports',
    'version': '19.0.1.0.0',
    'depends': [
        'account', 'account_generic_changes',
        'report_pdf'
    ],
    'author': 'OptimySME Limited',
    "license": "Other proprietary",
    'description': """
    
    User selects an as at date and XLS file for balances is produced
    
     
    """,
    'website': 'https://www.optimysme.co.nz',
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_trial_balance_view.xml',
        'wizard/account_trial_balance_month_view.xml'
    ],
    'installable': True,
    'active': False,
}
