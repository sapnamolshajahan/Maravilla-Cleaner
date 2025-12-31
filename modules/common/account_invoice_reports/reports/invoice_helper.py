# -*- coding: utf-8 -*-
from odoo.addons.account_basic_invoice_reports.reports.invoice_helper import BasicInvoiceHelper


class StandardInvoiceHelper(BasicInvoiceHelper):
    """
    This invoice helper supplies data for:
        * invoice.jrxml
        * credit.jrxml
    """

    def invoice(self, invoice_id):

        invoice = self.env["account.move"].browse(invoice_id)

        result = super(StandardInvoiceHelper, self).invoice(invoice_id)

        # Delivery Addresses
        result["delivery-address"] = ""
        sale = self.get_sale0(invoice)
        if sale:
            self.build_delivery_addr("delivery-address", result, sale)

        if invoice.move_type != "out_invoice" and invoice.amount_total_signed < 0:
            # Credit Note references
            picking = self.get_picking0(invoice)
            result["customer-rfc-ref"] = picking.customer_return_reference or ""
        else:
            result["customer-rfc-ref"] = ""

        return result

    def get_sale0(self, invoice):
        """
        :param invoice:
        :return: (possibly empty) sale.order recordset associated with the invoice.
        """
        for sale in invoice.sale_orders:
            return sale
        return self.env["sale.order"]

    def get_picking0(self, invoice):
        """
        Get the first packing/picking associated with the invoice.

        :param invoice: account.move browse record
        :return: stock.picking record-set, possibly empty
        """
        for picking in invoice.picking_ids:
            return picking
        return self.env["stock.picking"]

    def build_delivery_addr(self, key, result, sale_order):
        """
        Build delivery-address, for invoices relating to sales orders
        """
        if hasattr(sale_order, "alternate_shipping_address") and sale_order.alternate_shipping_address:
            # Alternate shipping address has been installed and
            # the alternate_shipping_address field is available
            result[key] = sale_order.alternate_shipping_address
        else:
            self.build_partner_addr(result, key, sale_order.partner_shipping_id)

    def _get_customer_reference(self, invoice):
        """
        Get the customer reference for different types of invoices
        :param invoice: account invoice browse record.
        :returns Customer reference
        """
        customer_reference = super(StandardInvoiceHelper, self)._get_customer_reference(invoice)

        sale = self.get_sale0(invoice)
        if sale:
            customer_reference = sale.client_order_ref or ""

        if not customer_reference and invoice.move_type == "out_refund" and invoice.invoice_origin:
            # Credit Note
            for credit in self.env["account.move"].search([("name", "=", invoice.invoice_origin)]):
                if self.get_sale0(credit):
                    return credit.invoice_origin or ""

        return customer_reference
