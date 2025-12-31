import datetime

from odoo import fields, models
import math


class ProductCyclicCount(models.Model):
    _name = 'product.cyclic.count'

    name = fields.Char(string='Name', default='/')
    frequency = fields.Integer(string='Frequency', default=1)
    time_measure = fields.Selection([('7', 'Weekly'), ('30', 'Monthly')], string='Time Measure',
                                    default='7')
    last_count_date = fields.Date()
    next_count_date = fields.Date()
    cycle_end_date = fields.Date()
    product_ids = fields.One2many('product.template', 'cyclic_count_frequency', string='Products')

    def _cron_product_cyclic_count(self):
        pccs = self.search([]).filtered(
            lambda c: c.next_count_date == datetime.datetime.today() or not c.next_count_date)
        products = self.env['product.product']
        quants = self.env['stock.quant']
        for pcc in pccs:
            pcc.last_count_date = datetime.date.today()
            nod = int(pcc.time_measure) * pcc.frequency
            per_cycle = math.ceil(len(pcc.product_ids) / nod)
            pcc.next_count_date = datetime.date.today() + datetime.timedelta(days=int(nod))
            if not pcc.cycle_end_date:
                pcc.cycle_end_date = fields.Date.context_today(self)
            if pcc.next_count_date == pcc.cycle_end_date:
                pcc.cycle_end_date = datetime.date.today() + datetime.timedelta(days=int(nod) * int(nod) * per_cycle)
            pcc_prods = pcc.product_ids.filtered(lambda p: (p.last_count_date and p.last_count_date >=
                                                            pcc.cycle_end_date)
                                                           or not p.last_count_date)[:int(per_cycle)]
            for pcc_prod in pcc_prods:
                pcc_prod.last_count_date = datetime.date.today()
                products += pcc_prod.product_variant_ids
        warehouses = self.env['stock.warehouse'].search([('incl_cyclic', '=', True)])
        internal_locations = [x.lot_stock_id for x in warehouses]
        for loc in internal_locations:

            for product in products:
                current_quants = quants.search([('location_id', '=', loc.id), ('product_id', '=', product.id)])
                for quant in current_quants:
                    quant.write({'inventory_date': product.product_tmpl_id.cyclic_count_frequency.cycle_end_date,
                                 'cyclic': True})
                if not current_quants:
                    quants.create({
                        'product_id': product.id,
                        'location_id': loc.id,
                        'quantity': 0.0,
                        'cyclic': True,
                        'inventory_date': product.product_tmpl_id.cyclic_count_frequency.cycle_end_date
                    })

