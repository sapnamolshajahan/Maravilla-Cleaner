# -*- coding: utf-8 -*-

from . import models
from . import reports


def register_alt_address_helper():
    from .reports import purchase_order_helper
