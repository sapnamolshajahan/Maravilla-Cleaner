# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CarrierShipmentCustomBox(models.TransientModel):
    _name = "carrier.shipment.custom.box"
    _description = "Carrier Shipment Custom Box"

    ########################################################################################
    # Default and compute methods
    ########################################################################################

    ########################################################################################
    # Fields
    ########################################################################################
    wizard_id = fields.Many2one(string='Wizard', comodel_name='carrier.shipment.wizard', ondelete='cascade')
    package_name = fields.Char('Package Name')
    weight = fields.Float('Weight(kg)', digits=(3, 2))
    width = fields.Float('Width(cm)', digits=(3, 2))
    height = fields.Float('Height(cm)', digits=(3, 2))
    length = fields.Float('Length(cm)', digits=(3, 2))


class DangerousGoods(models.TransientModel):
    _name = "carrier.shipment.dangerous.goods"
    _description = "Carrier Shipment Dangerous Goods Items"

    ########################################################################################
    # Default and compute methods
    ########################################################################################
    @api.onchange('dangerous_goods_preset_item')
    def onchange_dangerous_goods_preset_item(self):
        for item in self:
            if item.dangerous_goods_preset_item:
                item.un_or_id = item.dangerous_goods_preset_item.un_or_id
                item.shipping_name = item.dangerous_goods_preset_item.shipping_name
                item.shipping_class = item.dangerous_goods_preset_item.shipping_class
                item.packing_group = item.dangerous_goods_preset_item.packing_group
                item.subsidiary_risk = item.dangerous_goods_preset_item.subsidiary_risk
                item.packing_qty_type = item.dangerous_goods_preset_item.packing_qty_type
                item.packing_instructions = item.dangerous_goods_preset_item.packing_instructions
                item.authorization = item.dangerous_goods_preset_item.authorization
            else:
                item.un_or_id = ''
                item.shipping_name = ''
                item.shipping_class = ''
                item.packing_group = ''
                item.subsidiary_risk = ''
                item.packing_qty_type = ''
                item.packing_instructions = ''
                item.authorization = ''

    ########################################################################################
    # Fields
    ########################################################################################
    dangerous_goods_preset_item = fields.Many2one(
        string='DG Preset', comodel_name='gss.dangerous.goods.preset')

    wizard_id = fields.Many2one(string='Wizard', comodel_name='carrier.shipment.wizard', ondelete='cascade')
    un_or_id = fields.Char(string='UN or ID No')
    shipping_name = fields.Char(string='Proper Shipping Name')
    shipping_class = fields.Char(string='Class')
    packing_group = fields.Char(string='Packing Group')
    subsidiary_risk = fields.Char(string='Subsidiary Risk')
    packing_qty_type = fields.Char(string='Qty and Type of Packing')
    packing_instructions = fields.Char(string='Packing Inst')
    authorization = fields.Char(string='Authorization', default='Storeperson')


class CarrierShipmentWizard(models.TransientModel):
    _inherit = "carrier.shipment.wizard"
    _description = "Carrier Shipment Select Wizard"

    ########################################################################################
    # Default and compute methods
    ########################################################################################
    @api.onchange('custom_boxes', 'custom_box_ids', 'detail_ids')
    def onchange_custom_boxes(self):
        for obj in self:
            if obj.custom_box_ids:
                obj.show_services_button = True

            elif obj.detail_ids:
                obj.show_services_button = True

            else:
                obj.show_services_button = False

    @api.model
    def get_gss_delivery_carrier(self):
        return self.env['delivery.carrier'].search([('delivery_type', '=', 'gss')], limit=1)

    @api.model
    def _get_dg_gss_handling_info_default(self):
        gss_type = self.get_gss_delivery_carrier()

        if gss_type:
            return gss_type.gss_dg_additional_handling_info_preset or ''

    @api.model
    def _get_dg_gss_hazchem_default(self):
        gss_type = self.get_gss_delivery_carrier()

        if gss_type:
            return gss_type.gss_dg_hazchem_code_preset or ''

    ########################################################################################
    # Fields
    ########################################################################################
    custom_boxes = fields.Boolean(string='Include Custom Boxes')

    custom_box_ids = fields.One2many(
        string='Custom boxes', comodel_name='carrier.shipment.custom.box', inverse_name='wizard_id')

    dangerous_goods_ids = fields.One2many(
        string='Dangerous Goods Items', comodel_name='carrier.shipment.dangerous.goods', inverse_name='wizard_id')

    hazchem_code = fields.Char(string='Hazchem Code', default=_get_dg_gss_hazchem_default)
    total_qty = fields.Float(string='Total Qty')
    total_kg = fields.Float(string='Total Kg')
    box_size = fields.Char(string='Box Size')
    handling_info = fields.Text(string='Additional Handling Info', default=_get_dg_gss_handling_info_default)

    ########################################################################################
    # Methods
    ########################################################################################
    @api.model
    def build(self, picking, is_ship_only=False):
        wizard = super(CarrierShipmentWizard, self).build(picking, is_ship_only)
        shipment_model = self.env['delivery.carrier'].get_carrier_shipment_model(picking.carrier_id)
        wizard.shipment_model = shipment_model and shipment_model._name
        return wizard

    def package_details_supplied(self):
        return bool(self.detail_ids) or self.custom_boxes

    def validate_before_getting_services(self):
        if not self.detail_ids and not self.custom_boxes:
            raise UserError("Package details are required.")

    def button_send_shipment(self):
        res = super(CarrierShipmentWizard, self).button_send_shipment()

        for shipment in self:
            if shipment.is_dangerous_goods:
                shipment.picking_id.write({
                    "hazchem_code": shipment.hazchem_code,
                    "handling_info": shipment.handling_info,
                    "total_qty": shipment.total_qty,
                    "total_kg": shipment.total_kg,
                    "box_size": shipment.box_size,
                })

                for line in shipment.dangerous_goods_ids:
                    self.env["picking.dangerous.goods"].create({
                        "picking_id": shipment.picking_id.id,
                        "un_or_id": line.un_or_id,
                        "shipping_name": line.shipping_name,
                        "shipping_class": line.shipping_class,
                        "packing_group": line.packing_group,
                        "subsidiary_risk": line.subsidiary_risk,
                        "packing_qty_type": line.packing_qty_type,
                        "packing_instructions": line.packing_instructions,
                        "authorization": line.authorization,
                    })

        return res
