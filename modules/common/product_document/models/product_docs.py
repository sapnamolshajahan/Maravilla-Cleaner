# coding: utf-8
from odoo import fields, models, api
from odoo.exceptions import UserError


class ProductDocs(models.Model):
    _name = 'product.docs'
    _description = 'Product Document'
    _rec_name = 'document_name'

    product_tmpl_id = fields.Many2one('product.template', 'Product')
    product_id = fields.Many2one('product.product', 'Product Variant')
    document_name = fields.Char('Document Name', required=True)
    document_desc = fields.Char('Document Description')
    document_att = fields.Binary('Attachment', required=True)
    file_name = fields.Char(string='File Name')
    document_url = fields.Char('Document URL')

    @api.model_create_multi
    def create(self, values):
        res = super().create(values)
        for vals in values:
            if vals.get('document_name'):
                attachment = self.env['ir.attachment'].sudo().create({
                    'name': vals.get('document_name'),
                    'datas': vals.get('document_att'),
                })
                product_folder = self.env['documents.document'].sudo().search([
                    ('name', '=', 'Products'),
                    ('type', '=', 'folder')
                ], limit=1)
                document = self.env['documents.document'].sudo().create({
                    'name': vals.get('document_name'),
                    'attachment_id': attachment.id,
                    'folder_id': product_folder.id,
                    'res_model': 'product.docs',
                    'res_id': res.id,
                })
                if document:
                    res.document_url = document.access_url
        return res

    def open_product_document(self):
        document = self.env['documents.document'].sudo().search([
            ('res_model', '=', 'product.docs'),
            ('res_id', '=', self.id)
        ], limit=1)

        if not document:
            raise UserError("No related document found.")

        if self.document_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.document_url,
                'target': 'new'
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Document',
            'view_mode': 'kanban,list',
            'res_model': 'documents.document',
            'domain': [('id', '=', document.id)],
            'target': 'current',
        }
