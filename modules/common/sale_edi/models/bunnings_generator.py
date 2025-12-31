# -*- coding: utf-8 -*-
import base64
import logging
import time
import uuid
from xml.sax.saxutils import escape

import jwt
import requests
from odoo.exceptions import UserError
from odoo.addons.base_generic_changes.utils.config import configuration

from odoo import fields, models

_logger = logging.getLogger(__name__)
SECTION_NAME = "bunnings-edi-credentials"


class BunningsEDI(models.AbstractModel):
    _name = "bunnings.edi"
    _description = "Bunnings EDI Integration"

    def _get_credentials(self):
        sender_id = configuration.get(SECTION_NAME, "sender_id")
        secret_b64 = configuration.get(SECTION_NAME, "secret_key")
        endpoint_url = configuration.get(SECTION_NAME, "endpoint_url")
        if not (sender_id and secret_b64 and endpoint_url):
            raise UserError("Bunnings EDI credentials are not configured in .rc file.")
        return sender_id, secret_b64, endpoint_url

    def _generate_jwt(self, receiver, message_type):
        sender_id, secret_b64, _ = self._get_credentials()
        secret = base64.b64decode(secret_b64)
        now = int(time.time())
        payload = {
            "sub": "EDI",
            "exp": now + 3600,
            "iss": sender_id,
            "aud": receiver,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "typ": message_type,
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    # --------------------------------------------------
    # XML Builders
    # --------------------------------------------------

    def _build_invoice_xml(self, invoice, sender, receiver):
        """Build Invoice XML matching the Bunnings sample schema.
        Usage: _build_invoice_xml(self, invoice, sender, receiver)
        """

        def _get(obj, candidates, default=""):
            for c in candidates:
                try:
                    val = c(obj) if callable(c) else getattr(obj, c, None)
                    if not val:
                        continue
                    if hasattr(val, "name") and not isinstance(val, (str, int, float)):
                        val = getattr(val, "display_name", getattr(val, "name", val))
                    if isinstance(val, (fields.datetime, fields.date)):
                        val = str(val)
                    if val != "" and val is not None:
                        return val
                except Exception:
                    continue
            return default

        def _format_dt_for_sbd(dt, fmt="%Y%m%d"):
            if not dt:
                return ""
            try:
                return getattr(dt, "strftime", lambda f: dt)(fmt)
            except Exception:
                try:
                    return str(dt)
                except Exception:
                    return ""

        def _addr_block(partner, indent="                "):
            if not partner:
                return (
                    f"\n{indent}<AddressID/>"
                    f"\n{indent}<AddressName/>"
                    f"\n{indent}<Address1/>"
                    f"\n{indent}<Address2/>"
                    f"\n{indent}<Suburb/>"
                    f"\n{indent}<City/>"
                    f"\n{indent}<County/>"
                    f"\n{indent}<State/>"
                    f"\n{indent}<PinCode/>"
                    f"\n{indent}<CountryCode/>"
                    f"\n{indent}<Communications>"
                    f"\n{indent}    <ContactName/>"
                    f"\n{indent}    <TelephoneNo/>"
                    f"\n{indent}    <FaxNo/>"
                    f"\n{indent}    <MobileNo/>"
                    f"\n{indent}    <EmailAddress/>"
                    f"\n{indent}</Communications>"
                )
            # prefer edi_reference (or parent edi_reference) then fallback to DB id
            address_id = (
                    getattr(partner, "edi_reference", "")
                    or getattr(getattr(partner, "parent_id", None), "edi_reference", "")
                    or getattr(partner, "id", "")
            )
            return (
                f"\n{indent}<AddressID>{escape(str(address_id or ''))}</AddressID>"
                f"\n{indent}<AddressName>{escape(str(getattr(partner, 'name', getattr(partner, 'display_name', '')) or ''))}</AddressName>"
                f"\n{indent}<Address1>{escape(str(getattr(partner, 'street', '') or ''))}</Address1>"
                f"\n{indent}<Address2>{escape(str(getattr(partner, 'street2', '') or ''))}</Address2>"
                f"\n{indent}<City>{escape(str(getattr(partner, 'x_address3', '') or getattr(partner, 'city', '') or ''))}</City>"
                f"\n{indent}<Suburb>{escape(str(getattr(partner, 'x_suburb', '') or ''))}</Suburb>"
                f"\n{indent}<State>{escape(str(getattr(getattr(partner, 'state_id', None), 'name', getattr(partner, 'state', '') or '')))}</State>"
                f"\n{indent}<PinCode>{escape(str(getattr(partner, 'zip', '') or ''))}</PinCode>"
                f"\n{indent}<CountryCode>{escape(str(getattr(getattr(partner, 'country_id', None), 'code', '') or ''))}</CountryCode>"
                f"\n{indent}<Communications>"
                f"\n{indent}    <ContactName>{escape(str(getattr(partner, 'contact_name', '') or ''))}</ContactName>"
                f"\n{indent}    <TelephoneNo>{escape(str(getattr(partner, 'phone', '') or ''))}</TelephoneNo>"
                f"\n{indent}    <FaxNo>{escape(str(getattr(partner, 'fax', '') or ''))}</FaxNo>"
                f"\n{indent}    <MobileNo>{escape(str(getattr(partner, 'mobile', '') or ''))}</MobileNo>"
                f"\n{indent}    <EmailAddress>{escape(str(getattr(partner, 'email', '') or ''))}</EmailAddress>"
                f"\n{indent}</Communications>"
            )

        def _safe_float(x, default=0.0):
            try:
                return float(x)
            except Exception:
                return default

        sale_order = None
        for ln in getattr(invoice, "invoice_line_ids", []):
            sale_line = getattr(ln, "sale_line_id", None)
            if sale_line and getattr(sale_line, "order_id", None):
                sale_order = sale_line.order_id
                break

        # --- Header / top-level invoice fields ---
        InvoiceNo = escape(str(invoice.name or ""))
        OrderNo = escape(str(_get(invoice, ["ref"], "")))
        SalesOrderNo = escape(str(_get(invoice, ["ref"], OrderNo)))
        CRNNo = escape(str(_get(invoice, ["ref", "x_crn_no"], "")))
        InvoiceDate = _format_dt_for_sbd(getattr(invoice, "invoice_date", None), "%Y%m%d")
        InvoiceType = escape(str("9" if invoice.move_type == "out_invoice" else "381"))
        DespatchAdviceNo = escape(str(_get(invoice, ["x_despatch_no", "carrier_tracking_ref"], "")))
        DespatchDate = _format_dt_for_sbd(_get(invoice, ["x_despatch_date", "date"], None), "%Y%m%d")
        SenderTaxNo = escape(str(_get(getattr(invoice, "company_id", None), ["vat", "x_tax_no"], "")))
        ReceiverTaxNo = escape(str(_get(invoice.partner_id, ["vat"], "")))
        CurrencyCode = (
                getattr(getattr(invoice, "currency_id", None), "name", None)
                or getattr(getattr(getattr(sale_order, "pricelist_id", None), "currency_id", None), "name", None)
                or getattr(getattr(getattr(invoice, "company_id", None), "currency_id", None), "name", None)
                or ""
        )
        LanguageID = escape(str(_get(getattr(invoice, "partner_id", None), ["lang"], "en")))

        # --- Addresses ---
        BuyerAddr = _addr_block(getattr(invoice, "partner_id", None))
        CustomerAddr = _addr_block(getattr(invoice, "partner_id", None))
        invoice_partner = getattr(invoice, "partner_id", None)
        if invoice_partner and invoice_partner.parent_id:
            head_office = invoice_partner.parent_id
        else:
            head_office = invoice_partner
        InvoiceToAddr = _addr_block(head_office)  # ✅ Changed to Head Office
        RemitToAddr = _addr_block(getattr(getattr(invoice, "company_id", None), "partner_id", None))
        ShipToAddr = _addr_block(getattr(invoice, "partner_shipping_id", getattr(invoice, "partner_id", None)))
        SupplierAddr = _addr_block(getattr(getattr(invoice, "company_id", None), "partner_id", None))
        UltimateConsigneeAddr = _addr_block(None)

        # --- Totals ---
        NetTotal = f"{_safe_float(getattr(invoice, 'amount_untaxed', 0.0)):.2f}"
        NetTax = f"{_safe_float(getattr(invoice, 'amount_tax', 0.0)):.2f}"
        TotalTax = NetTax
        InvoiceTotal = f"{_safe_float(getattr(invoice, 'amount_total', 0.0)):.2f}"
        Charges = escape(str(_get(invoice, ["x_charges"], "")))
        ChargesTaxRate = escape(str(_get(invoice, ["x_charges_tax_rate"], "")))
        TaxOnCharges = escape(str(_get(invoice, ["x_tax_on_charges"], "")))
        TaxType = escape(str(_get(invoice, ["x_tax_type"], "GST")))

        # --- Build line items using invoice.invoice_line_ids (ASN-style logic) ---
        line_items_xml = []
        line_no = 0
        total_quantity = 0.0

        for ln in getattr(invoice, "invoice_line_ids", []):
            if getattr(ln, "display_type", "") in ("line_section", "line_note"):
                continue

            line_no += 1

            qty_invoiced = getattr(ln, "quantity", 0.0)
            total_quantity += _safe_float(qty_invoiced)

            sale_line = getattr(ln, "sale_line_id", None)
            qty_ordered = getattr(sale_line, "product_uom_qty", 0.0) if sale_line else 0.0

            product = getattr(ln, "product_id", None)
            product_id = escape(str(getattr(product, "id", "")))
            vendor_sku = escape(str(getattr(product, "default_code", "") or ""))
            gtin = escape(str(getattr(product, "barcode", "") or ""))
            product_name = escape(
                str(getattr(ln, "name", getattr(product, "display_name", getattr(product, "name", ""))) or "")
            )

            uom = escape(str(getattr(getattr(ln, "product_uom_id", None), "name", "")))

            unit_price = _safe_float(getattr(ln, "price_unit", 0.0))
            net_total = _safe_float(getattr(ln, "price_subtotal", 0.0))
            price_total = _safe_float(getattr(ln, "price_total", net_total))
            tax_amount = price_total - net_total

            pack_size = escape(str(getattr(product, "x_pack_size", "") or ""))
            retail_units = pack_size or "1"

            # tax rate
            tax_rate = ""
            try:
                taxes = getattr(ln, "tax_ids", None)
                if taxes:
                    t = taxes[0] if hasattr(taxes, "__getitem__") else taxes
                    tax_rate = str(int(getattr(t, "amount", 0) or 0))
            except Exception:
                tax_rate = ""

            line_xml = f"""
                        <LineItem>
                            <LineNo>{line_no}</LineNo>
                            <CustomerOrderLineNo>{escape(str(getattr(ln, 'x_customer_line_no', line_no)))}</CustomerOrderLineNo>
                            <ProductID>{product_id}</ProductID>
                            <VendorSKU>{vendor_sku}</VendorSKU>
                            <GTIN>{gtin}</GTIN>
                            <TradeUnitGTIN/>
                            <ProductName>{product_name}</ProductName>
                            <Quantity>{_safe_float(qty_invoiced):.2f}</Quantity>
                            <UoMID>{uom}</UoMID>
                            <PackSize>{pack_size}</PackSize>
                            <UnitPrice>{unit_price:.2f}</UnitPrice>
                            <PriceUOM>Shipper</PriceUOM>
                            <RetailUnitsInTradeUnit>{retail_units}</RetailUnitsInTradeUnit>
                            <NetTotal>{net_total:.2f}</NetTotal>
                            <TaxType>{TaxType}</TaxType>
                            <TaxRate>{tax_rate}</TaxRate>
                            <TaxAmount>{tax_amount:.2f}</TaxAmount>
                            <DiscountRate>{ln.discount:.2f}</DiscountRate>
                            <DiscountAmount>{(ln.price_unit * ln.quantity * ln.discount / 100):.2f}</DiscountAmount>
                            <LineTotal>{price_total:.2f}</LineTotal>
                            <CurrencyCode>{CurrencyCode}</CurrencyCode>
                            <LanguageId>{LanguageID}</LanguageId>
                            <Notes/>
                        </LineItem>""".rstrip()
            line_items_xml.append(line_xml)

        NoOfLines = str(len(line_items_xml))
        TotalQuantity = f"{total_quantity:.2f}"

        # Header XML
        header_xml = f"""
        <Header>
            <Sender><Identifier>{escape(str(sender))}</Identifier></Sender>
            <Receiver><Identifier>{escape(str(receiver))}</Identifier></Receiver>
            <MessageType>INV</MessageType>
            <DocumentDirection>Outbound</DocumentDirection>
            <DocumentIdentifier>{escape(str(invoice.id or InvoiceNo))}</DocumentIdentifier>
            <DocumentDate>{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}</DocumentDate>
            <TestFlag>1</TestFlag>
        </Header>
        """

        # Body XML
        body_xml = f"""
                <Body>
                    <InvoiceNo>{InvoiceNo}</InvoiceNo>
                    <OrderNo>{OrderNo}</OrderNo>
                    <SalesOrderNo>{SalesOrderNo}</SalesOrderNo>
                    <CRNNo>{CRNNo}</CRNNo>
                    <InvoiceDate>{InvoiceDate}</InvoiceDate>
                    <InvoiceType>{InvoiceType}</InvoiceType>
                    <CustomerReferenceNo/>
                    <DespatchAdviceNo>{DespatchAdviceNo}</DespatchAdviceNo>
                    <DespatchDate>{DespatchDate}</DespatchDate>
                    <SenderTaxNo>{SenderTaxNo}</SenderTaxNo>
                    <ReceiverTaxNo>{ReceiverTaxNo}</ReceiverTaxNo>
                    <CurrencyCode>{CurrencyCode}</CurrencyCode>
                    <LanguageID>{LanguageID}</LanguageID>
                    <Addresses>
                        <Buyer>{BuyerAddr}</Buyer>
                        <Customer>{CustomerAddr}</Customer>
                        <InvoiceTo>{InvoiceToAddr}</InvoiceTo>
                        <RemitTo>{RemitToAddr}</RemitTo>
                        <ShipTo>{ShipToAddr}</ShipTo>
                        <Supplier>{SupplierAddr}</Supplier>
                        <UltimateConsignee>{UltimateConsigneeAddr}</UltimateConsignee>
                    </Addresses>
                    <NetTotal>{NetTotal}</NetTotal>
                    <TaxType>{TaxType}</TaxType>
                    <NetTax>{NetTax}</NetTax>
                    <Charges>{Charges}</Charges>
                    <ChargesTaxRate>{ChargesTaxRate}</ChargesTaxRate>
                    <TaxOnCharges>{TaxOnCharges}</TaxOnCharges>
                    <TotalTax>{TotalTax}</TotalTax>
                    <InvoiceTotal>{InvoiceTotal}</InvoiceTotal>
                    <TotalQuantity>{TotalQuantity}</TotalQuantity>
                    <NoOfLines>{NoOfLines}</NoOfLines>
                    <Notes/>
                    <LineItems>
        {"".join(line_items_xml)}
                    </LineItems>
                </Body>
                """

        full = '<?xml version="1.0" encoding="utf-8"?>\n' + f"<StandardBusinessDocument>\n{header_xml}\n{body_xml}\n</StandardBusinessDocument>"
        return full

    def _build_asn_xml(self, picking, sender, receiver):
        """Build a detailed ASN XML matching the sample structure.
        - Adds many Body-level tags (ASNNo, OrderNo, ASNType, DespatchDate, TrackingNo, etc.)
        - Produces <LineItems><LineItem>... with fields similar to sample
        - Uses defensive get-field helpers with multiple fallbacks
        """

        def _get(obj, candidates, default=""):
            """Try a list of attribute names (or callables) on obj and return the first non-empty."""
            for c in candidates:
                try:
                    if callable(c):
                        val = c(obj)
                    else:
                        attrs = c.split('.')
                        if len(attrs) == 1:
                            val = getattr(obj, c, None)
                        else:
                            sub_obj = getattr(obj, attrs[0], None)
                            if not sub_obj:
                                val = None
                            else:
                                val = getattr(sub_obj, '.'.join(attrs[1:]), None)

                    if not val:  # catches None, False, empty, 0
                        continue
                    # If it's a record (res.partner, product, etc), try its common display attrs
                    if hasattr(val, "name") and not isinstance(val, (str, int, float)):
                        val = getattr(val, "display_name", getattr(val, "name", val))
                    if isinstance(val, (fields.datetime, fields.date)):
                        val = str(val)
                    if val != "" and val is not None:
                        return val
                except Exception:
                    continue
            return default

        def _format_dt_for_sbd(dt):
            """Return string in YYYYMMDDhhmmss (used in sample). Accepts date/datetime/str."""
            if not dt:
                return ""
            try:
                return getattr(dt, "strftime", lambda fmt: dt)("%Y%m%d%H%M%S")
            except Exception:
                try:
                    return str(dt)
                except Exception:
                    return ""

        def _format_date_iso(dt):
            if not dt:
                return ""
            try:
                return getattr(dt, "strftime", lambda fmt: dt)("%Y-%m-%d")
            except Exception:
                return str(dt)

        # Basic Body fields mapping
        ASNNo = escape(str(_get(picking, ["name", "asn_no", lambda r: getattr(r, "reference", None),
                                          lambda r: getattr(r, "origin", None)], picking.name)))
        OrderNo = picking.sale_id.client_order_ref

        asn_date_obj = _get(picking, ["scheduled_date", "date_done", "create_date", "date"], None)
        ASNDate = _format_dt_for_sbd(asn_date_obj) or _format_dt_for_sbd(fields.Datetime.now())
        ASNType = escape(
            str(_get(picking, ["asn_type", "picking_type_code", "picking_type_id.code"], "")))
        DespatchDate = _format_dt_for_sbd(_get(picking, ["scheduled_date", "min_date", "date_done"], None))
        EstimatedArrivalDate = _format_dt_for_sbd(
            _get(picking, ["expected_date", "date_expected", "estimated_delivery_date"], None))
        TrackingNo = escape(
            str(_get(picking, ["carrier_tracking_ref", "carrier_tracking_number", "tracking_number", "tracking_ref"],
                     "")))
        SalesOrderNo = escape(str(_get(picking, ["sale_id.name", "sale_id.client_order_ref", "origin"], "")))
        OrderDate = _format_dt_for_sbd(_get(picking, ["sale_id.confirmation_date", "sale_id.date_order", "date"], None))

        def _addr_block(tag, partner):
            if not partner:
                return f"""
                    <{tag}>
                        <AddressID/>
                        <AddressName></AddressName>
                        <Address1/>
                        <Address2/>
                        <City/>
                        <PinCode/>
                    </{tag}>
                """
            # ✅ Prefer child's edi_reference, only fallback to parent's if empty
            child_ref = (getattr(partner, "edi_reference", None) or "").strip()
            parent_ref = (getattr(partner.parent_id, "edi_reference", None) or "").strip() if partner.parent_id else ""
            address_id = child_ref if child_ref else parent_ref

            return f"""
                <{tag}>
                    <AddressID>{escape(str(address_id or ''))}</AddressID>
                    <AddressName>{escape(str(getattr(partner, 'name', getattr(partner, 'display_name', ''))))}</AddressName>
                    <Address1>{escape(str(getattr(partner, 'street', '') or ''))}</Address1>
                    <Address2>{escape(str(getattr(partner, 'street2', '') or ''))}</Address2>
                    <City>{escape(str(getattr(partner, 'city', '') or ''))}</City>
                    <PinCode>{escape(str(getattr(partner, 'zip', '') or ''))}</PinCode>
                </{tag}>
            """

        BuyerAddr = _addr_block("Buyer", getattr(picking.sale_id, "partner_id", None))
        ShipToAddr = _addr_block("ShipTo", getattr(picking, "partner_id", None))
        UltimateConsigneeAddr = _addr_block("UltimateConsignee", getattr(picking, "partner_id", None))
        invoice_partner = getattr(picking, "partner_invoice_id", getattr(picking, "partner_id", None))
        if invoice_partner and invoice_partner.parent_id:
            head_office = invoice_partner.parent_id
        else:
            head_office = invoice_partner
        InvoiceToAddr = _addr_block("InvoiceTo", head_office)

        # Additional shipment meta
        DockNo = escape(str(_get(picking, ["dock_no", "picking_type_id.warehouse_id.code", "location_id.name"], "")))
        ConsignmentNoteNo = escape(
            str(_get(picking, ["consignment_note_no", "carrier_consignment", "carrier_tracking_ref"], "")))
        SSCC = escape(str(_get(picking, ["carrier_id.gln"], "")))
        SCACCode = escape(str(_get(picking, ["carrier_id.gln"], "")))
        ShippingAgentCode = escape(str(_get(picking, ["carrier_id.gln"], "")))
        ShipmentMethod = escape(str(_get(picking, ["carrier_id.name", "shipping_method", "shipping_method_code"], "")))
        ShippingAgentService = escape(str(getattr(picking.carrier_id, "name", "")))
        BillOfLading = escape(str(_get(picking, ["bill_of_lading", "manifest", "name"], "")))
        ShipmentRefNo = escape(str(_get(picking, ["reference", "shipment_reference", "name"], "")))
        ScanPack = escape(str(_get(picking, ["scan_pack", "packed", "package_ids"], "")))

        # Weight / dimensions
        def _safe_float(x, default=0.0):
            try:
                return float(x)
            except Exception:
                return default

        weight = _get(picking, ["weight", "total_weight", "net_weight", "package_weight"], None)
        if weight in (None, ""):
            w_sum = 0.0
            for mv in getattr(picking, "move_lines", []):
                qty = _get(mv, ["quantity_done", "product_uom_qty", "qty_done"], 0)
                prod = getattr(mv, "product_id", None)
                pw = _get(prod, ["weight", "weight_net", "product_weight"], 0) if prod else 0
                w_sum += _safe_float(pw) * _safe_float(qty)
            weight = w_sum
        Weight = f"{_safe_float(weight):.4f}"
        WeightUoMID = escape(str(_get(picking, ["weight_uom", "weight_uom_id.name"], "KG")))

        Length = escape(str(_get(picking, ["length", "dimension_length", "package_length"], "")))
        Width = escape(str(_get(picking, ["width", "dimension_width", "package_width"], "")))
        Height = escape(str(_get(picking, ["height", "dimension_height", "package_height"], "")))
        DimensionUoMID = escape(str(_get(picking, ["dimension_uom", "dimension_uom_id.name"], "CM")))

        NoOfPallets = escape(str(getattr(picking, "pallet_qty", "")))
        NoOfCartons = escape(str(getattr(picking, "carton_qty", "")))
        GLNCode = escape(str(getattr(picking.carrier_id, "gln", "")))

        CurrencyCode = escape(
            str(_get(picking, ["sale_id.currency_id.name", "company_id.currency_id.name", "currency_id.name"], "")))
        LanguageID = escape(
            str(_get(picking, ["partner_id.lang", "sale_id.partner_id.lang", "company_id.partner_id.lang"], "")))

        # Build line items
        line_items_xml = []
        line_no = 0
        line_src = getattr(picking, "move_line_ids", None) or getattr(picking, "move_lines", [])
        for ml in line_src:
            line_no += 1
            sale_line = getattr(ml, "sale_line_id", None) or getattr(getattr(ml, "move_id", None), "sale_line_id", None)
            qty_ordered = _get(sale_line, ["product_uom_qty", "product_uom_qty"], 0) if sale_line else 0
            qty_shipped = _get(ml, ["qty_done", "quantity_done", "product_uom_qty", "quantity"], 0)
            product = getattr(ml, "product_id", None) or getattr(getattr(ml, "move_id", None), "product_id", None)
            product_id = escape(str(getattr(product, "id", "")))
            vendor_sku = escape(str(getattr(product, "default_code", "") or ""))
            gtin = escape(str(getattr(product, "barcode", "") or ""))
            product_name = escape(str(getattr(product, "display_name", getattr(product, "name", "")) or ""))
            ordered_uom = escape(str(getattr(ml, "product_uom_id",
                                             getattr(ml, "product_uom", None) and getattr(ml, "product_uom",
                                                                                          None)).name if getattr(ml,
                                                                                                                 "product_uom_id",
                                                                                                                 None) else ""))
            uom = ordered_uom or escape(str(getattr(product, "uom_id", getattr(product, "uom_po_id", None)) and getattr(
                getattr(product, "uom_id", getattr(product, "uom_po_id", None)), "name", "")))
            unit_price = _get(sale_line, ["price_unit", "price_subtotal", "price"], None) or _get(product,
                                                                                                  ["list_price",
                                                                                                   "standard_price",
                                                                                                   "price"], 0.0)

            line_xml = (
                "<LineItem>"
                f"<LineNo>{line_no}</LineNo>"
                f"<CustomerOrderLineNo>{escape(str(getattr(ml, 'customer_order_line_no', '') or line_no))}</CustomerOrderLineNo>"
                f"<ProductID>{product_id}</ProductID>"
                f"<VendorSKU>{vendor_sku}</VendorSKU>"
                f"<GTIN>{gtin}</GTIN>"
                f"<ProductName>{product_name}</ProductName>"
                f"<QuantityOrdered>{_safe_float(qty_ordered):.4f}</QuantityOrdered>"
                f"<OrderedUoMID>{ordered_uom or uom or ''}</OrderedUoMID>"
                f"<QuantityShipped>{_safe_float(qty_shipped):.4f}</QuantityShipped>"
                f"<UoMID>{uom or ''}</UoMID>"
                f"<UnitPrice>{_safe_float(unit_price):.4f}</UnitPrice>"
                "</LineItem>"
            )
            line_items_xml.append(line_xml)

        NoOfLines = str(len(line_items_xml))

        # Compose the XML
        body_xml = f"""
            <Body>
                <ASNNo>{ASNNo}</ASNNo>
                <OrderNo>{OrderNo}</OrderNo>
                <ASNDate>{ASNDate}</ASNDate>
                <ASNType>{ASNType}</ASNType>
                <DespatchDate>{DespatchDate}</DespatchDate>
                <EstimatedArrivalDate>{EstimatedArrivalDate}</EstimatedArrivalDate>
                <TrackingNo>{TrackingNo}</TrackingNo>
                <SalesOrderNo>{SalesOrderNo}</SalesOrderNo>
                <OrderDate>{OrderDate}</OrderDate>
                <Addresses>
                    {BuyerAddr}
                    {ShipToAddr}
                    {UltimateConsigneeAddr}
                    {InvoiceToAddr}
                </Addresses>
                <NoOfLines>{NoOfLines}</NoOfLines>
                <LineItems>
                    {"".join(line_items_xml)}
                </LineItems>

                <DockNo>{DockNo}</DockNo>
                <ConsignmentNoteNo>{ConsignmentNoteNo}</ConsignmentNoteNo>
                <SSCC>{SSCC}</SSCC>
                <SCACCode>{SCACCode}</SCACCode>
                <ShippingAgentCode>{ShippingAgentCode}</ShippingAgentCode>
                <ShipmentMethod>{ShipmentMethod}</ShipmentMethod>
                <ShippingAgentService>{ShippingAgentService}</ShippingAgentService>
                <BillOfLading>{BillOfLading}</BillOfLading>
                <ShipmentRefNo>{ShipmentRefNo}</ShipmentRefNo>
                <ScanPack>{ScanPack}</ScanPack>
                <Weight>{Weight}</Weight>
                <WeightUoMID>{WeightUoMID}</WeightUoMID>
                <Length>{Length}</Length>
                <Width>{Width}</Width>
                <Height>{Height}</Height>
                <DimensionUoMID>{DimensionUoMID}</DimensionUoMID>
                <NoOfPallets>{NoOfPallets}</NoOfPallets>
                <NoOfCartons>{NoOfCartons}</NoOfCartons>
                <GLNCode>{GLNCode}</GLNCode>
                <CurrencyCode>{CurrencyCode}</CurrencyCode>
                <LanguageID>{LanguageID}</LanguageID>
            </Body>
        """

        header_xml = f"""
        <Header>
            <Sender><Identifier>{escape(str(sender))}</Identifier></Sender>
            <Receiver><Identifier>{escape(str(receiver))}</Identifier></Receiver>
            <MessageType>ASN</MessageType>
            <DocumentDirection>Outbound</DocumentDirection>
            <DocumentIdentifier>{escape(str(picking.name or ''))}</DocumentIdentifier>
            <DocumentDate>{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}</DocumentDate>
            <TestFlag>0</TestFlag>
        </Header>
        """

        full = f"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<StandardBusinessDocument>\n{header_xml}\n{body_xml}\n</StandardBusinessDocument>"
        return full

    def _build_xml(self, sender, receiver, message_type, document):
        """Dispatcher for XML builders"""
        if message_type == "INV":
            return self._build_invoice_xml(document, sender, receiver)
        elif message_type == "ASN":
            return self._build_asn_xml(document, sender, receiver)
        else:
            raise UserError(f"Unsupported message type: {message_type}")

    # --------------------------------------------------
    # Send Logic
    # --------------------------------------------------

    def send_edi(self, partner, document, message_type="INV"):
        edi_gen = partner.parent_id.edi_generator if partner.parent_id else partner.edi_generator

        if message_type == "INV":
            # Invoices always use the partner’s own edi_reference
            edi_ref = partner.edi_reference
        else:
            edi_ref = partner.parent_id.edi_reference if partner.parent_id else partner.edi_reference

        _logger.info(
            "EDI check for partner=%s edi_generator=%s edi_ref=%s message_type=%s",
            partner.display_name,
            edi_gen,
            edi_ref,
            message_type,
        )

        if edi_gen != "bunnings":
            _logger.warning("EDI not sent. EDI generator %s not allowed", edi_gen)
            return False

        # Receiver: use edi_reference if provided, else fallback to "bunnings"
        receiver = edi_ref or "bunnings"

        sender_id, _, endpoint_url = self._get_credentials()
        xml_body = self._build_xml(sender_id, receiver, message_type, document)
        _logger.info("EDI XML Body: %s", xml_body)

        token = self._generate_jwt(receiver, message_type)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/xml",
        }

        try:
            response = requests.post(endpoint_url, data=xml_body.encode("utf-8"), headers=headers)
            _logger.info("EDI POST %s -> %s", endpoint_url, response.status_code)
            response.raise_for_status()
            document.sudo().update({"edi_sent": fields.Datetime.now()})
            _logger.info(
                "EDI %s sent successfully for %s (Partner %s, edi_reference=%s)",
                message_type,
                getattr(document, "name", document.id),
                partner.id,
                edi_ref,
            )
            return True
        except Exception as e:
            _logger.exception("EDI sending failed: %s", e)
            return False