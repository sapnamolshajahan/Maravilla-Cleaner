# -*- coding: utf-8 -*-
from io import BytesIO as StringIO
import base64
import xlsxwriter
from decimal import Decimal

from odoo import models, fields, api


class RebateReport(models.TransientModel):
    _name = 'rebate.report'
    _description = 'Rebate Report'

    ###########################################################################
    # Fields
    ###########################################################################

    export_xls = fields.Binary(string="Export file", readonly=True)
    report_name = fields.Char(string="Export file name", readonly=True, default="rebate_report.xls")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', required=True)
    date_from = fields.Date(string='Date From', default=fields.Date.today)
    date_to = fields.Date(string='Date To', default=fields.Date.today)

    def _get_company_id(self):
        company = self.uid.company_id
        return company

    def check_report(self):
        report_datas = self._generate_report_datas()
        output = self.__encode_report_data(report_datas)
        export_id = self.env['rebate.report.xls_export_options'].create({'export_xls': output})
        return {
            "name": "Rebate Report",
            "res_model": "rebate.report.xls_export_options",
            "res_id": export_id.id,
            "view_mode": "form",
            "view_id": False,
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "new",
            "domain": "[]",
        }

    def __encode_report_data(self, report_datas):
        fieldnames = [
            'parent_reference',
            'parent_name',
            'branch_reference',
            'branch_name',
            'product_category',
            'product_code',
            'product_description',
            'quantity',
            'list_price',
            'discount',
            'net_price',
            'extended_net_price',
            'period',
            'invoice_number',
            'rebate_flag',
            'client_order_ref'

        ]
        data = StringIO()

        report_name = "Rebate-Report-{}".format(self.date_from)
        file_name = "{0}.xlsx".format(report_name)

        self.report_name = file_name

        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('RebateReport')

        columns_map = {
            0: "Parent Reference",
            1: "Parent Name",
            2: "Branch Reference",
            3: "Branch Name",
            4: "Category",
            5: "Code",
            6: "Description",
            7: "Quantity",
            8: "List Price",
            9: "Disc %",
            10: "Net Price",
            11: "Line Total",
            12: "Period",
            13: "Invoice Number",
            14: "Rebate Flag",
            15: "Client Order Ref"
        }
        # formatting
        worksheet.set_column('A:C', 15)
        worksheet.set_column('C:F', 20)
        format_header = workbook.add_format({'text_wrap': True, 'bold': True, "bg_color": "#7BBDC4", "border": 1})

        # Write report header
        row = 1
        for key, value in columns_map.items():
            worksheet.write(row, key, value, format_header)
        row += 1

        # Write report body
        for report_data_line in report_datas:
            for index, field_name in enumerate(fieldnames):
                worksheet.write(row, index, report_data_line[field_name])
            row += 1
        workbook.close()
        data.seek(0)
        output = base64.b64encode(data.read()).decode()
        return output

    def _generate_report_datas(self):
        datas = {}
        partner_id =self.partner_id.id
        branch_partner_ids = self.__get_all_partners(partner_id)

        parent_invoice_lines = self.__get_invoice_lines([partner_id])
        datas[partner_id] = [x[1] for x in parent_invoice_lines]

        if len(branch_partner_ids) > 0:
            for branch_partner_id in branch_partner_ids:
                branch_invoice_lines = self.__get_invoice_lines([branch_partner_id])
                if branch_invoice_lines:
                    datas[branch_partner_id] = [x[1] for x in branch_invoice_lines]

        report_lines = self.__generate_report_lines(datas, partner_id)

        return report_lines

    def __generate_report_lines(self, datas, parent_partner_id):
        report_lines = []
        partner_pool = self.env['res.partner']
        invoice_line_pool = self.env['account.move.line']
        sale_order_line_pool = self.env['sale.order.line']
        for data_key in datas.keys():
            partner_id = data_key
            parent_partner = partner_pool.browse(parent_partner_id)
            partner = partner_pool.browse(partner_id)
            invoice_lines = invoice_line_pool.browse(datas[data_key])
            quantize_decimal = Decimal("1.00")
            for invoice_line in invoice_lines:
                report_line = {}
                report_line['parent_reference'] = parent_partner.ref
                report_line['parent_name'] = parent_partner.name
                journal_type = invoice_line.move_id.journal_id.type
                if partner_id != parent_partner_id:
                    report_line['branch_reference'] = partner.ref
                    report_line['branch_name'] = partner.name
                else:
                    report_line['branch_name'] = None
                    report_line['branch_reference'] = None
                # ignore text lines in invoices - identified by no product code
                if invoice_line.product_id:
                    report_line['product_category'] = invoice_line.product_id.product_tmpl_id.categ_id.name
                    report_line['product_code'] = invoice_line.product_id.code
                    if invoice_line.product_id.product_tmpl_id.name:
                        report_line['product_description'] = invoice_line.product_id.product_tmpl_id.name
                    else:
                        report_line['product_description'] = ""

                    if invoice_line.move_id.move_type in ('out_invoice', 'in_invoice', 'in_refund'):
                        report_line['quantity'] = invoice_line.quantity
                    else:
                        report_line['quantity'] = 0 - invoice_line.quantity

                    report_line['list_price'] = invoice_line.price_unit
                    report_line['discount'] = invoice_line.discount
                    report_line['net_price'] = Decimal(str(invoice_line.price_unit - (invoice_line.price_unit * invoice_line.discount / 100))).quantize(quantize_decimal)

                    report_line['extended_net_price'] = (
                        (invoice_line.price_unit -
                         (invoice_line.price_unit * invoice_line.discount / 100))
                        * report_line['quantity']
                    )

                    report_line['period'] = invoice_line.move_id.invoice_date.strftime("%b-%y")
                    report_line['period_start'] = invoice_line.move_id.invoice_date
                    report_line['invoice_number'] = invoice_line.move_id.name
                    sale_order_line_invoice_rel_sql = "select order_line_id from sale_order_line_invoice_rel where invoice_line_id = %s"
                    sql = sale_order_line_invoice_rel_sql % (invoice_line.id)
                    self.env.cr.execute(sql)
                    fetch_data = self.env.cr.fetchall()

                    if len(fetch_data) > 0:
                        sale_order_line_id = fetch_data[0][0]
                        sale_order_line = sale_order_line_pool.browse(sale_order_line_id)
                        sale_order_sql = "select order_id from sale_order_line where id = %s"
                        sql = sale_order_sql % (sale_order_line_id)
                        self.env.cr.execute(sql)
                        self.env.cr.fetchall()
                        report_line['rebate_flag'] = sale_order_line.order_id.has_rebate

                        if sale_order_line.order_id.client_order_ref:
                            report_line['client_order_ref'] = sale_order_line.order_id.client_order_ref
                        else:
                            report_line['client_order_ref'] = None
                    else:
                        report_line['invoice_number'] = None
                        report_line['rebate_flag'] = None
                        report_line['client_order_ref'] = None
                    report_lines.append(report_line)

        report_lines.sort(key=lambda x: x['period_start'])
        for report_line in report_lines:
            if 'period_start' in report_line:
                del report_line['period_start']
        return report_lines

    def __get_invoice_lines(self, partner_ids):
        invoice_line_sql = ("select partner_id, id from account_move_line where display_type = 'product' and move_id in "
                            "(select id from account_move where partner_id in %s "
                            "and state not in ('draft', 'cancel') and invoice_date BETWEEN '%s' and '%s')")
        partner_ids_str = self.__get_non_trailing_comma_tuple(partner_ids)
        sql = invoice_line_sql % (partner_ids_str, self.date_from, self.date_to)
        self.env.cr.execute(sql)
        invoice_line_ids = [(x[0], x[1]) for x in self.env.cr.fetchall()]
        return invoice_line_ids

    def __get_all_partners(self, partner_id):
        ids = []
        find_all_partners_sql = "select * from res_partner where parent_id = %s"
        sql = find_all_partners_sql % (partner_id)
        self.env.cr.execute(sql)
        ids.extend([x[0] for x in self.env.cr.fetchall()])
        return ids

    def __get_non_trailing_comma_tuple(self, args):
        tArray = "("
        iteration = 1
        for arg in args:
            if iteration != len(args):
                tArray += str(arg) + ", "
                iteration += 1
            else:
                tArray += str(arg)
                iteration += 1
        tArray += ")"
        return tArray


class XlsExportFile(models.TransientModel):
    _name = "rebate.report.xls_export_options"

    export_xls = fields.Binary(string="Export filename", readonly=True, default='Rebate Report.csv')
    report_name = fields.Char(string="Export file name", readonly=True, default="rebate_report.xls")
