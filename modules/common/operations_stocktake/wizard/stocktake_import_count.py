# -*- coding: utf-8 -*-
import binascii
import logging
import tempfile
import xlrd

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StocktakeImportCount(models.TransientModel):
    """Import count on stocktake to count sheet"""
    _name = "stocktake.import.count"
    _description = 'Stocktake Import Count'

    stocktake = fields.Many2one("stock.inventory", string="Stocktake", required=True)
    count_sheet = fields.Many2one('stocktake.data.entry', string='Count Sheet',
                                  domain="[('inventory', '=', stocktake)]", required=True)
    import_file = fields.Binary("Import File", required=True)

    ###################################################################################
    # Functions
    ###################################################################################

    def button_import_file(self):
        try:
            import_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            import_file.write(binascii.a2b_base64(self.import_file))
            import_file.seek(0)
            wb = xlrd.open_workbook(import_file.name)
            sheet = wb.sheet_by_index(0)

        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Please check the file is correct, it cannot be processed!"))

        for row_no, row in enumerate(sheet.get_rows()):
            if row_no <= 0:
                continue
            else:
                line = tuple(map(lambda r: isinstance(r.value, bytes) and r.value.encode('utf-8') or str(r.value), row))
                default_code, actual_qty = line[0].strip(), float(line[1].strip())
                _logger.info((default_code, actual_qty))

                if len(line) < 2:
                    raise ValidationError(_('Wrong length of the line: {}'.format(str(line))))

                if default_code:
                    try:
                        default_code = float(default_code)
                        default_code = str(int(default_code))
                    except:
                        default_code = default_code

                    product = self.env['product.product'].with_context(exact_match=True).search([
                        ('default_code', '=', default_code),
                    ], limit=1)

                    # Confirm the product exists
                    if not product:
                        raise ValidationError('Product {} not found'.format(default_code))

                    self.env['stocktake.data.entry.line'].create({
                        'stocktake_id': self.count_sheet.id,
                        'product_id': product.id,
                        'quantity': actual_qty
                    })

        return {'type': 'ir.actions.act_window_close'}