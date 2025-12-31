# -*- coding: utf-8 -*-
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountCommitmentReportDetailed(models.Model):
    _name = "account.commitment.report.detailed"
    _description = "Detailed Commitments Report"
    _inherit = "account.commitment.base"
    _auto = False

    ###########################################################################
    # Fields
    ###########################################################################
    account = fields.Text(string="Account", readonly=True)
    product_code = fields.Char(string="Product", readonly=True)
    purchase_line_id = fields.Many2one("purchase.order.line", string="Purchase order line", readonly=True)
    invoice_line_id = fields.Many2one("account.move.line", string="Invoice line", readonly=True)

    ###########################################################################
    # Model methods
    ###########################################################################
    @classmethod
    def _get_invoice_query(cls):
        """
        Query to retrieve invoices for the report
        """
        return """
        select
          min (account_move_line.id) AS id,
          account_move_line.id as invoice_line_id,
          account_move_line.currency_id AS currency_id,
          ({date_due}) as date_due,
          account_move_line.name as reference,
          CONCAT(account_account.name::text,' ') AS account,
          account_move_line.company_id AS company_id,
          account_move_line.partner_id AS partner_id,
          product_template.name as product_code,
          account_move_line.price_subtotal AS total_due,
          account_move_line.price_subtotal * {rate} AS local_due,
          account_move_line.purchase_line_id AS purchase_line_id,
          account_move.invoice_date AS tr_date
        from account_move_line
        join account_move
          on account_move_line.move_id = account_move.id
        left join account_payment_term
          on account_move.invoice_payment_term_id = account_payment_term.id
        left join account_payment_term_line
            on account_payment_term_line.payment_id = account_payment_term.id
        left join account_account
          on account_move_line.account_id = account_account.id
        left join product_product
          on account_move_line.product_id = product_product.id
        left join product_template
          on product_product.product_tmpl_id = product_template.id
        where account_move.state not in ('done','cancel')
        and account_move.move_type in ('in_invoice', 'in_refund')
        group by
          account_move_line.id, account_account.name, product_template.name, account_move.id,
          account_payment_term.name, account_payment_term_line.nb_days
        """.format(rate=cls._get_transfer_rate("account_move"),
                   date_due=cls._get_date_due("account_move", "invoice_date_due", "invoice_date"))

    @classmethod
    def _get_purchase_order_query(cls):
        """
        Query to retrieve purchase orders for the report
        """
        return """
        select
          min (line.id + 9000000) as id,
          null as invoice_line_id,
          purchase_order.currency_id AS currency_id,
          ({date_due}) AS date_due,
          line.name AS reference,
          CONCAT(account.name::text,' ') AS account,
          line.company_id AS company_id,
          line.partner_id AS partner_id,
          product_template.name AS product_code,
          sum (line.price_subtotal) AS total_due,
          sum (line.price_subtotal) *  {rate} as local_due,
          line.id AS purchase_line_id,
          purchase_order.date_order AS tr_date
        from purchase_order_line AS line
        join purchase_order on line.order_id = purchase_order.id
        left join account_payment_term
          on purchase_order.payment_term_id = account_payment_term.id
        left join account_payment_term_line
            on account_payment_term_line.payment_id = account_payment_term.id
        left join account_account account
          on line.account = account.id
        left join product_product
          on line.product_id = product_product.id
        left join product_template
          on product_product.product_tmpl_id = product_template.id
        where line.product_qty != line.qty_invoiced
        group by
          line.id, account.name, product_template.name, purchase_order.id,
          account_payment_term.name, account_payment_term_line.nb_days
        having sum (line.qty_invoiced) = 0
        """.format(rate=cls._get_transfer_rate("purchase_order"),
                   date_due=cls._get_date_due("purchase_order", "date_planned", "date_order"))

    def init(self):
        view_name = "account_commitment_report_detailed"
        sql = "create or replace view {view} as ({invoices} union {purchases})".format(
            view=view_name, invoices=self._get_invoice_query(), purchases=self._get_purchase_order_query())
        _logger.debug("sql=" + sql)
        self._cr.execute(sql)
