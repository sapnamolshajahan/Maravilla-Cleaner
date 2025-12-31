# coding: utf-8
from odoo import _, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_doc_ids = fields.One2many('product.docs', 'product_tmpl_id', 'Product Document')

    def upload_product_document(self):
        view_id = self.env.ref('product_document.view_product_docs_form').id
        return {
            'name': _('Product Document'),
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'product.docs',
            'type': 'ir.actions.act_window',
            'context': {
                'default_product_tmpl_id': self.id,
            },
            'target': 'new',
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_doc_ids = fields.One2many('product.docs', 'product_id', 'Product Document')

    def upload_product_document(self):
        view_id = self.env.ref('product_document.view_product_docs_form').id
        return {
            'name': _('Product Document'),
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'product.docs',
            'type': 'ir.actions.act_window',
            'context': {
                'default_product_id': self.id,
            },
            'target': 'new',
        }
