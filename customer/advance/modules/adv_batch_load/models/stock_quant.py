from odoo import api, models

class StockInventory(models.Model):
    _inherit = 'stock.quant'

    def action_import_batch_excel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import Batch Excel',
            'res_model': 'adv.batch.load.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }
