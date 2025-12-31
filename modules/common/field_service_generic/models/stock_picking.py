from odoo import models
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    _logger.info("✅ Custom StockPicking override loaded")

    def button_validate(self):
        if not self:
            _logger.warning("⚠️ button_validate called with EMPTY recordset (ignored)")
            return True
        return super().button_validate()

