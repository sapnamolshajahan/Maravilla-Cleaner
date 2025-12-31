import logging
from dateutil.relativedelta import relativedelta

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _cron_product_bom_price(self):
        two_days_ago = fields.Date.context_today(self) - relativedelta(days=2)
        products = self.search([]).filtered(lambda p: p.bom_ids)

        for product in products:
            for bom in product.bom_ids:
                bom_recently_updated = bom.write_date.date() > two_days_ago

                recent_manuf_orders = self.env["mrp.production"].search([
                    ("bom_id", "=", bom.id),
                    ("create_date", ">", two_days_ago),
                    ("state", "=", "done")
                ])
                if bom_recently_updated or recent_manuf_orders:
                    product.update_product_cost(bom=bom)
                    _logger.info(f"Updating cost price for {product.default_code} because of changes in BOM")

    def update_product_cost(self, bom):
        component_price_sum = 0
        company = bom.company_id or self.env.company

        for line in bom.bom_line_ids:
            component_price_sum += line.product_id.uom_id._compute_price(
                line.product_id.with_company(company).standard_price, line.product_uom_id) * line.product_qty

        price_per_product = component_price_sum / (bom.product_qty or 1)
        self.standard_price = self.uom_id._compute_price(price_per_product, bom.product_uom_id)
