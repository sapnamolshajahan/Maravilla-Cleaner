# -*- coding: utf-8 -*-
{
    "name": "Queue Job Notifications",
    "version": "1.0",
    "category": "Other",
    "depends": ["queue_job"],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "description": """
    Job queue success and failure notifications.
    Success/Fail notification turn ON/OFF in the job queue creation moment.
    Notifications with link to task.
    """,
    "data": [
        'security/ir.model.access.csv',
        'datas/queue_notifications.xml',
        'views/queue_job.xml',
    ],
    "test": [],
    "installable": True,
    "active": False,
}
