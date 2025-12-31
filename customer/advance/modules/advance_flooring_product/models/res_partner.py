from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    bank_name = fields.Char(string="Bank")
    bank_account_number = fields.Char(string="Bank Account Number")
    bank_branch = fields.Char(string="Bank Branch")
    date_account_created = fields.Date(string="Date Account Created")
    tax_code = fields.Char(string="Tax Code")
    tax_number = fields.Char(string="Tax Number")
    account_form = fields.Boolean(string="Account Form")
    prompt_payment_terms_id = fields.Many2one(
        'account.payment.term',
        string="Prompt Payment Terms"
    )
    customer_prompt_payment_discount = fields.Float(
        string="Prompt Payment Discount (%)",
        help="If customer pays within the prompt payment term, "
             "this percentage discount will be applied on the invoice."
    )
    customer_priority_id = fields.Many2one(
        'customer.priority',
        string="Customer Priority"
    )
    customer_type_id = fields.Many2one(
        'customer.type',
        string="Customer Type"
    )

