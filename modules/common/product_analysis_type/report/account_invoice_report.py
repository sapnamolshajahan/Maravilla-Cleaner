# -*- coding: utf-8 -*-
from odoo import fields, models,api
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    """
    Tweak invoice report to include product analysis
    """
    _inherit = "account.invoice.report"

    ################################################################################
    # Fields
    ################################################################################
    product_analysis = fields.Many2one("product.analysis.type", string="Analysis Type")

    # @api.model
    # def _select(self):
    #     res = super(AccountInvoiceReport, self)._select()
    #     if isinstance(res, SQL):
    #         res = str(res)
    #
    #     additional_columns = "line.product_analysis AS product_analysis,"
    #     placeholder = "line.partner_id AS commercial_partner_id,"
    #
    #     new_res = res.replace(placeholder, f"{placeholder}{additional_columns}")
    #
    #     print("Modified SQL: %s", new_res)
    #     return new_res

    @api.model
    def _select(self) -> SQL:
        return SQL(
            '''
            SELECT
                line.id,
                line.move_id,
                line.product_id,
                line.account_id,
                line.journal_id,
                line.company_id,
                line.company_currency_id,
                line.product_analysis AS product_analysis,  
                account.account_type AS user_type,
                move.state,
                move.move_type,
                move.partner_id,
                move.invoice_user_id,
                move.fiscal_position_id,
                move.payment_state,
                move.invoice_date,
                move.invoice_date_due,
                uom_template.id                                             AS product_uom_id,
                template.categ_id                                           AS product_categ_id,
                line.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0) * (CASE WHEN move.move_type IN ('in_invoice','out_refund','in_receipt') THEN -1 ELSE 1 END)
                                                                            AS quantity,
                line.price_subtotal * (CASE WHEN move.move_type IN ('in_invoice','out_refund','in_receipt') THEN -1 ELSE 1 END)
                                                                            AS price_subtotal_currency,
                -line.balance * account_currency_table.rate                         AS price_subtotal,
                line.price_total * (CASE WHEN move.move_type IN ('in_invoice','out_refund','in_receipt') THEN -1 ELSE 1 END)
                                                                            AS price_total,
                -COALESCE(
                   -- Average line price
                   (line.balance / NULLIF(line.quantity, 0.0)) * (CASE WHEN move.move_type IN ('in_invoice','out_refund','in_receipt') THEN -1 ELSE 1 END)
                   -- convert to template uom
                   * (NULLIF(COALESCE(uom_line.factor, 1), 0.0) / NULLIF(COALESCE(uom_template.factor, 1), 0.0)),
                   0.0) * account_currency_table.rate                               AS price_average,
                CASE
                    WHEN move.move_type NOT IN ('out_invoice', 'out_receipt') THEN 0.0
                    ELSE -line.balance * account_currency_table.rate - (line.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0)) * COALESCE(product.standard_price -> line.company_id::text, to_jsonb(0.0))::float
                END
                                                                            AS price_margin,
                line.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0) * (CASE WHEN move.move_type IN ('out_invoice','in_refund','out_receipt') THEN -1 ELSE 1 END)
                    * COALESCE(product.standard_price -> line.company_id::text, to_jsonb(0.0))::float                    AS inventory_value,
                COALESCE(partner.country_id, commercial_partner.country_id) AS country_id,
                line.currency_id                                            AS currency_id
            ''',
        )


