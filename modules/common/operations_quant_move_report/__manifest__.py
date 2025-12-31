# -*- coding: utf-8 -*-
{
    "name": "Quants Vs Moves",
    "version": "1.0",
    "category": "Operations",
    "author": "OptimySME Limited",
    "depends": [
        "stock",
        "queue_job",
        "queue_job_channels"
    ],
    "description": """Reporting and fixing of discrepancies between quants and stock moves.
                      The update logic checks at a location | product | lot | package level.
                      Includes a scheduled job to run each night""",
    "data": [
        "wizards/moves_vs_quants_report.xml",
        "security/operations_quant_move_report.xml",
        "data/ir_cron.xml",
        "wizards/moves_vs_quants_fix.xml"
    ],
    "installable": True,
}
