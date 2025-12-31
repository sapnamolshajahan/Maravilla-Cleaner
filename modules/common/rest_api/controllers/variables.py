# -*- coding: utf-8 -*-
# AUTH
HEADER_ODOO_AUTHORISATION = 'Odoo-Authorisation'

# Routes
MODEL_ROUTE = "/api/v1/model/<model>"
RECORD_ROUTE = "/api/v1/model/<model>/<record_id>"
ATTACHMENT_ROUTE = "/api/v1/model/<model>/<record_id>/attachment"
LOGIN_ROUTE = "/api/v1/login"

# CORS
ALLOWED_AUTH_HEADERS = 'Content-Type, Odoo-Authorisation'
ALLOWED_HEADERS = "Content-Type, Accept, Access-Token, access_token, Origin, X-Requested-With"
ORIGIN = "*"  # TODO replace with actual domains
