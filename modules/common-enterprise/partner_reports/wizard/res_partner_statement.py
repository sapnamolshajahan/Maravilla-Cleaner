# -*- coding: utf-8 -*-
import base64
import logging
import math
from datetime import datetime, timedelta
from io import BytesIO

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero
from odoo.tools.translate import _

from odoo import models, fields, api
from ..models.email_doctype import STATEMENT_TYPE

logger = logging.getLogger(__name__)


class res_partner_statement(models.TransientModel):
    _name = 'res.partner.statement'
    _description = 'Statement of Account'

    ###########################################################################
    # Fields
    ###########################################################################
    reconcil = fields.Boolean(string="Include Reconciled Entries", help="Consider reconciled entries", default=False)
    type = fields.Selection(selection=[("asset_receivable", "Receivables"), ("liability_payable", "Payables")],
                            string="Type",
                            default="asset_receivable", required=True)
    detailed = fields.Boolean(string="Detailed", help="If checked a detailed report will be produced",
                              default=False)
    partner_ids = fields.Many2many(comodel_name="res.partner", relation="res_partner_statement_partner_rel",
                                   column1="partner_ids", column2="partner_id", string="Partners")
    company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)
    as_at_date = fields.Date(string="As At Date", required=True, default=fields.Date.today)
    zero_transactions = fields.Boolean(string="Include Zero-balance transactions",
                                       help="If unchecked, statements will exclude fully paid transactions",
                                       default=False)
    zero_balance = fields.Boolean(string="Include Zero Balance Statements",
                                  help=("Include or exclude zero balance statements.  Either "
                                        "exclude all or include statements with a zero balance but with "
                                        "transactions in the statement period that brought "
                                        "the balance to zero."), default=False)
    exclude_credit_balance = fields.Boolean(string="Exclude Credit Balance Statements",
                                            help="Include or exclude credit balance statements.", default=False)
    reconcile_offset = fields.Integer(string="Reconciliation Date Offset",
                                      help=("The number of days after month end that reconciled transactions "
                                            "will be treated as happened in the previous month"),
                                      default=1
                                      )
    aging = fields.Selection(selection=[
        ("months", "Age by Months"),
        ("days", "Age by Days"),
    ], string="Aging", required=True, default="months",
        help="Show aging on balances by days or months")
    days = fields.Integer(string="Days", required=True, default=30)
    date_from = fields.Date(string="As at date", required=True, default=fields.Date.today)
    groupdebtor = fields.Boolean(string="Central Debtor", help="If partner is a parent include subsidiaries activity",
                                 default=False)
    print_all_clients = fields.Boolean(string="Select all",
                                       help="Check this box to select all Customers and Suppliers.")
    statement_currency = fields.Many2one(comodel_name="res.currency", string="Currency",
                                         help=("If blank or NZD, all transactions will be included and converted to"
                                               " NZD, otherwise only those transactions for that currency will be "
                                               "selected."),
                                         default=lambda self: self.env.company.currency_id
                                         )
    line_ids = fields.One2many(comodel_name="res.partner.statement.lines", inverse_name="res_partner_statement_id",
                               string="Lines")
    report_name = fields.Char(size=64, string="Report Name", readonly=True, default="Aged Trial Balance.xlsx")
    data = fields.Binary(string="Download File", readonly=True)
    run_as_task = fields.Boolean(string="Run in Background")
    exclude_non_local = fields.Boolean(string="Exclude Not Local Currency",
                                       help=("If checked and currency is company currency then all non-company"
                                             "currency transactions will be excluded")
                                       )
    report_type = fields.Char(size=64, string="Report Type")
    send_email = fields.Boolean(string="Email Statement", readonly=True, default=False)
    due_date = fields.Date(string="Due Date", help=("If entered, only invoices with a due date <= this"
                                                    " or a blank due date will be selected"))

    emailed = fields.Boolean(string='Emailed')
    overdue_only = fields.Boolean(string='Overdue Only')
    in_credit = fields.Boolean(string='In Credit')
    no_email_clients = fields.Boolean(string='No Email Clients',
                                      help='Clients with a balance that would get a printed statement in email run')

    @api.onchange("type")
    def _onchange_type(self):
        """
            Only allow units that are related to this location
        """
        domain = [
            "|",
            ("company_id", "=", False),
            ("company_id", "=", self.company_id.id),
            ("is_company", "=", True),
        ]
        if self.type == "asset_receivable":
            domain.append(("customer", "=", True))
        elif self.type == "liability_payable":
            domain.append(("supplier", "=", True))
        return {
            "domain":
                {
                    "partner_ids": domain
                },
        }

    def __get_move_line_period_start(self):

        if self.aging == 'months':
            date_start = self.as_at_date
            month = date_start.month
            year = date_start.year
            day = '01'
            date_start = parse(str(year) + '-' + str(month) + '-' + day)
            return date_start
        date_start = self.date_from
        return date_start

    def __get_move_line_period_end(self):

        if self.aging == 'months':
            return self.as_at_date
        else:
            return self.date_from

    def _get_index(self, date, base_date):
        """
        This function provides an index for aging and inclusion purposes.
        @return: int which can be used to select/update an item in a list.
        @param date: the date of an invoice
        @param base_date: the date the report is based on
        """
        inv_date = date
        if self.aging == 'months':
            base_month = base_date.month
            base_year = base_date.year
            inv_month = inv_date.month
            inv_year = inv_date.year
            if base_year < inv_year:
                return 0
            if base_year > inv_year:
                base_month += 12 * (base_year - inv_year)
            if inv_month > base_month:
                return 0
            return min((base_month - inv_month), 4)
        else:
            days = self.days
            delta = base_date - inv_date
            period_cnt = delta.days / days
            if period_cnt < 0:
                periods = 0
            else:
                periods = int(math.floor(period_cnt))
            return min(periods, 4)

    @api.model
    def get_to_date_value(self):
        if self.aging == 'days':
            return self.date_from + timedelta(days=self.days)
        else:
            return self.as_at_date

    def _get_move_line_balance(self, line, date_end):

        wizard = self

        """
        the reconcile logic uses the create date of the reconcile id. So for the 1st of the month
        processing of the last days receipts the reconcile create date is 1 days after the date end. 
        We allow for this as default but allow the user to select a higher value
        if processing of the bank statement has been delayed.
        """
        to_date = wizard.get_to_date_value()

        if not line.full_reconcile_id and not line.matched_debit_ids and not line.matched_credit_ids:
            line_balance = line.debit - line.credit
            currency_line_balance = line.amount_currency
        elif line.full_reconcile_id:
            adj_days = wizard.reconcile_offset
            adjusted_date = to_date + timedelta(days=adj_days)
            lastest_reconcile_line = self.env['account.move.line'].search(
                [('full_reconcile_id', '=', line.full_reconcile_id.id)],
                order='date desc', limit=1)
            if lastest_reconcile_line.date > date_end:
                line_balance = line.debit - line.credit
                currency_line_balance = line.amount_currency
            elif line.full_reconcile_id.create_date.date() > adjusted_date:
                line_balance = line.debit - line.credit
                currency_line_balance = line.amount_currency
            else:
                line_balance = 0.0
                currency_line_balance = 0.0
        else:
            # TODO need to handle partly reconciled through matched_debit_ids and matched_credit_ids
            debit_aml = self.env['account.partial.reconcile'].search([('debit_move_id', '=', line.id),
                                                                      ('max_date', '<=', self.as_at_date)])
            credit_aml = self.env['account.partial.reconcile'].search([('credit_move_id', '=', line.id),
                                                                       ('max_date', '<=', self.as_at_date)])
            allocated_amount = sum([x.amount for x in debit_aml]) - sum([x.amount for x in credit_aml])
            line_balance = line.debit - line.credit - allocated_amount
            currency_allocated_amount = sum([x.debit_amount_currency for x in debit_aml]) - sum(
                [x.credit_amount_currency for x in credit_aml])
            currency_line_balance = line.amount_currency - currency_allocated_amount

        return line_balance, currency_line_balance

    def create_line_values(self, wizard, line, sort_name, currency_id, debit, credit, line_balance, ageing_month):
        values = {}
        values.update(
            {
                "res_partner_statement_id": wizard.id,
                "company_id": wizard.company_id.id,
                "parent_partner_id": line.partner_id.parent_id.id or line.partner_id.id,
                "groupdebtor_name": line.partner_id.parent_id.name if line.partner_id.parent_id else line.partner_id.name,
                "transaction_partner_id": line.partner_id.id or wizard.company_id.partner_id.id,
                "sort_name": sort_name,
                "currency_id": currency_id.id or False,
                "reconcile_id": line.full_reconcile_id.id or False,
                "date": line.date,
                "invoice_number": line.move_name,
                "ref": line.ref,
                "debit": debit,
                "credit": credit,
                "balance": line_balance,
                "period0": line_balance if ageing_month == 0 else 0.0,
                "period1": line_balance if ageing_month == 1 else 0.0,
                "period2": line_balance if ageing_month == 2 else 0.0,
                "period3": line_balance if ageing_month == 3 else 0.0,
                "period4": line_balance if ageing_month == 4 else 0.0,
                "move_line": line.id,
                "journal_id": line.journal_id.id,
            })
        return values

    def create_line(self, wizard, line, sort_name, currency_id, debit, credit, line_balance, ageing_month):
        lines_model = self.env["res.partner.statement.lines"]
        values = self.create_line_values(wizard, line, sort_name, currency_id, debit, credit, line_balance,
                                         ageing_month)
        lines_model.create(values)

    def check_currency(self, wizard, company_currency_id):
        if wizard.report_type == "aged.trial.balance.currency.xls.report":
            currency = True
        elif wizard.statement_currency:
            if wizard.statement_currency.id == company_currency_id:
                currency = False
            else:
                currency = wizard.statement_currency
        else:
            currency = False
        return currency

    def _process_move_lines(self, process_dict, date_end):

        company_currency_id = self.env.company.currency_id.id
        precision = self.env["decimal.precision"].precision_get("Accounting")
        count = 0
        k_count = len(process_dict)

        wizard = self[0]
        currency = self.check_currency(wizard, company_currency_id)

        for k, v in process_dict.items():
            count += 1
            logger.info("processing {0}, {1}/{2}".format(k, count, k_count))
            for line in v:
                trans_line_balance, trans_amount_currency_balance = self._get_move_line_balance(line, date_end)
                if currency and (line.currency_id.id == company_currency_id or not line.currency_id):
                    debit = line.debit
                    credit = line.credit
                    line_balance = trans_line_balance
                elif not currency or line.currency_id.id == company_currency_id or not line.currency_id:
                    debit = line.debit
                    credit = line.credit
                    line_balance = trans_line_balance
                else:
                    if line.amount_currency > 0:
                        debit = line.amount_currency
                        credit = 0
                    else:
                        debit = 0
                        credit = line.amount_currency
                    line_balance = trans_amount_currency_balance
                if wizard.type == 'liability_payable':
                    line_balance = line_balance * -1
                currency_id = line.currency_id
                ageing_month = self._get_index(line.date, self.__get_move_line_period_end())

                if not wizard.zero_transactions and float_is_zero(line_balance, precision_digits=precision):
                    continue

                sort_name = line.partner_id.name or wizard.company_id.name
                if wizard.groupdebtor and line.partner_id.parent_id:
                    sort_name = line.partner_id.parent_id.name

                if wizard.due_date:
                    if line.date_maturity and line.date_maturity > wizard.due_date:
                        continue

                self.create_line(wizard, line, sort_name, currency_id, debit, credit, line_balance, ageing_month)

    def _exclude_reconciled_moves(self, move_ids, date_start, date_end):
        """
        This removes the reconciled items up to the start of the month so statements just show transcations for the current month
        """
        keep_move_line = []
        logger.info("Starting exclude reconciled")
        reconcile_cut_off = date_start + timedelta(days=self.reconcile_offset)

        for move in move_ids:
            if move in keep_move_line:
                continue

            move = self.env['account.move.line'].browse(move)
            if not move.full_reconcile_id:
                keep_move_line.append(move.id)
                continue

            if move.full_reconcile_id.create_date > datetime(reconcile_cut_off.year, reconcile_cut_off.month,
                                                             reconcile_cut_off.day):
                keep_move_line.append(move.id)
                continue

            latest_for_this_reconcile = self.env['account.move.line'].search([
                ('full_reconcile_id', '=', move.full_reconcile_id.id)],
                order='id desc', limit=1)

            if latest_for_this_reconcile.date > date_end:
                keep_move_line.append(move.id)

            logger.info("Ending reconciled")

        return list(set(keep_move_line))

    def get_move_lines_sql(self, select_date, check_reconcile_date, account_ids, partner_id, report_type,
                           statement_currency):

        sql_select = (
            """ select aml.id from account_move_line aml 
            left join account_full_reconcile afr on aml.full_reconcile_id = afr.id 
            where aml.date <= %s 
            and aml.parent_state = 'posted' 
            and (aml.full_reconcile_id is null or afr.create_date >= %s)""")

        params = (fields.Date.to_string(select_date), fields.Date.to_string(check_reconcile_date))

        sql_select += " and aml.account_id in %s "
        params += (tuple(account_ids),)

        if partner_id:
            partner_ids = partner_id if isinstance(partner_id, list) else [partner_id]

            if self.groupdebtor:
                # Find children and grandchildren, and append into the list of partner to look for
                children = self.env['res.partner'].search([('parent_id', 'in', partner_ids)])
                partner_ids += children.ids

                grandchildren = self.env['res.partner'].search([('parent_id', 'in', children.ids)])
                partner_ids += grandchildren.ids

            # Append partners into the params
            sql_select += " and aml.partner_id in %s "
            params += (tuple(partner_ids),)

        local_currency = self.env.company.currency_id.id
        if report_type == "aged.trial.balance.currency.xls.report":
            pass
        elif (statement_currency and statement_currency == local_currency) or not statement_currency:
            if self.exclude_non_local:
                sql_select += " and aml.currency_id is null or currency_id = %s "
                params += (local_currency,)
        else:
            sql_select += " and aml.currency_id  = %s "
            params += (statement_currency,)

        if self.as_at_date:
            date_start = self.__get_move_line_period_start()
            date_end = self.__get_move_line_period_end()
        else:
            # ie as at date for non-monthly ageing
            date_end = self.date_from
            date_start = self.date_from - relativedelta(days=self.days)

        """
        little hack for old historical Zeald transactions - there are thousands that have no partner so
        the report keeps running out of memory. Unfortunately they do not balance so can't just set a reconcile id.
        So check and if too many just exclude anything with no partner

        """
        if len(account_ids) == 1:
            sql_check = "select count(*) from account_move_line where account_id = {accounts} and partner_id is null"
            self.env.cr.execute(sql_check.format(accounts=account_ids[0]))
        else:
            sql_check = "select count(*) from account_move_line where account_id in {accounts} and partner_id is null"
            self.env.cr.execute(sql_check.format(accounts=tuple(account_ids)))

            no_partner_count = self.env.cr.fetchall()
            if no_partner_count[0][0] > 5000:
                sql_select += " and aml.partner_id is not Null "

        return sql_select, params, date_start, date_end

    def exclude_zero_transactions(self, move_ids, date_end):
        """
        if the line is fully reconciled then exclude as long as this reconcile does not have transactions after the period end.
        Exclude reconciled lines has already excluded old stuff. This is for current transactions so only open items show
        """
        keep_moves = []
        reconcile_cut_off = date_end + timedelta(days=self.reconcile_offset)

        for move in move_ids:
            if move in keep_moves:
                continue
            move = self.env['account.move.line'].browse(move)
            if not move.full_reconcile_id:
                keep_moves.append(move.id)
                continue

            if move.full_reconcile_id and move.full_reconcile_id.create_date > \
                    datetime(reconcile_cut_off.year, reconcile_cut_off.month, reconcile_cut_off.day):
                keep_moves.append(move.id)
                continue

            latest_for_this_reconcile = self.env['account.move.line'].search(
                [('full_reconcile_id', '=', move.full_reconcile_id.id)],
                order='id desc', limit=1)
            if latest_for_this_reconcile.date > date_end:
                keep_moves.append(move.id)

        return keep_moves

    def _get_move_lines(self, partner_id, statement_currency, account_ids, report_type):
        '''
        @return: Move Lines as Browse Records
        '''
        logger.info("Starting get move lines")
        process_dict = {}
        item_ct = 0
        move_line_model = self.env['account.move.line']

        # if for a specific partner and not just a monthly report then allow use to specify a large number
        # so they can generate a statement covering multiple periods
        if self.partner_ids and self.date_from:
            offset_days = self.days * 2
        else:
            offset_days = 40

        # set an offset of 40 days just to be sure
        if self.as_at_date:
            check_reconcile_date = self.as_at_date - timedelta(days=offset_days)
            select_date = self.as_at_date
        else:
            check_reconcile_date = self.date_from - timedelta(days=offset_days)
            select_date = self.date_from

        sql_select, params, date_start, date_end = self.get_move_lines_sql(select_date, check_reconcile_date,
                                                                           account_ids, partner_id, report_type,
                                                                           statement_currency)

        self.env.cr.execute(sql_select, params)
        move_ids = self.env.cr.fetchall()

        logger.info('count move_ids : {0}'.format(len(move_ids)))

        if not move_ids:
            return [], date_end
        if not self.reconcil and report_type != 'ar.ap.audit.xls.report':
            move_ids = self._exclude_reconciled_moves(move_ids, date_start, date_end)
        keep_move_lines_rows = move_ids

        if not move_ids:
            return [], date_end

        if not self.zero_transactions:
            keep_move_lines_rows = self.exclude_zero_transactions(move_ids, date_end)

        move_line_rows_sql_statement = "select id from account_move_line where id in %s and date <= %s order by move_id"
        if keep_move_lines_rows:
            self.env.cr.execute(move_line_rows_sql_statement,
                                (tuple(keep_move_lines_rows), fields.Date.to_string(date_end)))
            keep_move_lines_rows = self.env.cr.fetchall()

        move_line_ids = [mvl_row[0] for mvl_row in keep_move_lines_rows]
        move_line_records = move_line_model.browse(move_line_ids)

        for item in move_line_records:
            item_ct += 1
            key_entry = TransactionMapKey(transaction_browse=item)
            if key_entry in process_dict:
                process_dict[key_entry].append(item)
            else:
                process_dict[key_entry] = [item]

        return process_dict, date_end

    def get_partners(self, report_type):
        """
        If all partners selected then do nothing as we do not use for selection purposes
        """
        if not self.print_all_clients and not self.no_email_clients and len(self.partner_ids) == 0:
            raise UserError(_("Oops looks like you have not set a value. Either check \"Select all\" or add Partners."))

        partner_ids = []
        if report_type == 'ar.ap.audit.xls.report' or (
                self.type == 'asset_receivable' and self.type == 'liability_payable'):
            possible_partners = self.env['res.partner'].with_context(active_test=False).search([
                ('is_company', '=', True),
            ])

        elif self.type == 'asset_receivable':
            possible_partners = self.env['res.partner'].with_context(active_test=False).search([
                ('is_company', '=', True),
                ('customer', '=', True)
            ])

        elif self.type == 'liability_payable':
            possible_partners = self.env['res.partner'].with_context(active_test=False).search([
                ('is_company', '=', True),
                ('supplier', '=', True)
            ])

        else:
            possible_partners = self.env['res.partner'].with_context(active_test=False).search([
                ('is_company', '=', True),
            ])

        if self.no_email_clients:
            for partner in possible_partners:
                if not partner.has_doctype("partner-statement"):
                    partner_ids.append(partner.id)

        elif not self.print_all_clients:
            partner_ids = self.partner_ids.ids

        return partner_ids

    def _filter_zero_balance(self):
        """Filter out partner statements that have a Zero balance if required.
        """
        precision = self.env["decimal.precision"].precision_get("Account")
        line_model = self.env["res.partner.statement.lines"]

        if self.groupdebtor:
            partner_filter = "parent_partner_id"
        else:
            partner_filter = "transaction_partner_id"

        partner_ids = set()
        for line in line_model.search([("res_partner_statement_id", "=", self.id)]):
            partner_ids.add(line[partner_filter].id)

        for partner_id in partner_ids:
            lines = line_model.search(
                [
                    ("res_partner_statement_id", "=", self.id),
                    (partner_filter, "=", partner_id),
                ])
            partner_balance = sum([x.balance for x in lines])
            if float_is_zero(partner_balance, precision_digits=precision):
                remove = True
                if self.zero_balance:
                    # Include zero-balance only if there are transactions in current-period
                    period0_balance = sum([abs(x.period0) for x in lines])
                    if not float_is_zero(period0_balance, precision_digits=precision):
                        remove = False
                if remove:
                    lines.unlink()
                    logger.info("zero-filtered partner={0}".format(partner_id))

            if self.exclude_credit_balance:
                if partner_balance < 0:
                    line.unlink()
                    logger.info("credit-filtered partner={0}".format(partner_id))

    @api.model
    def get_statement_report(self):
        """
        Override to use custom statement.
        :return: ir.actions.report record
        """
        return self.env.ref("partner_reports.generic_partner_statement")

    def get_statement_report_filename(self):
        """
        File names can be overwritten for customers
        """
        return "Partner Statement"

    def run_report(self, wizard):

        report = self.get_statement_report()

        if wizard.send_email:
            result, rpt_format = self._email_statements(report, wizard)
            if not result:
                return None
        else:
            self.env.cr.commit()  # forced commit to allow Viaduct to view records
            result, rpt_format = report._render(report, wizard.ids, {})

        report_filename = "{}.{}".format(wizard.get_statement_report_filename(), rpt_format)
        return report.name, report_filename, "Statements", BytesIO(result)

    def _do_report(self, report_type):
        """
       Creates the underlying report data into the transient model below
       and then calls the required report
        """
        if self.aging == 'months' and not self.as_at_date:
            raise UserError('Please specify As At Date field')

        start_time = datetime.now()
        partner_ids = self.get_partners(report_type)
        statement_currency = False
        if self.statement_currency:
            statement_currency = self.statement_currency.id

        if report_type == 'ar.ap.audit.xls.report':
            accounts = self.env["account.account"].search([
                ('company_ids', 'in', self.company_id.id),
                ('account_type', 'in', ('asset_receivable', 'liability_payable')),
            ])
        else:
            accounts = self.env["account.account"].search([
                ('company_ids', 'in', self.company_id.id),
                ('account_type', '=', self.type),
            ])

        account_ids = [x.id for x in accounts]

        if self.print_all_clients:
            process_dict, date_end = self._get_move_lines(partner_ids, statement_currency, account_ids, report_type)

            if not process_dict:
                raise UserError("No records to process. Check selection")

            self._process_move_lines(process_dict, date_end)

        else:
            for partner_id in partner_ids:
                process_dict, date_end = self._get_move_lines(partner_id, statement_currency, account_ids, report_type)

                if not process_dict and len(partner_ids) == 1:
                    raise UserError("No records to process. Check selection")

                elif process_dict:
                    self._process_move_lines(process_dict, date_end)

        if not self.zero_balance and not self.zero_transactions:
            self._filter_zero_balance()

        if not report_type and self.report_type:
            report_type = self.report_type

        result = None
        if self.line_ids and report_type:
            result = self.env[report_type].run_report(self)
        elif not self.line_ids:
            raise UserError("There are only zero transactions for this statement configuration.")

        logger.info("check_report completed - elapsed = {elapsed} seconds".format(
            elapsed=(datetime.now() - start_time).seconds
        ))

        return result

    def _email_statements(self, report_name, wizard):
        """
        Email statements to partners who have an email address,
        and produce a report for all the others who don't.
        """
        line_model = self.env["res.partner.statement.lines"]
        email_model = self.env["res.partner.statement.email"]

        email_partners = set()
        no_email_partners = set()

        if wizard.groupdebtor:
            partner_col = "parent_partner_id"
        else:
            partner_col = "transaction_partner_id"

        for line in line_model.search([("res_partner_statement_id", "=", wizard.id)]):

            partner = line[partner_col]
            if not partner:
                continue

            if partner.has_doctype(STATEMENT_TYPE):
                email_partners.add(partner)
            else:
                no_email_partners.add(partner)

        emails = []
        for partner in email_partners:
            email = email_model.create(
                {
                    "res_partner_statement_id": wizard.id,
                    "partner_id": partner.id,
                })
            emails.append(email)

        self.env.cr.commit()  # force commit to allow Viaduct to see all new data.

        for email in emails:
            self.env["email.async.send"].send(STATEMENT_TYPE, [email.id], email.partner_id, email_model._name)

        if not no_email_partners:
            return None, None

        report_data = {
            "viaduct-parameters": {
                "all-partners": False,
                "partner-ids": [x.id for x in no_email_partners],
            },
        }
        odoo_report = self.get_statement_report()
        return self.env['ir.actions.report']._render_qweb_pdf(odoo_report, res_ids=wizard.ids, data=report_data)

    def submit_task(self, report_type):
        """ Submit a task to run the report based on the wizard.
        """
        self.report_type = report_type
        self.with_delay(
            channel=self.light_job_channel(),
            description="Run Partner Report").run_in_background(self.id, report_type, self.env.uid)

        return {"type": "ir.actions.act_window_close"}

    @api.model
    def run_in_background(self, wizard_id, report_type, run_uid):
        if 'job_uuid' in self.env.context:

            result = self.with_user(run_uid).browse(wizard_id)._do_report(report_type)
            if result:
                name, file_name, desc, data = result

                queue_model = self.env["queue.job"].sudo()
                job_uuid = self.env.context["job_uuid"]
                task = queue_model.search([('uuid', '=', job_uuid)], limit=1)

                if task:
                    self.env["ir.attachment"].sudo().create({
                        "name": file_name,
                        "datas": base64.encodebytes(data.getvalue()),
                        "mimetype": "application/octet-stream",
                        "description": file_name,
                        "res_model": task._name,
                        "res_id": task.id,
                    })

            return "Completed Successfully"

        return "No Task Found?"

    def run_in_foreground(self, report_type):
        self.line_ids = False
        self.report_type = report_type

        result = self._do_report(report_type)
        if not result:
            return {"type": "ir.actions.act_window_close"}

        _name, file_name, _desc, data = result

        data.seek(0)
        output = base64.encodebytes(data.read())
        self.write(
            {
                "data": output,
                "report_name": file_name,
            })
        view = self.env.ref("partner_reports.partner_statement_download_view")
        return {
            "name": view.name,
            "type": "ir.actions.act_window",
            "res_model": "res.partner.statement",
            "view_mode": "form",
            "view_id": view.id,
            "res_id": self.id,
            "target": "new",
        }

    def print_audit_atb(self):
        self.write({'print_all_clients': True})
        report_type = "ar.ap.audit.xls.report"

        if not self.as_at_date:
            # set to the future to catch forward dated transactions as well
            self.write({'as_at_date': '2100-01-01'})

        if self.run_as_task:
            return self.submit_task(report_type)

        return self.run_in_foreground(report_type)

    def print_atb(self):

        report_type = "aged.trial.balance.xls.report"
        if self.run_as_task:
            return self.submit_task(report_type)
        return self.run_in_foreground(report_type)

    def print_statement(self):

        report_type = "res.partner.statement"
        if self.run_as_task:
            return self.submit_task(report_type)
        if self.print_all_clients:
            raise UserError('Do not try and print statements for all clients in foreground.')
        return self.run_in_foreground(report_type)

    def email_statement(self):
        # To avoid duplicate errors on any button double clicks
        if self.emailed:
            return

        action = None
        report_type = "res.partner.statement"
        self.send_email = True
        if self.run_as_task or self.print_all_clients:
            self.submit_task(report_type)
        else:
            action = self.run_in_foreground(report_type)

        # This wizard has been emailed, indicate it to avoid duplicates
        self.emailed = True
        return action

    def print_atb_by_currency(self):

        report_type = "aged.trial.balance.currency.xls.report"
        if self.run_as_task:
            return self.submit_task(report_type)
        return self.run_in_foreground(report_type)

    def print_detail_atb(self):
        report_type = "detailed.aged.trial.balance.report"
        if self.run_as_task:
            return self.submit_task(report_type)
        return self.run_in_foreground(report_type)


class res_partner_statement_lines(models.TransientModel):
    _name = 'res.partner.statement.lines'
    _description = 'Statement of Account Lines'

    ###########################################################################
    # Fields
    ###########################################################################
    res_partner_statement_id = fields.Many2one(comodel_name="res.partner.statement", string="Statement")
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    parent_partner_id = fields.Many2one(comodel_name="res.partner", string="Parent")
    groupdebtor_name = fields.Char(string="GroupDebtor Name", size=64)
    transaction_partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")
    sort_name = fields.Char(string="Sort Name", size=64)
    account_move_line_ids = fields.One2many(comodel_name="account.move.line",
                                            inverse_name="id", string="Account Move Lines")
    reconcile_id = fields.Many2one(comodel_name="account.full.reconcile", string="Reconcile ID")
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency")
    date = fields.Date(string="Date")
    invoice_number = fields.Char(string="Invoice Number", size=64)
    ref = fields.Char(string="Ref", size=64)
    debit = fields.Float(string="Debit", digits=(18, 4))
    credit = fields.Float(string="Credit", digits=(18, 4))
    balance = fields.Float(string="Balance", digits=(18, 4))
    period0 = fields.Float(string="Period 0", digits=(18, 4))
    period1 = fields.Float(string="Period 1", digits=(18, 4))
    period2 = fields.Float(string="Period 2", digits=(18, 4))
    period3 = fields.Float(string="Period 3", digits=(18, 4))
    period4 = fields.Float(string="Period 4", digits=(18, 4))
    move_line = fields.Many2one(comodel_name="account.move.line", string="Account Move line")
    journal_id = fields.Many2one(comodel_name="account.journal", string="Account Journal")
    ignore = fields.Boolean(string='Technical field - this line gets ignored')


class TransactionMapKey(object):
    """ Provides a key to the map of lines to be processed.

    Attributes:
        move_id: unique move_id
    """

    move_id = 0

    def __init__(self, transaction_browse=None):

        if transaction_browse:
            self.move_id = transaction_browse.move_id.id

    def __eq__(self, other):
        if isinstance(other, TransactionMapKey):
            if self.move_id == other.move_id:
                return True

        return False

    def __hash__(self):
        return hash((self.move_id))

    def __str__(self):
        return 'Move {move_id}'.format(move_id=self.move_id)

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()
