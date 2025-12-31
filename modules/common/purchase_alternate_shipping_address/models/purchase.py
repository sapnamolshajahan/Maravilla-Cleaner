# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _make_alt_addr_from_fields(self):
        lines = []
        if self.alt_contact:
            lines.append("ATT:{}".format(self.alt_contact.strip()))
        if self.alt_building:
            lines.append(self.alt_building)
        if self.alt_street:
            lines.append(self.alt_street.strip())
        if self.alt_street2:
            lines.append(self.alt_street2.strip())
        if len(lines) < 2:
            return ''
        if self.alt_city:
            city = self.alt_city.strip()
            if self.alt_zip:
                city += ' ' + self.alt_zip
            lines.append(city)
        if self.alt_state_id:
            lines.append(self.alt_state_id.name)

        lines.append(self.alt_country_id.name or self.company_id.partner_id.country_id.name or 'New Zealand')
        if self.alt_phone:
            lines.append("ph:{}".format(self.alt_phone.strip()))

        return '\n'.join(lines)

    def _compute_alternate_delivery_address(self):
        for po in self:
            if po.alternate_shipping_address_text:
                lines = po.alternate_shipping_address_text.replace(',', '\n').split('\n')
                po.alternate_shipping_address = '\n'.join([line.strip() for line in lines])
            elif any([po.alt_street, po.alt_street2]):
                po.alternate_shipping_address = po._make_alt_addr_from_fields()
            else:
                po.alternate_shipping_address = False

    def _compute_is_alt_address_separate_fields(self):
        for po in self:
            po.is_alt_address_separate_fields = any([po.alt_street, po.alt_street2])

    ###########################################################################
    # Fields
    ###########################################################################
    show_alt_delivery_address = fields.Boolean(string='Show Alt Delivery Address',
                                               default=lambda self: self.env.company.show_hide_alt_po_address)
    alternate_shipping_address_text = fields.Text(string="Alt Delivery Address(OLD)")
    alternate_shipping_address = fields.Text(string="Alt Delivery Address",
                                             compute="_compute_alternate_delivery_address")

    alt_contact = fields.Char('Contact Person')
    alt_phone = fields.Char('Phone Number')
    alt_building = fields.Char('Building/Unit/Flat')
    alt_street = fields.Char()
    alt_street2 = fields.Char()
    alt_zip = fields.Char(change_default=True)
    alt_city = fields.Char()
    alt_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    alt_country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    alt_email = fields.Char()
    is_alt_address_separate_fields = fields.Boolean(compute='_compute_is_alt_address_separate_fields')
