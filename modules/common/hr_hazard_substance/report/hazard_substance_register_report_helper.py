# -*- coding: utf-8 -*-
from odoo.addons.jasperreports_viaduct.viaduct_helper import ViaductHelper

REGISTER_REPORT = "hazard.substance.register.report.viaduct"


class HazardSubstanceRegisterReportHelper(ViaductHelper):

    def product(self, product_id):
        result = {}

        product_template = self.env["product.template"].browse(product_id)
        product = product_template.product_variant_ids[0]

        result["company"] = product.company_id.name or ""
        result["product-name"] = product.display_name
        result["hazard-approval-nr"] = product.hazard_approval_nr or ""
        result["hazard-classification"] = product.hazard_classifications or ""
        result["hazard-sds-issue-date"] = product.hazard_sds_issuing_date or ""
        result["hazard-storage-reqs"] = product.hazard_storage_reqs or ""
        result["hazard-substance-state"] = product.hazard_material_state or ""
        result["hazard-bin-location"] = product.hazard_location.name or ""
        result["available-qty"] = product.free_qty or ""
        result["max-qty"] = product.hazard_max_qty or ""
        result["hazard-ppe-notes"] = product.hazard_ppe_notes or ""

        return result
