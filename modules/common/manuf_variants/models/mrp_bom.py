# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError

from odoo import api, models, fields, _


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    is_intermediate = fields.Boolean(related="product_tmpl_id.is_intermediate")
    # to do: make it required when is_intermediate is True
    fp_bom_id = fields.Many2one("mrp.bom", string="Final Product BoM")

    @api.model_create_multi
    def create(self, vals_list):
        boms = super().create(vals_list)
        for bom in boms:
            if bom.is_intermediate:
                bom.product_id = False

        return boms

    @api.depends(
        'product_tmpl_id.is_intermediate',
    )
    def _compute_possible_product_template_attribute_value_ids(self):
        intermediate_bom_ids = self.filtered_domain([('is_intermediate', '=', True)])
        others = self - intermediate_bom_ids
        super(MrpBom, others)._compute_possible_product_template_attribute_value_ids()

        for bom in intermediate_bom_ids:
            bom.possible_product_template_attribute_value_ids = bom.fp_bom_id.product_tmpl_id.valid_product_template_attribute_line_ids._without_no_variant_attributes().product_template_value_ids._only_active()

    @api.constrains('product_id', 'product_tmpl_id', 'bom_line_ids', 'byproduct_ids', 'operation_ids')
    def _check_bom_lines(self):
        for bom in self:
            apply_variants = bom.bom_line_ids.bom_product_template_attribute_value_ids | bom.operation_ids.bom_product_template_attribute_value_ids | bom.byproduct_ids.bom_product_template_attribute_value_ids
            if bom.product_id and apply_variants:
                raise ValidationError(
                    _("You cannot use the 'Apply on Variant' functionality and simultaneously create a BoM for a specific variant."))
            for ptav in apply_variants:
                if bom.is_intermediate and ptav.product_tmpl_id != bom.fp_bom_id.product_tmpl_id:
                    raise ValidationError(_(
                        "The attribute value %(attribute)s set on product %(product)s does not match the BoM product %(bom_product)s.",
                        attribute=ptav.display_name,
                        product=ptav.product_tmpl_id.display_name,
                        bom_product=bom.fp_bom_id.product_tmpl_id.display_name
                    ))
                elif not bom.is_intermediate and ptav.product_tmpl_id != bom.product_tmpl_id:
                    raise ValidationError(_(
                        "The attribute value %(attribute)s set on product %(product)s does not match the BoM product %(bom_product)s.",
                        attribute=ptav.display_name,
                        product=ptav.product_tmpl_id.display_name,
                        bom_product=bom.product_tmpl_id.display_name
                    ))
            for byproduct in bom.byproduct_ids:
                if bom.product_id:
                    same_product = bom.product_id == byproduct.product_id
                else:
                    same_product = bom.product_tmpl_id == byproduct.product_id.product_tmpl_id
                if same_product:
                    raise ValidationError(_("By-product %s should not be the same as BoM product.", bom.display_name))
                if byproduct.cost_share < 0:
                    raise ValidationError(_("By-products cost shares must be positive."))
            if sum(bom.byproduct_ids.mapped('cost_share')) > 100:
                raise ValidationError(_("The total cost share for a BoM's by-products cannot exceed 100."))
