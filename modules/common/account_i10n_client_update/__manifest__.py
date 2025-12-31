# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'generic module to update a COA to a clients COA - assumes that i10n_nz has been run first',
    "version": "19.0.1.0",
    "author": "Optimysme Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "description": """Imports an XLS file with a format of
                        Code | Name | Account Type.
                    You need to make sure code is properly formatted and unique
                    AND the account type is converted to the Odoo format(eg expense).
                    This module just fixes the COA codes and descriptions and adds/archives as required.
                    Can be uninstalled after running"""
,
    "depends": ["account"],
    "category": "Accounting & Finance",
    "data": [
        "wizard/coa_upgrade.xml",
        "security/security.xml"
    ],
    "installable": True,
}