# -*- coding: utf-8 -*-

from odoo import models,fields, tools, api


class MRPWorcenter(models.Model):
    _inherit = 'mrp.workcenter'

    type = fields.Selection([('normal','Normal'),('outwork','Outwork')], string='Type')

    partner = fields.Many2one(comodel_name='res.partner', string='Supplier',
                              domain="[('supplier_rank','>',0),('is_company','=',True)]")
    product = fields.Many2one(comodel_name='product.product', string='Product',
                              domain="[('type','=','service')]")


class MRPWorkorder(models.Model):
    _inherit='mrp.workorder'

    type = fields.Selection([('normal', 'Normal'), ('outwork', 'Outwork')], string='Type')
    partner = fields.Many2one(comodel_name='res.partner', string='Supplier',
                                 domain="[('supplier_rank','>',0),('is_company','=',True)]")
    product = fields.Many2one(comodel_name='product.product', string='Product',
                              domain="[('type','=','service')]")
    purchase_order = fields.Many2one(comodel_name='purchase.order', string='Purchase Order')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('workcenter_id', None):
                workcenter = self.env['mrp.workcenter'].browse(vals['workcenter_id'])
                if workcenter.type == 'outwork' and workcenter.partner and workcenter.product:
                    existing_po = False
                    if self.env.company.aggregate_po:
                        existing_po = self.env['purchase.order'].search([('partner_id', '=', workcenter.partner.id),
                                                                         ('state', '=', 'draft')])
                    purchase_order = False
                    if not self.env.company.aggregate_po or not existing_po:
                        purchase_order = self.env['purchase.order'].create({
                            'partner_id': workcenter.partner.id,
                            'state': 'draft'})

                    production = vals.get('production_id', None)
                    if production:
                        product_qty = self.env['mrp.production'].browse(production).product_qty
                    else:
                        product_qty= 1
                    production = self.env['mrp.production'].browse(vals.get('production_id'))
                    group = production.procurement_group_id if production else False
                    if existing_po:
                        order_id = existing_po[0].id
                    elif purchase_order:
                        order_id = purchase_order.id
                    else:
                        order_id = False
                    line = self.env['purchase.order.line'].create({
                        'order_id': order_id,
                        'product_id': workcenter.product.id,
                        'product_qty': product_qty,
                        'group_id': group.id if group else False,
                        'name': production.product_id.display_name if production else ""
                    })
                    if line.order_id and production:
                        line.order_id.origin = production.display_name
                    vals['purchase_order'] = existing_po[0].id if existing_po else purchase_order.id
                    vals['type'] = workcenter.type
                    vals['partner'] = workcenter.partner.id or False
                    vals['product'] = workcenter.product.id or False
        return super(MRPWorkorder, self).create(vals_list)
