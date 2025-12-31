from odoo.osv import expression
from odoo import models, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @staticmethod
    def _word_split_search(column, search_word):
        """
        Return a tuple usable for search(); splitting the search_word so that matches
        must include all the component words, but in any order.
        """
        result = []
        for word in search_word.split():
            size = len(result)
            if result:
                result.insert(size - 1, "&")
            result.append((column, "ilike", word))
        return result

    # @api.model
    # def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
    #
    #     """
    #     Override the default search method such that if name_search xor default_code
    #     are selected then both are searched.
    #     """
    #     if not domain:
    #         domain = []
    #     if (len(domain) == 1
    #             and [x for x in domain if ('default_code' in x) or ('id' in x)]
    #             and type(domain[0][2]) == str
    #             and not self.env.context.get('exact_match', False)):
    #
    #         search_pattern = domain[0][2]
    #         if search_pattern:
    #             domain = ['|']
    #             domain.extend(self._word_split_search("default_code", search_pattern))
    #             domain.extend(self._word_split_search("name", search_pattern))
    #
    #     else:
    #         # Search for default_code/name with ilike operands
    #         rebuilt = []
    #         for arg in domain:
    #             if (isinstance(arg, (list, tuple))
    #                 and len(arg) == 3
    #                 and arg[1] == "ilike"
    #                 and arg[0] in ["default_code", "name"]) \
    #                     and arg[2]:
    #                 rebuilt.extend(self._word_split_search(arg[0], arg[2]))
    #             else:
    #                 rebuilt.append(arg)
    #         domain = rebuilt
    #     if self.env.context.get('from_purchase_order_misc_product'):
    #         domain.append(('is_misc_product', '=', False))
    #     return super().search_fetch(domain, field_names, offset, limit, order)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80, order=None):
        args = args or []
        if isinstance(name, int):
            name_domain = ['|', '|', '|',
                           ('default_code', operator, name),
                           ('name', operator, name),
                           ('id', operator, name),
                           ('attribute_line_ids', 'ilike', name)]
        else:
            name_domain = ['|', '|',
                           ('default_code', operator, name),
                           ('name', operator, name),
                           ('attribute_line_ids', 'ilike', name)]
        args = expression.AND([name_domain, args])
        if (len(args) == 1 and type(args[0][2]) == str
                and not self.env.context.get('exact_match', False)):
            search_pattern = args[0][2]
            if search_pattern:
                args = ['|', '|', '|']
                args.extend(self._word_split_search("default_code", search_pattern))
                args.extend(self._word_split_search("name", search_pattern))
                args.extend(self._word_split_search("id", search_pattern))
                args.extend(self._word_split_search("attribute_line_ids", search_pattern))
        else:
            rebuilt = []
            for domain in args:
                if (isinstance(domain, (list, tuple))
                    and len(domain) == 3
                    and domain[1] == "ilike"
                    and domain[0] in ["default_code", "name", "id", "attribute_line_ids"]) \
                        and domain[2]:
                    rebuilt.extend(self._word_split_search(domain[0], domain[2]))
                else:
                    rebuilt.append(domain)
            args = rebuilt
        if self.env.context.get('from_purchase_order_misc_product'):
            args.append(('is_misc_product', '=', False))
        return super().name_search(name, args, operator, limit)

    def _has_stock_transactions(self):
        """Check if stock moves exist for any variant of this product template."""
        return self.env['stock.move'].search_count([
            ('product_id.product_tmpl_id', 'in', self.ids),
            ('state', 'not in', ['cancel']),
        ]) > 0

    def write(self, vals):
        if 'lot_valuated' in vals:
            for template in self:
                if template.lot_valuated != vals['lot_valuated']:
                    if template._has_stock_transactions():
                        raise UserError(_(
                            'The Valuation by Lot/Serial Number cannot be changed '
                            'as a transaction has already been applied.'))
        return super().write(vals)



class ProductProduct(models.Model):
    _inherit = 'product.product'

    @staticmethod
    def _word_split_search(column, search_word):
        """
        Return a tuple usable for search(); splitting the search_word so that matches
        must include all the component words, but in any order.
        """
        result = []
        for word in search_word.split():
            size = len(result)
            if result:
                result.insert(size - 1, "&")
            result.append((column, "ilike", word))
        return result

    # @api.model
    # def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
    #
    #     """
    #     Override the default search method such that if name_search xor default_code
    #     are selected then both are searched.
    #     """
    #     if not domain:
    #         domain = []
    #     if (len(domain) == 1
    #             and [x for x in domain if ('default_code' in x) or ('product_tmpl_id' in x)]
    #             and type(domain[0][2]) == str
    #             and not self.env.context.get('exact_match', False)):
    #
    #         search_pattern = domain[0][2]
    #         if search_pattern:
    #             domain = ['|']
    #             domain.extend(self._word_split_search("default_code", search_pattern))
    #             domain.extend(self._word_split_search("product_tmpl_id.name", search_pattern))
    #
    #     else:
    #         # Search for default_code/name with ilike operands
    #         rebuilt = []
    #         for arg in domain:
    #             if (isinstance(arg, (list, tuple))
    #                 and len(arg) == 3
    #                 and arg[1] == "ilike"
    #                 and arg[0] in ["default_code", "name"]) \
    #                     and arg[2]:
    #                 rebuilt.extend(self._word_split_search(arg[0], arg[2]))
    #             else:
    #                 rebuilt.append(arg)
    #         domain = rebuilt
    #
    #     if self.env.context.get('job_service_transaction_search') and not limit:
    #         limit = 80
    #
    #     if self.env.context.get('from_purchase_order_misc_product'):
    #         domain.append(('is_misc_product', '=', False))
    #
    #     return super().search_fetch(domain, field_names, offset, limit, order)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80, order=None):
        args = args or []

        if isinstance(name, int):
            name_domain = ['|', '|', '|',
                           ('default_code', operator, name),
                           ('name', operator, name),
                           ('id', operator, name),
                           ('attribute_line_ids', 'ilike', name)]
        else:
            name_domain = ['|', '|',
                           ('default_code', operator, name),
                           ('name', operator, name),
                           ('attribute_line_ids', 'ilike', name)]

        args = expression.AND([name_domain, args])
        if (len(args) == 1 and type(args[0][2]) == str
                and not self.env.context.get('exact_match', False)):

            search_pattern = args[0][2]
            if search_pattern:
                args = ['|', '|', '|']
                args.extend(self._word_split_search("default_code", search_pattern))
                args.extend(self._word_split_search("name", search_pattern))
                args.extend(self._word_split_search("id", search_pattern))
                args.extend(self._word_split_search("attribute_line_ids", search_pattern))

        else:
            rebuilt = []
            for domain in args:
                if (isinstance(domain, (list, tuple))
                    and len(domain) == 3
                    and domain[1] == "ilike"
                    and domain[0] in ["default_code", "name", "id", "attribute_line_ids"]) \
                        and domain[2]:
                    rebuilt.extend(self._word_split_search(domain[0], domain[2]))
                else:
                    rebuilt.append(domain)
            args = rebuilt

        if self.env.context.get('from_purchase_order_misc_product'):
            args.append(('is_misc_product', '=', False))

        return super().name_search(name, args, operator, limit)

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        """
        To handle inventory in excluded from available stock warehouses (such as the rental warehouse).
        """
        ctx = dict(self.env.context)
        if not self.env.context.get('warehouse', None) and not self.env.context.get('location'):
            warehouses = self.env['stock.warehouse'].search([('exclude_in_avail_stock', '=', False)])
            warehouse_ids = [warehouse.id for warehouse in warehouses]
            ctx['warehouse'] = warehouse_ids
        return super(ProductProduct, self.with_context(ctx))._compute_quantities_dict(lot_id, owner_id, package_id,
                                                                                      from_date=from_date,
                                                                                      to_date=to_date)

    def _has_stock_transactions(self):
        """Check if stock moves exist for this product variant."""
        return self.env['stock.move'].search_count([
            ('product_id', 'in', self.ids),
            ('state', 'not in', ['cancel']),
        ]) > 0

    def write(self, vals):
        if 'lot_valuated' in vals:
            for variant in self:
                if variant.lot_valuated != vals['lot_valuated']:
                    if variant._has_stock_transactions():
                        raise UserError(_(
                            'The Valuation by Lot/Serial Number cannot be changed '
                            'as a transaction has already been applied.'))
        return super().write(vals)
