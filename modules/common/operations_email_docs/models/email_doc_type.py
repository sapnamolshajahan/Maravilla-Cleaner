from odoo import fields, models, api

NEW_TYPES = {
    "sale_order": (60, "Sale Order"),
    "packing_slip": (70, "Packing Slip"),
}


class EmailDocTypes(models.Model):
    """
    This module abuses email.doc.type and adds a report-type not tied
    to any particular model. The ${DOC_KEY} type is just a placeholder
    to allow email addresses to be associated to partners for receiving
    back order notifications.
    """
    _inherit = "email.doc.type"

    ###########################################################################
    # Default & compute methods
    ###########################################################################
    @api.model
    def _name_selection_list(self):
        """
        Build ordered selection list for use in name-selection.
        :return: list of tuple [(selection, description)]
        """
        result = super(EmailDocTypes, self)._name_selection_list()

        for k, v in NEW_TYPES.items():
            result.append((v[0], k, v[1]))

        return result

    def get_description(self, name):
        if name in NEW_TYPES:
            return NEW_TYPES[name][1]
        return super(EmailDocTypes, self).get_description(name)

    ###########################################################################
    # Fields
    ###########################################################################
