# -*- encoding: utf-8 -*-
from odoo import fields, models, api


class HrHazardType(models.Model):
    _name = "hr.hazard.type"
    _description = "Hazard Type"

    ###########################################################################
    #  Fields
    ###########################################################################

    sequence = fields.Integer(string="Sequence", help="Sequence for order in view")
    name = fields.Char(string="Name", size=256, required=True, help="Name of the Hazard Type.")
    active = fields.Boolean(string="Active",
                            help="Indicates whether the Type is active or not.", default=True)

    _order = 'sequence'


class HrHazardHarmed(models.Model):
    _name = "hr.hazard.harmed"
    _description = "Hazard Who Harmed"

    ###########################################################################
    # Fields
    ###########################################################################

    sequence = fields.Integer(string="Sequence", help="Sequence for order in view")
    name = fields.Char(string="Name", size=256, required=True, help="Name of the Hazard Type.")
    active = fields.Boolean(string="Active",
                            help="Indicates whether the Type is active or not.", default=True)

    _order = 'sequence'


class HrHazard(models.Model):
    _name = "hr.hazard"
    _description = "Hazard"

    ###########################################################################
    # Fields
    ###########################################################################

    create_date = fields.Datetime(string="Date Created", readonly=True)
    name = fields.Char(string="Reference", size=32, required=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('hr.hazard'))
    hazard_type_id = fields.Many2one("hr.hazard.type",
                                     string="Hazard Type", required=True, help="Hazard Type.")
    hazard_identified = fields.Char(string="Hazard Identified", size=128, required=True, help="Hazard information")
    description = fields.Text(string="Description", required=True, help="Hazard information")
    go_wrong = fields.Text(string="What Can Go Wrong", required=True, help="Hazard information")

    who_harmed = fields.Many2many("hr.hazard.harmed", relation="hr_hazard_harmed_rel",
                                  column1="hr_hazard_id",
                                  column2="hr_hazard_harmed_id", string="Who could be Harmed")

    how_harmed = fields.Char(string="How Harmed", size=128, required=True, help="How could someone be harmed")

    location = fields.Selection(selection=[('office', 'Office'), ('store', 'Store'), ('workshop', 'Workshop'),
                                           ('yard', 'Yard'), ('travelling_to_site', 'Travelling To Site'),
                                           ('on_site', 'On Site'), ('travelling_to_work', 'Travelling to Work'), ],
                                string="Workplace / Location", required=True)

    consequence = fields.Selection(
        selection=[('insignificant', 'Insignificant'), ('minor', 'Minor'), ('moderate', 'Moderate'),
                   ('major', 'Major or Significant'), ('catastrophic', 'Catastrophic'), ],
        string="Consequence", required=False)
    likelihood = fields.Selection(selection=[('rare', 'Rare'), ('unlikely', 'Unlikely'), ('possible', 'Possible'),
                                             ('likely', 'Likely'), ('almost_certain', 'Almost Certain'), ],
                                  string="Likelihood", required=False)

    risk_matrix = fields.Selection(
        selection=[('low', 'Low'),
                   ('moderate', 'Moderate'),
                   ('high', 'High'),
                   ('critical', 'Critical'),
                   ('unacceptable', 'Unacceptable')
                   ],
        string="Risk Matrix", required=True)

    controls = fields.Selection(
        selection=[('eliminate', 'Eliminate'), ('isolate', 'Isolate'), ('minimise', 'Minimise'), ],
        string="Controls",
        help="Eliminate: get rid of, don't do it, replace. Isolate: time, distance, shielding. "
             "Minimise: Safe/standard operating procedures, PPE, signage, training",
        required=True)

    control_measure = fields.Char(string="Preventative Control Measure", size=128, required=True,
                                  help="Preventative measures")

    recovery_measure = fields.Char(string="Recovery Control Measure", size=128, required=True,
                                   help="Recovery control measures")

    further_action = fields.Text(string="Further Action", required=True,
                                 help="From Accident Investigation - prevention: "
                                      "person responsible, target completion date")

    notes = fields.Text(string="Review Notes", required=True, help="Any notes")
    review_date = fields.Date(string="Review Date", required=True)

    company_id = fields.Many2one("res.company", string="Company",
                                 default=lambda self: self.env['res.users'].company_id.id)

    residual_risk_assessment = fields.Selection([('low', 'Low'),
                                                 ('moderate', 'Moderate'),
                                                 ('high', 'High'),
                                                 ('critical', 'Critical')
                                                 ],
                                                string="Residual Risk Assessment")

    @api.onchange('consequence', 'likelihood')
    def onchange_likelihood(self):
        risk_matrix = None

        if not self.consequence and not self.likelihood:
            return
        if self.consequence == 'insignificant':
            if self.likelihood in ('rare', 'unlikely', 'possible'):
                risk_matrix = 'low'
            else:
                risk_matrix = 'moderate'
        elif self.consequence == 'minor':
            if self.likelihood == 'rare':
                risk_matrix = 'low'
            else:
                risk_matrix = 'moderate'
        elif self.consequence == 'moderate':
            if self.likelihood == 'rare':
                risk_matrix = 'low'
            elif self.likelihood in ('unlikely', 'possible', 'likely'):
                risk_matrix = 'moderate'
            else:
                risk_matrix = 'unacceptable'
        elif self.consequence == 'major':
            if self.likelihood in ('unlikely', 'possible', 'rare'):
                risk_matrix = 'moderate'
            else:
                risk_matrix = 'unacceptable'
        elif self.consequence == 'catastrophic':
            if self.likelihood in ('unlikely', 'rare'):
                risk_matrix = 'moderate'
            else:
                risk_matrix = 'unacceptable'

        return {'value': {'risk_matrix': risk_matrix}}

    @api.model
    def get_hazard_report(self):
        """
        Return the the report to use.

        This can be overidden to provide customised reports.
        :return: ir.actions.report record
        """
        return self.env.ref("hr_hazard.hazard_risk_register_report")
