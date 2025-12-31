# -*- coding: utf-8 -*-
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountCommitmentReport(models.Model):
    """
    View for statistics.
    """
    _name = "account.commitment.report"
    _description = "Commitments Report"
    _inherit = "account.commitment.base"
    _auto = False

    ###########################################################################
    # Fields
    ###########################################################################
    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order", readonly=True)
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True)

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
          min (account_move.id) as id,
          account_move.id as invoice_id,
          account_move.currency_id as currency_id,
          ({date_due}) as date_due,
          account_move.name as reference,
          account_move.company_id as company_id,
          account_move.partner_id as partner_id,
          account_move.amount_residual_signed as total_due,
          account_move.amount_residual_signed * {rate} as local_due,
          null as purchase_order_id,
          account_move.invoice_date as tr_date
        from account_move
        left join account_payment_term
          on account_move.invoice_payment_term_id = account_payment_term.id
        left join account_payment_term_line
          on account_payment_term_line.payment_id = account_payment_term.id
        left join account_move_line aml on aml.move_id = account_move.id
        join account_account aa on aml.account_id = aa.id
        where account_move.state = 'posted'
        and aa.account_type = 'liquidity_payable'
        and aml.reconciled = null
        and account_move.move_type IN ('in_invoice', 'in_refund')
        and account_move.amount_residual_signed != 0.0
        group by
          account_move.id, account_move.amount_residual_signed,
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
          min (purchase_order.id + 9000000) as id,
          null as invoice_id,
          purchase_order.currency_id as currency_id,
          ({date_due}) as date_due,
          null as reference,
          purchase_order.company_id as company_id,
          purchase_order.partner_id as partner_id,
          sum (pol.price_subtotal) as total_due,
          sum (pol.price_subtotal) * {rate} as local_due,
          purchase_order.id as purchase_order_id,
          purchase_order.date_order as tr_date
        from purchase_order
        join purchase_order_line pol
          on pol.order_id = purchase_order.id
        left join account_payment_term
          on purchase_order.payment_term_id = account_payment_term.id
        left join account_payment_term_line
          on account_payment_term_line.payment_id = account_payment_term.id
        where purchase_order.invoice_status != 'invoiced'
        group by purchase_order.id , account_payment_term.name, account_payment_term_line.nb_days
        having sum (pol.qty_invoiced) = 0
        """.format(rate=cls._get_transfer_rate("purchase_order"),
                   date_due=cls._get_date_due("purchase_order", "date_planned", "date_order"))

    def init(self):
        view_name = "account_commitment_report"
        sql = "create or replace view {view} as ({invoices} union {purchases})".format(
            view=view_name, invoices=self._get_invoice_query(), purchases=self._get_purchase_order_query())
        _logger.debug("sql=" + sql)
        self._cr.execute(sql)
