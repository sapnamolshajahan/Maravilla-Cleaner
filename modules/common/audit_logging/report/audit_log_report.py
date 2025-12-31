# -*- coding: utf-8 -*-

import xlsxwriter
from collections import defaultdict
from io import BytesIO as StringIO
from odoo import models, fields


class AuditLogReport(models.TransientModel):
    _name = 'audit.log.report'

    wizard_id = fields.Many2one(comodel_name='audit.log.print', string='Wizard')
    sort_name = fields.Char(string='Name')
    lines = fields.One2many('audit.log.report.line', 'audit_log_report_id', string='Lines')

    def run_report(self, wizard_id):
        wizard = self.env['audit.log.print'].browse(wizard_id)
        models = wizard.model_ids
        for model in models:
            group_by = self.env['audit.logging.group'].search([('model_id', '=', model.id)])
            if group_by:
                for field in model.field_id:
                    if field.id == group_by.field_id.id:
                        sort_by = group_by.field_id
                        break
            else:
                sort_by = False

            records_to_process = self.env['audit.logging'].search([
                ('create_date', '>=', wizard.start),
                ('create_date', '<=', wizard.finish),
                ('model', '=', model.model),
                ('field_id.ttype', '!=', 'binary'),
                '|', ('company_id', '=', False),
                ('company_id', '=', self.env.company.id)
            ])

            for record in records_to_process:
                sort_name = False
                if sort_by and sort_by.model == model.model and sort_by.name == 'id':
                    try:
                        existing_rec = self.env[record.model].browse(record.record_id)
                        if existing_rec:
                            sort_name = existing_rec.display_name
                    except:
                        sort_name = 'Deleted Record'
                elif sort_by and sort_by.relation:
                    existing_rec = self.env[record.model].browse(record.record_id)
                    try:
                        browse_field = existing_rec[sort_by.name]
                        if browse_field:
                            sort_name = browse_field.display_name
                    except:
                        sort_name = 'Deleted Relational Record'
                else:
                    sort_name = 'No sort'

                existing_rec = self.env['audit.log.report'].search([('sort_name', '=', sort_name),
                                                                    ('wizard_id', '=', wizard.id)])
                if not existing_rec:
                    existing_rec = self.env['audit.log.report'].create({'sort_name': sort_name,
                                                                        'wizard_id': wizard.id})

                self.env['audit.log.report.line'].create({
                    'audit_log_report_id': existing_rec.id,
                    'audit_log_id': record.id,
                    'timestamp': record.create_date,
                    'login': record.login,
                    'model_id': model.id,
                    'field_id': record.field_id.id,
                    'old_value': record.old_value,
                    'new_value': record.new_value,
                    'method': record.method})

        # now build the report

        if wizard.output_type == 'pdf':
            file_name = "{0}.pdf".format(wizard.report_name)
            output = self.create_pdf(wizard, file_name)
        else:
            file_name = "{0}.xlsx".format(wizard.report_name)
            output = self.create_xls(wizard, file_name)

        return output

    def create_pdf(self, wizard, file_name):
        # this is spaced out as we set the column widths based on the actual spacing below
        heading = ['Timestamp                             ', 'LogIn                        ',
                   'Model Name                               ', 'Field Name                         ', 'Method       ',
                   'Old Value                                             ',
                   'New Value                                              ']
        heading_alignment = ['L', 'L', 'L', 'L', 'L', 'L', 'L']
        row_data = self.build_dict(wizard)
        output = self.env['pdf.create'].create_raw_pdf(file_name, heading, row_data, True, heading_alignment)
        return (file_name, file_name, 'Audit Report', StringIO(output))

    def build_dict(self, wizard):
        dict_of_results = defaultdict(dict)

        recs_to_process = self.env['audit.log.report'].search([('wizard_id', '=', wizard.id)], order='sort_name asc')

        for rec in recs_to_process:
            name = rec.sort_name
            lines = self.env['audit.log.report.line'].search([('audit_log_report_id', '=', rec.id)],
                                                             order='timestamp asc')
            for line in lines:
                if line.field_id.ttype in ('binary', 'one2many'):
                    continue
                line_list = ["", "", "", "", "", "", ""]
                line_list[0] = line.timestamp
                line_list[1] = line.login
                line_list[2] = line.model_id.name
                line_list[3] = line.field_id.field_description
                line_list[4] = line.method
                line_list[5] = line.old_value
                line_list[6] = line.new_value
                dict_of_results[name][line.id] = line_list

        return dict_of_results

    def create_xls(self, wizard, file_name):

        data = StringIO()

        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('Data')

        # write headings
        worksheet.write(0, 0, 'Timestamp')
        worksheet.write(0, 1, 'Login')
        worksheet.write(0, 2, 'Model Name')
        worksheet.write(0, 3, 'Field name')
        worksheet.write(0, 4, 'Method')
        worksheet.write(0, 5, 'Old Value')
        worksheet.write(0, 6, 'New Value')

        row = 1
        format_row_bold = workbook.add_format({'text_wrap': True, 'bold': True})
        format_row = workbook.add_format({'text_wrap': True})

        recs_to_process = self.env['audit.log.report'].search([('wizard_id', '=', wizard.id)], order='sort_name asc')

        for rec in recs_to_process:
            row += 1
            worksheet.write(row, 1, rec.sort_name, format_row_bold)
            row += 2
            lines = self.env['audit.log.report.line'].search([('audit_log_report_id', '=', rec.id)],
                                                             order='timestamp asc')
            for line in lines:
                if line.field_id.ttype in ('binary', 'one2many'):
                    continue

                worksheet.write(row, 0, line.timestamp)
                worksheet.write(row, 1, line.login)
                worksheet.write(row, 2, line.model_id.name, format_row)
                worksheet.write(row, 3, line.field_id.field_description, format_row)
                worksheet.write(row, 4, line.method)
                worksheet.write(row, 5, line.old_value, format_row)
                worksheet.write(row, 6, line.new_value, format_row)
                row += 1

        worksheet.set_column('A:B', 20)
        worksheet.set_column('C:D', 30)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:G', 50)
        workbook.close()
        return (file_name, file_name, 'Audit Report', data)


class AuditLogReportLine(models.TransientModel):
    _name = 'audit.log.report.line'

    audit_log_report_id = fields.Many2one(comodel_name='audit.log.report', string='Report')
    audit_log_id = fields.Many2one(comodel_name='audit.logging', string='Audit Log')
    timestamp = fields.Datetime(string='Timestamp')
    login = fields.Char(string='User Name')
    model_id = fields.Many2one(comodel_name='ir.model', string="Model ID")
    field_id = fields.Many2one(comodel_name='ir.model.fields', string="Field ID")
    old_value = fields.Char(string="Original Value")
    new_value = fields.Char(string="Updated Value")
    method = fields.Char(string="Operation type")
