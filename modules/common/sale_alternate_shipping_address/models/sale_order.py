# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

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

    def _compute_alternate_shipping_address(self):
        for so in self:
            if any([so.alt_street, so.alt_street2]):
                so.alternate_shipping_address = so._make_alt_addr_from_fields()
            else:
                so.alternate_shipping_address = False

    ###########################################################################
    # Fields
    ###########################################################################
    show_alt_delivery_address = fields.Boolean(string='Show Alt Shipping Address',
                                               default=lambda self: self.env.company.show_hide_alt_so_address)

    alternate_shipping_address = fields.Text(string="Alt. Shipping Address",
                                             compute="_compute_alternate_shipping_address")

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
