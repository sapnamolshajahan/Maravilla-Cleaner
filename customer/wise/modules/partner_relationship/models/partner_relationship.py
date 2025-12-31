# -*- coding: utf-8 -*-
from odoo import fields, models, api

class PartnerRelationship(models.Model):
    """
    Simple single level group of partners
    """
    _name = "partner.relationship"
    _description = 'Partner Relationships'
    _rec_name = 'partner'

    company_id = fields.Many2one(
        "res.company", string="Company", required=True, ondelete="cascade",
        default=lambda self: self.env.company
    )
    partner = fields.Many2one('res.partner', string='Person')
    relationship_type = fields.Many2one('partner.relationship.type', string='Relationship Type')
    related_partners = fields.Many2many('res.partner', string='Related People')
    active = fields.Boolean("Active", default=True)

    def create_other_side(self, created_record, other_partner, relationship_type):

        self.env['partner.relationship'].with_context(partner_relationship=True).create({
            'partner': other_partner,
            'relationship_type': relationship_type,
            'related_partners': [(6, 0, [created_record.partner.id])]
        })


    @api.model
    def create(self, values):

        res = super(PartnerRelationship, self).create(values)

        for record in res:
            # Prevent recursive call
            if self.env.context.get('partner_relationship', None):
                return res

            if record.related_partners:
                for partner in record.related_partners:

                    created = self.search([
                        ('partner', '=', partner.id),
                        ('relationship_type', '=', record.relationship_type.related_type.id)
                    ])

                    if created:
                        continue
                    else:

                        self.with_delay(
                            channel='partner_relationships',
                            description="Create Other side of relationships"
                        ).create_other_side(
                            record,
                            partner.id,
                            record.relationship_type.related_type.id
                        )

        return res


class PartnerRelationshipType(models.Model):
    _name = 'partner.relationship.type'
    _description = 'Partner Relationship Type'

    name = fields.Char(string='Description')
    related_type = fields.Many2one('partner.relationship.type', string='Related Type')
