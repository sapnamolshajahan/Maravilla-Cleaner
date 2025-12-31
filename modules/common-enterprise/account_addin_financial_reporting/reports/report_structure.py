# -*- coding: utf-8 -*-

import base64
from collections import defaultdict
from datetime import datetime
from io import BytesIO as StringIO
from operator import attrgetter

import xlsxwriter

from odoo import fields, models


class AddinReportStructure(models.TransientModel):
    _name = "addin.report.structure"

    account_group_id = fields.Many2one(
        comodel_name='addin.report.account.group',
        string='Account Structure',
        domain="[('parent_id','=', False)]"
    )
    report_name = fields.Char(size=64, string='Report Name', readonly=True, default='Financial Report Account Structure')
    data = fields.Binary(string='Download File', readonly=True)

    def set_defaults(self, workbook):
        cell_left = workbook.add_format({'align': 'left', 'text_wrap': True})
        cell_right_numeric = workbook.add_format({'align': 'right', 'num_format': '0.00', })
        cell_right = workbook.add_format({'align': 'right', 'num_format': '#,##0', 'text_wrap': True})
        cell_bold = workbook.add_format({'bold': True})
        return cell_left, cell_right_numeric, cell_bold, cell_right

    def build_group_structure(self, group):

        list_of_groups = []
        list_of_groups.append(group)
        for i in range(1, 10):
            groups = self.env['addin.report.account.group'].search([('parent_id', 'in', [x.id for x in list_of_groups])])
            list_of_groups.extend(groups)

        list_set = set(list_of_groups)

        group_dict = defaultdict(list)
        for i in list_set:
            if i == group:
                continue
            group_id = i
            parent_id = i.parent_id if i.parent_id else group
            group_dict[parent_id].append(group_id)

        return group_dict

    def print_line(self, k, all_accounts_for_report, row, worksheet, colnum, cell_left, depth):

        accounts = self.get_accounts(k)
        if accounts:
            all_accounts_for_report.extend(accounts)

        worksheet.write(row, 0, k.report_name.name, cell_left)
        worksheet.write(row, 1, k.footer_name, cell_left)
        worksheet.write(row, 2, k.heading, cell_left)
        worksheet.write(row, 3, k.print_accounts, cell_left)
        worksheet.write(row, 4, k.lines_before, cell_left)
        worksheet.write(row, 5, k.subtotal, cell_left)
        worksheet.write(row, 6, k.lines_after, cell_left)
        worksheet.write(row, 7, k.sequence, cell_left)
        worksheet.write(row, 8, '; '.join([x.name for x in accounts[0]]) if accounts else ' ')
        worksheet.write(row, colnum + depth, k.name)
        return all_accounts_for_report

    def printitem(self, group_id, structure, worksheet, all_accounts_for_report, row, colnum, cell_left, depth=0):

        all_accounts_for_report = self.print_line(group_id, all_accounts_for_report, row[0], worksheet, colnum, cell_left, depth)
        row[0] = row[0] + 1

        for k in sorted(structure[group_id], key=attrgetter('sequence')):
            self.printitem(k, structure, worksheet, all_accounts_for_report, row, colnum, cell_left, depth + 1)

        return all_accounts_for_report

    def get_accounts(self, group):
        list_accounts = []
        if group.account_tag_ids:
            accounts = self.env['account.account'].search([('tag_ids', 'in', [x.id for x in group.account_tag_ids])])
            list_accounts.extend(accounts)
        if group.account_ids:
            list_accounts.extend([x for x in group.account_ids])
        return list_accounts

    def generate_report(self, workbook):
        worksheet = workbook.add_worksheet('Report')
        cell_left, cell_right_numeric, cell_bold, cell_right = self.set_defaults(workbook)
        worksheet.set_column('A:C', 20)
        worksheet.set_column('D:H', 10)
        worksheet.set_column('I:I', 50)
        worksheet.set_column('J:Z', 3)

        row = 1
        worksheet.write(row, 0, 'Report Name', cell_left)
        worksheet.write(row, 1, 'Footer Name', cell_left)
        worksheet.write(row, 2, 'Heading Name', cell_right)
        worksheet.write(row, 3, 'Pint Accounts', cell_left)
        worksheet.write(row, 4, 'Lines Before', cell_right)
        worksheet.write(row, 5, 'Print Subtotal', cell_left)
        worksheet.write(row, 6, 'Lines After', cell_right)
        worksheet.write(row, 7, 'Sequence', cell_right)
        worksheet.write(row, 8, 'Account Codes', cell_left)
        worksheet.write(row, 9, 'Group Name', cell_left)

        """
        put the data that prints for each line at the start and can then indent the columns for the structure
        print the headings once we know what to print
        """

        structure = self.build_group_structure(self.account_group_id)
        all_accounts_for_report = self.printitem(self.account_group_id, structure, worksheet, [], [3], 9, cell_left, 0)
        if all_accounts_for_report:
            worksheet = workbook.add_worksheet('Accounts')
            row = 1
            worksheet.write(row, 0, 'Account ID', cell_left)
            worksheet.write(row, 1, 'Account Code', cell_left)
            worksheet.write(row, 2, 'Account Name', cell_right)
            worksheet.write(row, 3, 'Account Tags', cell_left)
            worksheet.write(row, 4, 'Account Category', cell_left)
            row = 3

            for i in range(0, len(all_accounts_for_report)):
                account = all_accounts_for_report[i]
                worksheet.write(row, 0, account.id, cell_left)
                worksheet.write(row, 1, account.code, cell_left)
                worksheet.write(row, 2, account.name, cell_left)
                # worksheet.write(row, 3, '; '.join([x.name for x in account.tags]))
                worksheet.write(row, 4, account.user_type_id.name)
                row += 1

        return

    def button_process(self):
        current_date = datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), '%Y-%m-%d %H:%M:%S')
        report_name = 'Financial Report Account Structure as at : ' + current_date + 'for Account Structure: ' + self.account_group_id.name
        self.write({'report_name': report_name + '.xlsx'})
        data = StringIO()
        workbook = xlsxwriter.Workbook(data, {'in_memory': True})

        self.generate_report(workbook)

        workbook.close()
        data.seek(0)
        output = base64.encodebytes(data.read())
        self.write({'data': output})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'addin.report.structure',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new', }
