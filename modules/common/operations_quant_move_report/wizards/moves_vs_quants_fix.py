# -*- coding: utf-8 -*-

from odoo import models, api, fields
import logging
from odoo.tools.float_utils import float_round
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class OperationsMovesQuantsFix(models.TransientModel):
    _name = "operations.moves.quants.fix"
    _description = 'Move Quants Fix'

    #   TODO Implication around stock lots - these are being ignored
    #   TODO - handle stock by bin location

    def get_stock_moves_soh(self, product, location, lot, package):
        stock_moves = self.env['stock.move.line'].search([
            '|', ('location_id', '=', location.id),
            ('location_dest_id', '=', location.id),
            ('product_id', '=', product),
            ('lot_id', '=', lot),
            ('package_id', '=', package),
            ('state', '=', 'done')])

        soh = 0.0
        for stock_move in stock_moves:
            if stock_move.location_id.id == location.id and \
                    stock_move.location_dest_id.id == location.id:
                continue
            elif stock_move.location_id.id == location.id:
                if stock_move.product_uom_id.id == stock_move.product_id.uom_id.id:
                    soh -= stock_move.product_uom_id._compute_quantity(stock_move.quantity,
                                                                       stock_move.product_id.uom_id)
                else:
                    soh -= stock_move.quantity
            else:
                if stock_move.product_uom_id.id == stock_move.product_id.uom_id.id:
                    soh += stock_move.product_uom_id._compute_quantity(stock_move.quantity,
                                                                       stock_move.product_id.uom_id)
                else:
                    soh += stock_move.quantity

        return soh

    def get_stock_moves_reserved(self, product, location, lot, package):
        stock_moves = self.env['stock.move.line'].search([
            '|', ('location_id', '=', location.id),
            ('location_dest_id', '=', location.id),
            ('product_id', '=', product),
            ('lot_id', '=', lot),
            ('package_id', '=', package),
            ('state', 'not in', ('done', 'cancel'))])

        soh = 0.0
        for stock_move in stock_moves:
            if stock_move.location_id.id == location.id and \
                    stock_move.location_dest_id.id == location.id:
                continue
            elif stock_move.location_id.id == location.id:
                if stock_move.product_uom_id.id == stock_move.product_id.uom_id.id:
                    soh -= stock_move.product_uom_id._compute_quantity(stock_move.quantity,
                                                                       stock_move.product_id.uom_id)
                else:
                    soh -= stock_move.quantity
            else:
                if stock_move.product_uom_id.id == stock_move.product_id.uom_id.id:
                    soh += stock_move.product_uom_id._compute_quantity(stock_move.quantity,
                                                                       stock_move.product_id.uom_id)
                else:
                    soh += stock_move.quantity

        return 0 - soh

    def process_difference(self, quant_qty, sm_soh, quants, product, location):
        if not quants:
            self.env['stock.quant'].create({
                'product_id': product,
                'location_id': location.id,
                'quantity': sm_soh - quant_qty,
                'in_date': fields.Datetime.now()
            })
        elif float_round(quant_qty, 3) < float_round(sm_soh, 3):
            if quants:
                quants[0].write({'quantity': quants[0].quantity + sm_soh - quant_qty})
            else:
                self.env['stock.quant'].create({
                    'product_id': product,
                    'location_id': location.id,
                    'quantity': sm_soh - quant_qty,
                    'in_date': fields.Datetime.now()
                })
        elif float_round(quant_qty, 3) > float_round(sm_soh, 3):
            difference = quant_qty - sm_soh
            for quant in quants:
                if not difference:
                    break
                if quant.quantity > difference:
                    quant.write({'quantity': quant.quantity - difference})
                    break
                else:
                    difference = difference - quant.quantity
                    quant.write({'quantity': 0})

        self.env.cr.commit()

    def process_reserved_difference(self, quant_qty, sm_soh, quants, product, location):
        if float_round(quant_qty, 3) < float_round(sm_soh, 3):
            if quants:
                quants[0].write({'reserved_quantity': quants[0].reserved_quantity + sm_soh - quant_qty})
            else:
                self.env['stock.quant'].create({
                    'product_id': product,
                    'location_id': location.id,
                    'quantity': 0.0,
                    'reserved_quantity': sm_soh - quant_qty,
                    'in_date': fields.Datetime.now()
                })
        elif float_round(quant_qty, 3) > float_round(sm_soh, 3):
            difference = quant_qty - sm_soh
            for quant in quants:
                if not difference:
                    break
                if quant.reserved_quantity > difference:
                    quant.write({'reserved_quantity': quant.reserved_quantity - difference})
                    break
                else:
                    difference = difference - quant.quantity
                    quant.write({'reserved_quantity': 0})

        self.env.cr.commit()

    def query_quants(self, product, location, lot, package):
        quants = self.env['stock.quant'].search([('product_id', '=', product),
                                                 ('location_id', '=', location.id),
                                                 ('lot_id', '=', lot),
                                                 ('package_id', '=', package)])
        return quants

    def check_product_only(self, location, product):
        quants = self.query_quants(product, location, False, False)
        move_soh = self.get_stock_moves_soh(product, location, False, False)
        quant_soh = sum([x.quantity for x in quants])
        if float_round(move_soh, 3) != float_round(quant_soh, 3):
            self.process_difference(quant_soh, move_soh, quants, product, location)

        reserved_sm = self.get_stock_moves_reserved(product, location, False, False)
        quants_reserved = sum([x.reserved_quantity for x in quants])
        if float_round(reserved_sm, 3) != float_round(quants_reserved, 3):
            self.process_reserved_difference(quants_reserved, reserved_sm, quants, product, location)

    def check_product_lot(self, location, product, lot):
        quants = self.query_quants(product, location, lot, False)
        move_soh = self.get_stock_moves_soh(product, location, lot, False)
        quant_soh = sum([x.quantity for x in quants])
        if float_round(move_soh, 3) != float_round(quant_soh, 3):
            self.process_difference(quant_soh, move_soh, quants, product, location)

        reserved_sm = self.get_stock_moves_reserved(product, location, lot, False)
        quants_reserved = sum([x.reserved_quantity for x in quants])
        if float_round(reserved_sm, 3) != float_round(quants_reserved, 3):
            self.process_reserved_difference(quants_reserved, reserved_sm, quants, product, location)

    def check_product_package(self, location, product, package):
        quants = self.query_quants(product, location, False, package)
        move_soh = self.get_stock_moves_soh(product, location, False, package)
        quant_soh = sum([x.quantity for x in quants])
        if float_round(move_soh, 3) != float_round(quant_soh, 3):
            self.process_difference(quant_soh, move_soh, quants, product, location)

        reserved_sm = self.get_stock_moves_reserved(product, location, False, package)
        quants_reserved = sum([x.reserved_quantity for x in quants])
        if float_round(reserved_sm, 3) != float_round(quants_reserved, 3):
            self.process_reserved_difference(quants_reserved, reserved_sm, quants, product, location)

    def check_product_lot_package(self, location, product, lot, package):
        quants = self.query_quants(product, location, lot, package)
        move_soh = self.get_stock_moves_soh(product, location, lot, package)
        quant_soh = sum([x.quantity for x in quants])
        if float_round(move_soh, 3) != float_round(quant_soh, 3):
            self.process_difference(quant_soh, move_soh, quants, product, location)

        reserved_sm = self.get_stock_moves_reserved(product, location, lot, package)
        quants_reserved = sum([x.reserved_quantity for x in quants])
        if float_round(reserved_sm, 3) != float_round(quants_reserved, 3):
            self.process_reserved_difference(quants_reserved, reserved_sm, quants, product, location)

    def run_process(self):
        locations = self.env['stock.location'].search([('usage', '=', 'internal'),
                                                       ('company_id', '=', self.env.company.id)])

        for location in locations:
            sm_products_sql = """
                                select sml.product_id, sml.lot_id, sml.package_id from stock_move_line sml
                                join product_product pp on sml.product_id = pp.id 
                                join product_template pt on pp.product_tmpl_id = pt.id  
                                where (sml.location_id = {location} or 
                                sml.location_dest_id = {location}) and sml.state = 'done' 
                                and pt.type = 'consu' 
                                group by product_id, lot_id, package_id
                                """.format(location=location.id)
            self.env.cr.execute(sm_products_sql)
            recs = self.env.cr.fetchall()
            for rec in recs:
                product = rec[0]
                lot = rec[1]
                package = rec[2]

                if not lot and not package:
                    self.check_product_only(location, product)
                elif lot and not package:
                    self.check_product_lot(location, product, lot)
                elif package and not lot:
                    self.check_product_package(location, product, package)
                else:
                    self.check_product_lot_package(location, product, lot, package)

        return {"type": "ir.actions.act_window_close"}
