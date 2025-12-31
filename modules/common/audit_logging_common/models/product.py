# -*- coding: utf-8 -*-

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    _excluded_values = []

    @api.model
    def _get_record_name(self, record):
        """Required for audit logging"""
        return "Product Template"

    @api.model
    def create(self, values):
        print("valuessssss",values)
        return self.env["audit.logging"].create_with_log(ProductTemplate, self, values)

    def write(self, values):
        return self.env["audit.logging"].write_with_log(ProductTemplate, self, values)

    def unlink(self):
        return self.env["audit.logging"].unlink_with_log(ProductTemplate, self)


class ProductProduct(models.Model):
    _inherit = "product.product"

    _excluded_values = []

    @api.model
    def _get_record_name(self, record):
        """Required for audit logging"""
        return "Product Product"

    @api.model
    def create(self, values):
        return self.env["audit.logging"].create_with_log(ProductProduct, self, values)

    def write(self, values):
        return self.env["audit.logging"].write_with_log(ProductProduct, self, values)

    def unlink(self):
        return self.env["audit.logging"].unlink_with_log(ProductProduct, self)


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    _excluded_values = []

    @api.model
    def _get_record_name(self, record):
        """Required for audit logging"""
        return "Product Supplier Information"

    @api.model
    def create(self, values):
        return self.env["audit.logging"].create_with_log(ProductSupplierInfo, self, values)

    def write(self, values):
        return self.env["audit.logging"].write_with_log(ProductSupplierInfo, self, values)

    def unlink(self):
        return self.env["audit.logging"].unlink_with_log(ProductSupplierInfo, self)


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    _excluded_values = []

    @api.model
    def _get_record_name(self, record):
        """Required for audit logging"""
        return "Product Pricelist Information"

    @api.model
    def create(self, values):
        return self.env["audit.logging"].create_with_log(ProductPricelist, self, values)

    def write(self, values):
        return self.env["audit.logging"].write_with_log(ProductPricelist, self, values)

    def unlink(self):
        return self.env["audit.logging"].unlink_with_log(ProductPricelist, self)


class ProductPricelistLine(models.Model):
    _inherit = "product.pricelist.item"

    _excluded_values = []

    @api.model
    def _get_record_name(self, record):
        """Required for audit logging"""
        return "Product Supplier Information"

    @api.model
    def create(self, values):
        return self.env["audit.logging"].create_with_log(ProductPricelistLine, self, values)

    def write(self, values):
        return self.env["audit.logging"].write_with_log(ProductPricelistLine, self, values)

    def unlink(self):
        return self.env["audit.logging"].unlink_with_log(ProductPricelistLine, self)
