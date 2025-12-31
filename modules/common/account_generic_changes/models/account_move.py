# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_fiscal_lock_dates(self):
        super(AccountMove, self)._check_fiscal_lock_dates()
        for move in self:
            if move.state == 'posted':
                fiscal_year_last_lock_date = move.company_id.fiscal_year_last_lock_date

                if fiscal_year_last_lock_date and (move.date > fiscal_year_last_lock_date):
                    message = (
                        "You cannot add/modify entries after the last lock date {d}. "
                        "Ask someone with the 'Adviser' role"
                    ).format(d=fiscal_year_last_lock_date)

                    raise UserError(message)

        return True

    def _get_account_move_sequence(self, journal=False):
        """
        Return the sequence to be used during the post of the current move.

        :return: An ir.sequence record or False.
        """
        self.ensure_one()
        if not journal:
            journal = self.journal_id
        if (self.move_type in ("entry", "out_invoice", "in_invoice") or not journal.refund_sequence) \
                and journal.sequence_id:
            return journal.sequence_id

        if self.move_type in ('out_refund', 'in_refund') and journal.refund_sequence_id:
            return journal.refund_sequence_id

        return self.env.ref("account_generic_changes.default_journal_sequence")

    ###########################################################################
    # Fields
    ###########################################################################
    journal_short_description = fields.Char(related='journal_id.short_description', string="TR Type")
    invoice_address = fields.Many2one(comodel_name="res.partner", string="Invoice Address")
    sequence_set = fields.Boolean(string='Sequence Set', help='Technical field to stop sequences jumping', copy=False)

    # Field below is just changing from read only to editable after invoice is validated
    invoice_payment_term_id = fields.Many2one(
        "account.payment.term", string="Payment Terms",
        help="If you use payment terms, the due date will be computed automatically at the generation "
             "of accounting entries. If you keep the payment terms and the due date empty, it means direct payment. "
             "The payment terms may compute several due dates, for example 50% now, 50% in one month.")

    ###########################################################################
    # Methods
    ###########################################################################

    def _constrains_date_sequence(self):
        # Make it possible to bypass the constraint to allow edition of already messed up documents.
        # /!\ Do not use this to completely disable the constraint as it will make this mixin unreliable.
        constraint_date = fields.Date.to_date(self.env['ir.config_parameter'].sudo().get_param(
            'sequence.mixin.constraint_start_date',
            '1970-01-01'
        ))

        for record in self:
            date = fields.Date.to_date(record[record._sequence_date_field])
            sequence = record[record._sequence_field]
            sequence_config = record._get_account_move_sequence()

            if sequence_config:
                seq_date = self.env['ir.sequence.date_range'].search([
                    ('sequence_id', '=', sequence_config.id),
                    ('date_from', '<=', date),
                    ('date_to', '>=', date)
                ], limit=1)
            else:
                seq_date = False

            if not seq_date:
                return

            if not (seq_date.date_from <= date <= seq_date.date_to) and date > constraint_date:
                raise ValidationError(_(
                    "The %(date_field)s (%(date)s) doesn't match the %(sequence_field)s (%(sequence)s).\n"
                    "You might want to clear the field %(sequence_field)s "
                    "before proceeding with the change of the date.",
                    date=format_date(self.env, date),
                    sequence=sequence,
                    date_field=record._fields[record._sequence_date_field]._description_string(self.env),
                    sequence_field=record._fields[record._sequence_field]._description_string(self.env),
                ))

    def action_reset_journal(self):
        res_id = ''
        group_ids = [gp.id for gp in self.env.user.groups_id]
        model_id = self.env['ir.model.data'].search([('name', '=', 'group_account_manager')])
        if model_id:
            res_id = model_id[0].res_id
        if res_id and res_id not in group_ids:
            raise UserError(_('Current User is not allowed to reset the state'))
        self.write({'state': 'draft'})

        return {}

    @api.model_create_multi
    def create(self, vals_list):
        for i, vals in enumerate(vals_list):
            if not vals.get('ref', None):
                if vals.get('line_ids', None):
                    try:
                        first_line = vals['line_ids'][0][2]
                        if first_line.get('name', None):
                            vals['ref'] = first_line['name']
                    except:
                        pass

        return super(AccountMove, self).create(vals_list)

    @api.model
    def get_name_get_types(self):
        return {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Vendor Bill'),
            'out_refund': _('Refund'),
            'in_refund': _('Vendor Refund'),
        }

    def _get_move_display_name(self, show_ref=False):
        show_ref = False
        return super(AccountMove, self)._get_move_display_name(show_ref)

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed=relaxed)
        payment_string = where_string.find('AND payment_id IS NOT NULL')
        if payment_string:
            where_string = where_string.replace('AND payment_id IS NOT NULL', '')
        return where_string, param

    def action_post(self):
        """ Invoice validate processing.

            Partner on the invoice must match the partner on the purchase order if specified.
        """
        for record in self:
            if record.move_type in ['in_invoice', 'in_refund'] and self.env.company.supplier_partner_check:
                for line in record.line_ids:
                    if hasattr(line, 'purchase_line_id'):
                        if line.purchase_line_id and line.purchase_line_id.order_id.partner_id != record.partner_id:
                            raise UserError(_(
                                "Invoice: {} cannot be validated as "
                                "the supplier does not match Purchase Order: {}").format(
                                record.name, line.purchase_line_id.order_id.display_name
                            ))

            if record.ref and record.move_type in ['in_invoice', 'in_refund']:
                exist = self.search_count(
                    [
                        ("ref", "=", record.ref),
                        ("company_id", "=", record.company_id.id),
                        ("partner_id", "=", record.partner_id.id)
                    ])
                if exist > 1:
                    raise UserError(
                        f"Supplier Invoice Ref: {record.ref} is not unique\n"
                        "Supplier Invoice Number must be unique per supplier/vendor.")

            if record.move_type in ['in_invoice', 'in_refund', 'out_invoice', 'out_refund']:
                for line in record.invoice_line_ids:
                    if not line.display_type and not line.tax_ids:
                        raise UserError(
                            ('No Tax is set for a line on this invoice. '
                             'Review taxes to proceed'))
                    if line.tax_ids and len(line.tax_ids) > 1:
                        raise UserError(
                            ('Only one Tax per line allowed on an invoice. '
                             'Review taxes to proceed'))
            else:
                for line in record.line_ids:
                    if line.tax_ids and len(line.tax_ids) > 1:
                        raise UserError(
                            'Only one Tax per line allowed. Review taxes to proceed')

            # Setup invoice name from the sequence if not set already
            record.get_invoice_name_from_sequence()

        res = super(AccountMove, self).action_post()

        for move in self.filtered(lambda m: m.state == 'posted'):
            # Setup invoice name from the sequence if not set already
            move.get_invoice_name_from_sequence()

        return res

    def get_invoice_name_from_sequence(self, journal_id=False):
        def get_next_name():
            name = sequence.with_context(ir_sequence_date=self.date).next_by_id()

            if not self.sudo().search([('name', '=', name)]):
                return name

            return get_next_name()

        if not self.sequence_set:
            sequence = self._get_account_move_sequence(journal_id)
            if sequence:
                try:
                    self.name = get_next_name()
                except RecursionError:
                    raise UserError(
                        "Check sequence {} (ID {}) - it might have to be restarted with the correct next value. "
                        "Contact Odoo admins for support.".format(sequence.name, sequence.id))

                self.sequence_set = True

            else:
                journal = journal_id or self.journal_id
                raise UserError(_('Please define document sequence on the journal {}'.format(
                    journal and journal.name or "")))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):

        res = super(AccountMove, self)._onchange_partner_id()

        if self.partner_id and self.move_type in (
                'out_invoice', 'out_refund') and self.partner_id.property_product_pricelist.currency_id.id:
            self.currency_id = self.partner_id.property_product_pricelist.currency_id.id

        invoice_date = self.invoice_date
        if not invoice_date:
            self.invoice_date = fields.Date.context_today(self)

        return res

    #
    # getting some transactions sitting in in payment status even though fully paid
    def calc_payment_status(self):
        moves = self.env['account.move'].search([
            ('move_type', 'in', ('in_invoice', 'in_refund', 'out_invoice', 'out_refund')),
            ('payment_state', '=', 'in_payment')])

        for move in moves:
            if not move.amount_residual:
                ar_ap_line = move.line_ids.filtered(
                    lambda x: x.account_id.account_type in ('asset_receivable', 'liability_payable'))

                if ar_ap_line:
                    reconcile_id = ar_ap_line[0].full_reconcile_id
                    if reconcile_id:
                        bank_line = self.env['account.move.line'].search([
                            ('full_reconcile_id', '=', reconcile_id.id),
                            ('id', '!=', ar_ap_line[0].id)], limit=1)

                        if bank_line.account_id.account_type == 'asset_cash':
                            move.write({'payment_state': 'paid'})

    def action_export(self):
        self.ensure_one()
        wizard = self.env['account.journal.export'].create(
            {'move_id': self.id}
        )
        return {
            "name": "Journal Export",
            "view_mode": "form",
            "res_model": "account.journal.export",
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for record in self:
            if record.move_id.sequence_number and not record.move_id.sequence_set:
                sequence = record.move_id.journal_id.sequence_id
                if sequence:
                    if sequence.number_next <= record.move_id.sequence_number:
                        sequence.number_next = record.move_id.sequence_number + 1
                        record.move_id.sequence_set = True

        return res
