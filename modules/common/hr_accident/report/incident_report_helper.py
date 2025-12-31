# -*- coding: utf-8 -*-
from odoo.addons.jasperreports_viaduct.viaduct_helper import ViaductHelper


class IncidentReportHelper(ViaductHelper):

    def __init__(self, env):
        self.env = env

    def _append_non_null(self, result, key, str2, sep="\n"):
        if str2:
            if key in result and result[key].strip():
                result[key] += sep + str2
            else:
                result[key] = str2

    def accident(self, accident_id):

        result = {}

        accident = self.env["hr.accident.accident"].browse(accident_id)

        result["created"] = self._2localtime(accident.create_date)
        result["period"] = accident.hr_accident_employment_period_id.name or ""
        result["incident-type"] = accident.hr_incident_type_id.name or ""
        result["treatment"] = accident.hr_accident_injury_treatment_id.name or ""
        result["mechanism"] = accident.hr_accident_event_mechanism_id.name or ""
        result["agency"] = accident.hr_accident_event_agency_id.name or ""
        result["body-part"] = accident.hr_accident_body_part_id.name or ""
        result["company"] = accident.company_id.name or ""
        result["hazard-id"] = accident.hr_hazard_id.display_name or "N/A"

        return result


class DetailedIncidentReportHelper(IncidentReportHelper):

    def accident(self, accident_id):
        result = super(DetailedIncidentReportHelper, self).accident(accident_id)

        accident = self.env["hr.accident.accident"].browse(accident_id)

        result['analysis'] = accident.analysis or ""
        result['seriousness'] = accident.seriousness or ""
        result['future_probability'] = accident.future_probability or ""
        result['actioned_person'] = accident.actioned_person or ""
        result['actioned_date'] = accident.actioned_date or ""
        result['actioned_state'] = accident.actioned_state or ""
        result['assiting_attendee'] = accident.assisting_attendee or ""
        result['medical_entity'] = accident.medical_entity or ""
        result['internal_investigator'] = accident.internal_investigator.name or ""
        result['worksafe_advised'] = accident.worksafe_advised or "no"
        result['investigation_date'] = accident.investigation_date or ""

        return result
