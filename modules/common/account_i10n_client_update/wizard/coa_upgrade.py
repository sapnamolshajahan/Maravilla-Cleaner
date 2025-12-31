from pandas.core.dtypes.inference import is_float

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import tempfile
import binascii
import xlrd
import logging


_logger = logging.getLogger(__name__)



class COAUpgrade(models.TransientModel):
    _name = 'coa.upgrade'
    _description = 'COA Upgrade'

    file = fields.Binary(string='File to Import')
    filename = fields.Char(string='File Name')


    def import_file(self):
        try:
            file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            file.write(binascii.a2b_base64(self.file))
            file.seek(0)
            wb = xlrd.open_workbook(file.name)
            sheet = wb.sheet_by_index(0)
        except Exception:
            raise ValidationError("Please Select Valid File Format !")

        account_type_field = self.env['ir.model.fields'].search([('name', '=', 'account_type'),
                                                                 ('model', '=', 'account.account')], limit=1)
        account_type_val_ids = self.env['ir.model.fields.selection'].search([('field_id', '=', account_type_field.id)])
        account_type_vals = [x.value for x in account_type_val_ids]

        # do some initial validation
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                continue
            line = list(
                map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                    sheet.row(row_no)))
            if not line[0] or not line[1] or not line[2]:
                raise UserError("Every row must have a code, name and type")

            account_type = line[2]
            if account_type not in account_type_vals:
                raise UserError('Account type {account_type} not found'.format(account_type=account_type))

        total_count = sheet.nrows
        data_dict = {}
        up_to = 1
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                pass
            else:
                _logger.debug(f"upto: {up_to} of {total_count}")
                up_to += 1
                line = list(
                    map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or row.value,
                        sheet.row(row_no)))
                account_type = line[2]
                if account_type in data_dict:
                    data_dict[account_type].append(line)
                else:
                    data_dict[account_type] = []
                    data_dict[account_type].append(line)
        for k in data_dict:
            counter = 0
            vals = data_dict[k]
            existing_account_records = self.env['account.account'].search([('account_type', '=', k)])
            for line in vals:
                if is_float(line[0]):
                    code = int(line[0])
                else:
                    code = line[0]
                try:
                    existing_account = existing_account_records[counter]
                    existing_account.write({
                        'code': code,
                        'name': line[1]})
                except:
                    self.env['account.account'].sudo().create({
                        'code': code,
                        'name': line[1],
                        'account_type': k
                            })
                counter += 1
            if len(existing_account_records) > len(vals):
                for i in range(len(existing_account_records), len(vals), -1):
                    existing_account_records[i-1].write({'active': False})



