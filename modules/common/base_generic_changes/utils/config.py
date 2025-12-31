# -*- coding: utf-8 -*-
from configparser import ConfigParser

from odoo.tools import config

#
# Introduce a Configuration Reader for Internal Sections
#
configuration = ConfigParser()
configuration.read(config["config"])
