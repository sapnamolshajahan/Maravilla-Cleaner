# -*- coding: utf-8 -*-
from . import models
from . import wizards


def _account_account_post_init(env):
    env.cr.execute("""
        UPDATE ir_model_data
        SET noupdate = true
        WHERE module ilike '%l10n%' AND model = 'account.account'
       """)
