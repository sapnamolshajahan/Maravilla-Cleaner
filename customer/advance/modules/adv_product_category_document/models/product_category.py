from odoo import models, fields, api


class ProductCategoryDocument(models.Model):
    _name = 'product.category.document'
    _description = 'Product Category Documents'

    name = fields.Char(string='Document Name', required=True)
    file = fields.Binary(string='Document File', required=True)
    filename = fields.Char(string='File Name')
    category_id = fields.Many2one('product.category', string='Product Category', ondelete='cascade')
    ir_attachment_id = fields.Many2one('ir.attachment', string="Attachment")

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('file'):
                attachment = self.env['ir.attachment'].create({
                    'name': vals.get('filename'),
                    'datas': vals.get('file'),
                    'res_model': 'product.category.document',
                })
                vals['ir_attachment_id'] = attachment.id
        return super(ProductCategoryDocument, self).create(vals_list)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    document_ids = fields.One2many('product.category.document', 'category_id', string='Documents')
    document_count = fields.Integer(string="Document Count", compute='_compute_document_count')

    def action_open_documents(self):
        """Open related documents in a tree view"""
        self.ensure_one()
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'product.category.document',
            'view_mode': 'kanban,list',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
            'target': 'current',
        }

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    def action_open_category_documents(self):
        """Open the wizard to add a document"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Document',
            'res_model': 'category.document.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('adv_product_category_document.view_category_document_wizard_form').id,
            'target': 'new',  # Opens as a popup
            'context': {
                'default_category_id': self.id
            },
        }


class CategoryDocumentWizard(models.TransientModel):
    _name = 'category.document.wizard'
    _description = 'Wizard to add documents to product category'

    name = fields.Char(string="Document Name", required=True)
    file = fields.Binary(string="Upload File", required=True)
    filename = fields.Char(string="File Name")
    category_id = fields.Many2one('product.category', string="Category")

    def action_add_document(self):
        """Create the document record linked to the category"""
        self.env['product.category.document'].create({
            'name': self.name,
            'file': self.file,
            'filename': self.filename or self.name,
            'category_id': self.category_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}


