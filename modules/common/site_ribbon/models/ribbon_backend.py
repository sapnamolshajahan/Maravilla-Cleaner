# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.addons.base_generic_changes.utils.config import configuration

#
# The labels for the attributes can be modified by adding keys under the [site_ribbon] section
# in the odoo.conf file.
#
# Example:
#   [site_ribbon]
#   name = UAT
#   colour = #FFFFFF
#   background = rgba(255,0,0,.6)
#

SECTION_NAME = "site_ribbon"

name_label = configuration.get(SECTION_NAME, "name", fallback="UAT")
colour_label = configuration.get(SECTION_NAME, "colour", fallback="#f0f0f0")
background_label = configuration.get(SECTION_NAME, "background", fallback="rgba(255,0,0,.6)")


class WebEnvironmentRibbonBackend(models.AbstractModel):
    """
    Abstract model for site-ribbon display.
    """
    _name = "site.ribbon.backend"
    _description = __doc__

    @api.model
    def get_display_data(self):
        """
        Returns ribbon data for frontend JS call.
        :return: dictionary
        """
        if name_label:
            colour = colour_label
            background = background_label
        else:
            colour = None
            background = None

        return {
            "name": name_label,
            "color": colour,
            "background_color": background,
        }
