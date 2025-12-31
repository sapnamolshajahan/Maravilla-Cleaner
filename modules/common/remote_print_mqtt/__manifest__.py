# -*- coding: utf-8 -*-
{
    "name": "Remote Printing (MQTT)",
    "version": "1.0",
    "depends": [
        "base_generic_changes",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "category": "Hidden/Tools",
    "external_dependencies": {
        "python": ["paho-mqtt"],
    },
    "data": [
        "security/models.xml",
        "wizards/print_test.xml",
    ],
    "installable": True,
}
