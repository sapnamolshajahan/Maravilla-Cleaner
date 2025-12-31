# -*- coding: utf-8 -*-
from . import models


def pre_init_hook(env):
    env.cr.execute("""
        ALTER TABLE product_template 
        ADD COLUMN list_price_jsonb jsonb DEFAULT '{}'::jsonb;
    """)

    env.cr.execute("""
        WITH active_companies AS (
            SELECT id FROM res_company WHERE active = TRUE
        )
        UPDATE product_template
        SET list_price_jsonb = (
            SELECT jsonb_object_agg(company.id::TEXT, product_template.list_price::TEXT::NUMERIC)
            FROM active_companies company
        )::jsonb;
    """)

    env.cr.execute("""
        ALTER TABLE product_template DROP COLUMN list_price;
    """)

    env.cr.execute("""
        ALTER TABLE product_template RENAME COLUMN list_price_jsonb TO list_price;
    """)

    env.cr.execute("""
        ALTER TABLE public.product_template
        ALTER COLUMN list_price TYPE jsonb
        USING list_price::jsonb;
    """)

    env.cr.execute("""
        ALTER TABLE product_template 
        ADD COLUMN tracking_jsonb jsonb DEFAULT '{}'::jsonb;
    """)

    env.cr.execute("""
        WITH active_companies AS (
            SELECT id FROM res_company WHERE active = TRUE
        )
        UPDATE product_template
        SET tracking_jsonb = (
            SELECT jsonb_object_agg(company.id::TEXT, product_template.tracking)
            FROM active_companies company
        )::jsonb;
    """)

    env.cr.execute("""
        ALTER TABLE product_template DROP COLUMN tracking;
    """)

    env.cr.execute("""
        ALTER TABLE product_template RENAME COLUMN tracking_jsonb TO tracking;
    """)
