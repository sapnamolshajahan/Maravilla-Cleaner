# -*- coding: utf-8 -*-
from odoo import fields
from odoo.addons.jasperreports_viaduct.viaduct_helper import ViaductHelper


class HazardRiskRegisterReportHelper(ViaductHelper):

    def HeaderDetail(self, hazard_id):
        result = {}

        hazard_pool = self.env["hr.hazard"]
        hazard = hazard_pool.browse(hazard_id)

        today = fields.Date.context_today(hazard)

        result['company'] = self.env.company.name
        result['date-day'] = today.day
        result['date-month'] = today.month
        result['date-year'] = today.year

        return result

    def Hazard(self, hazard_id):

        result = {}
        hazard_pool = self.env["hr.hazard"]
        hazard = hazard_pool.browse(hazard_id)

        result['reference'] = hazard.name
        result['hazard-type'] = hazard.hazard_type_id.name or ""
        result['go-wrong'] = hazard.go_wrong or ""
        result['hazard-identified'] = hazard.hazard_identified or ""
        result['initial-risk-assessment'] = hazard.risk_matrix or ""
        result['preventative-control-measures'] = hazard.control_measure or ""
        result['level-of-control'] = hazard.controls or ""
        result['residual-risk-assessment'] = hazard.residual_risk_assessment or ""

        return result
