# -*- coding: utf-8 -*-
{
    "name": "Operations - Eliminate quants with negative quantity",
    "version": "1.0",
    "depends": [
        "stock",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "category": "Operations",
    "description": """
        Cron job to run nightly to eliminate quants with negative quantity by redistributing the negative quantity among other same-location quants with positive quantities.
    """,
    "data": [
        "data/cron.xml",
    ],
    "installable": True,
    "active": False,
}
