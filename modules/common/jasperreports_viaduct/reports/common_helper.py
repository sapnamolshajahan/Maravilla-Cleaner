# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup

from ..viaduct_helper import ViaductHelper


class CommonHelper(ViaductHelper):
    """
    Common code used in many ViaductHelpers.
    """

    def get_addr(self, partner, addr_type):
        """
        @return: a res.partner browse record of partner and type
        @param partner: usually latest partner browse record - 'o'
        @param addr_type: list of address-types in order or preference e.g. 'invoice'
        """
        addresses = partner.address_get(addr_type)
        for t in addr_type:
            if t in addresses and addresses[t] != partner.id:
                return self.env["res.partner"].browse([addresses[t]])
        return partner

    def build_company_addr(self, result, key, address):
        """
        Standard company address constructor.
        :param result:
        :param key:
        :param address:
        :return:
        """
        self.append_non_null(result, key, address.street)
        self.append_non_null(result, key, address.street2)
        self.append_non_null(result, key, address.city)
        self.append_non_null(result, key, address.state_id.name)
        self.append_non_null(result, key, address.zip, " ")
        self.append_non_null(result, key, address.country_id.name)
        if address.phone:
            self.append_non_null(result, key, "p: " + address.phone)
        if address.email:
            self.append_non_null(result, key, "e: " + address.email)
        self.append_non_null(result, key, address.website)
        if address.vat:
            taxname = address.country_id.company_tax_name or "GST No"
            self.append_non_null(result, key, f"{taxname}: {address.vat}")

    def build_partner_addr(self, result, key, address):

        if hasattr(address, 'building'):
            self.append_non_null(result, key, address.building)

        self.append_non_null(result, key, address.street)
        self.append_non_null(result, key, address.street2)
        self.append_non_null(result, key, address.city)
        self.append_non_null(result, key, address.state_id.name)
        self.append_non_null(result, key, address.zip, " ")
        self.append_non_null(result, key, address.country_id.name)

    def convert_html_for_jasper(self, html):
        """
        Convert HTML content to JasperReports-compatible HTML.
        """

        # Parse the HTML content
        soup = BeautifulSoup(html, 'html.parser')

        # Map unsupported tags to supported ones
        tag_mapping = {
            'strong': 'b',
            'em': 'i',
            'del': 'strike',
            'ins': 'u',
            'h1': 'p',  # Convert headings to paragraphs
            'h2': 'p',
            'h3': 'p',
            'h4': 'p',
            'h5': 'p',
            'h6': 'p',
        }

        # Convert tags based on mapping
        for old_tag, new_tag in tag_mapping.items():
            for tag in soup.find_all(old_tag):
                tag.name = new_tag

        # List of supported tags by JasperReports styled text
        supported_tags = {'b', 'i', 'u', 'strike', 'font', 'br', 'p', 'li', 'ol', 'ul'}

        return str(soup)
