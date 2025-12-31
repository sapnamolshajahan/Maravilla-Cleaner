# -*- coding: utf-8 -*-
from odoo.addons.jasperreports_viaduct.reports.common_helper import CommonHelper


class AltAddrPurchaseOrderHelper (CommonHelper):
    """Display delivery addresses slightly differently.
    """

    def purchase(self, purchase_id):
        result = super(AltAddrPurchaseOrderHelper, self).purchase(purchase_id)

        purchase_order = self.env["purchase.order"].browse(purchase_id)

        if purchase_order.delivery_address_desc:
            result["delivery-address"] = purchase_order.delivery_address_desc

        elif purchase_order.alternate_shipping_address:
            result["delivery-address"] = purchase_order.alternate_shipping_address

        else:
            address_delivery = self._get_delivery_address(purchase_order)
            self._build_delivery_addr(result, "delivery-address", address_delivery)

        return result
