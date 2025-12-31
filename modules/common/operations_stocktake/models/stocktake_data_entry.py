# -*- coding: utf-8 -*-
import logging

from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from ..utils.serial_numbers import numeric_decompose

_logger = logging.getLogger(__name__)


class StockTakeDataEntryControl(models.Model):
    _name = "stocktake.data.entry.control"
    _description = 'Stocktake Data Entry Control'
    _order = "id desc"

    name = fields.Many2one("stock.inventory", string="Inventory", required=True, domain="[('state', '=', 'confirm')]")
    lines = fields.One2many('stocktake.data.entry.line', 'stocktake_data_entry_control', string='Lines')


class StockTakeDataEntry(models.Model):
    _name = "stocktake.data.entry"
    _order = "id desc"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    def _inventory_locations(self):
        for r in self:
            if r.inventory.warehouse_id:
                r.inventory_locations = r.inventory.warehouse_id.lot_stock_id
            else:
                r.inventory_locations = False

    @api.onchange("inventory")
    def onchange_inventory(self):
        for record in self:
            if not record.inventory:
                continue
            record.name = record.inventory.name
            record._inventory_locations()

            for location in record.inventory.location_ids:
                record.location = location
                break

    def _get_display_name(self):
        loc_name = self.location.display_name
        for record in self:
            record.display_name = "{inventory}/{loc}/{counter}".format(
                inventory=record.inventory.name,
                loc=loc_name,
                counter=record.counter)

    ###########################################################################
    # Fields
    ###########################################################################
    display_name = fields.Char(compute="_get_display_name", string="Display_name")
    name = fields.Char(string="Name")
    inventory = fields.Many2one("stock.inventory", string="Inventory", required=True,
                                domain="[('state','in',['draft','confirm'])]")
    state = fields.Selection([("draft", "Draft"), ("done", "Done")], string="State", readonly=True, default="draft")
    location = fields.Many2one("stock.location", string="Location", required=True)
    inventory_locations = fields.Many2many("stock.location", compute="_inventory_locations", readonly=True)
    notes = fields.Text(string="Notes")
    counter = fields.Char(string="Counter")
    products = fields.One2many("stocktake.data.entry.line", "stocktake_id",
                               string="Products")
    company_id = fields.Many2one(related="inventory.company_id", readonly=True, string="Company")
    stocktake_data_entry_control_id = fields.Many2one('stocktake.data.entry.control', string='Control')

    ###########################################################################
    # Model methods
    ###########################################################################

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            inventory = self.env["stock.inventory"].browse(values["inventory"])
            if inventory.state not in ("draft", "confirm"):
                raise UserError("Inventory Adjustment {} must be in Draft or In Progress state".format(inventory.name))

            control = self.env['stocktake.data.entry.control'].search([('name', '=', inventory.id)])
            if not control:
                control = self.env['stocktake.data.entry.control'].create({'name': inventory.id})
            values['stocktake_data_entry_control_id'] = control.id

        res = super(StockTakeDataEntry, self).create(values)
        return res

    def action_reset(self):
        for record in self:
            record.write({'state': 'draft'})


    def unlink(self):
        for data_entry in self:
            if data_entry.state == "done":
                raise UserError("You cannot delete a stock take data entry which has been processed")
            control = self.env['stocktake.data.entry.control'].search([('name', '=', data_entry.inventory.id)])
            control.unlink()
        return super(StockTakeDataEntry, self).unlink()

    def copy(self, default=None):
        raise UserError("Sorry, but duplication is not allowed to be performed on stocktake data entry items")


