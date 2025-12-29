from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request
import json


class CheckoutExtend(WebsiteSale):

    @http.route('/shop/address/submit', type='http', auth="public", website=True, methods=['POST'], sitemap=False)
    def shop_address_submit(self, **post):

        # First call original method to process the address
        response = super().shop_address_submit(**post)

        # 🔥 Correct: request.cart is the current sale order in Odoo 19
        order = request.cart

        if order:
            order.write({
                'room_number': post.get('room_number'),
                'room_type': post.get('room_type'),
                'check_in': post.get('check_in'),
                'check_out': post.get('check_out'),
                'num_person': post.get('num_person'),
                'remarks': post.get('remarks'),
            })

        return response
