from odoo import fields, models


class HrAccidentEmploymentPeriod(models.Model):
    _name = "hr.accident.employment.period"
    _description = "Employment Period"

    ###########################################################################
    # Fields
    ###########################################################################

    sequence = fields.Integer(string='Sequence', help="Sequence for order in view")
    name = fields.Char(string="Name", size=256, required=True, help="Name of the Period of Employment.")
    active = fields.Boolean(string="Active", help="Indicates whether the Period of Employment is active or not.",
                            default=True)

    _order = 'sequence'


class HrAccidentInjuryTreatment(models.Model):
    _name = "hr.accident.injury.treatment"
    _description = "Injury Treatment"

    ###########################################################################
    # Fields
    ###########################################################################

    sequence = fields.Integer(string='Sequence', help="Sequence for order in view")
    name = fields.Char(string="Name", size=256, required=True, help="Name of the Treatment of Injury.")
    active = fields.Boolean(string="Active", help="Indicates whether the Treatment of Injury is active or not.",
                            default=True)

    _order = 'sequence'


class HrIncidentType(models.Model):
    _name = "hr.incident.type"
    _description = "Incident Type"

    ###########################################################################
    # Fields
    ###########################################################################

    sequence = fields.Integer(string='Sequence', help="Sequence for order in view")
    name = fields.Char(string="Name", size=256, required=True, help="Name of the Incident Type.")
    active = fields.Boolean(string="Active", help="Indicates whether the Type is active or not.",
                            default=True)

    _order = 'sequence'


class HrAccidentEventMechanism(models.Model):
    _name = "hr.accident.event.mechanism"
    _description = "Event Mechanism"

    ###########################################################################
    # Fields
    ###########################################################################

    sequence = fields.Integer(string="Sequence", help="Sequence for order in view")
    name = fields.Char(string="Name", size=256, required=True, help="Name of the Mechanism of Event.")
    active = fields.Boolean(string="Active", help="Indicates whether the Mechanism of Event is active or not.",
                            default=True)

    _order = 'sequence'


class HrAccidentEventAgency(models.Model):
    _name = "hr.accident.event.agency"
    _description = "Event Agency"

    ###########################################################################
    # Fields
    ###########################################################################

    sequence = fields.Integer(string="Sequence", help="Sequence for order in view")
    name = fields.Char(string="Name", size=256, required=True, help="Name of the Agency of Event.")
    active = fields.Boolean(string="Active", help="Indicates whether the Agency of Event is active or not.",
                            default=True)

    _order = 'sequence'


class HrAccidentBodyPart(models.Model):
    _name = "hr.accident.body.part"
    _description = "Body Part"

    ###########################################################################
    # Fields
    ###########################################################################

    sequence = fields.Integer(string="Sequence", help="Sequence for order in view")
    name = fields.Char(string="Name", size=256, required=True, help="Name of the Body Part.")
    active = fields.Boolean(string="Active", help="Indicates whether the Body Part is active or not.",
                            default=True)

    _order = 'sequence'


class HrAccidentNature(models.Model):
    _name = "hr.accident.nature"
    _description = "Nature of Injury or Disease"

    ###########################################################################
    # Fields
    ###########################################################################

    sequence = fields.Integer(string="Sequence", help="Sequence for order in view")
    name = fields.Char(string="Name", size=256, required=True, help="Name of the Nature of Injury or Disease.")
    active = fields.Boolean(string="Active",
                            help="Indicates whether the Nature of Injury or Disease is active or not.", default=True)

    _order = 'sequence'


class HrAccidentAccident(models.Model):
    _name = "hr.accident.accident"
    _description = "Accident"

    ###########################################################################
    # Fields
    ###########################################################################

    create_date = fields.Datetime(string="Date Created", readonly=True)
    name = fields.Char(string="Reference", size=32, required=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('hr.accident.accident'))
    location = fields.Text(string="Location of accident", required=True,
                           help="shop, shed, unit nos., floor, building, street nos., and names, locality/suburb, or details of vehicle, ship or aircraft.")
    injured_person = fields.Char(string="Injured/Affected Person", size=256, required=True,
                                 help="Name of the Injured/Affected Person.")
    residential_address = fields.Text(string="Residential Address", required=True)
    birth_date = fields.Date(string="Date of Birth", required=True)
    sex = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string="Sex", required=True,
                           help="Sex of Injured Person.")
    occupation = fields.Char(string="Occupation", size=256,
                             help="Occupation or job title of injured person (employees and self-employed persons only).")
    relationship = fields.Selection(selection=[('employee', 'Employee'), ('self', 'Self'),
                                               ('contractor', 'Contractor'), ('other', 'Other')],
                                    string="Relationship to injured", required=True)
    hr_accident_employment_period_id = fields.Many2one("hr.accident.employment.period",

                                                       string="Period of employment", required=True,
                                                       help="Employees only.")
    hr_accident_injury_treatment_id = fields.Many2one("hr.accident.injury.treatment",
                                                      string="Treatment of injury", required=True)
    hr_incident_type_id = fields.Many2one("hr.incident.type", string="Incident Type", required=True)
    event_datetime = fields.Datetime(string="Time/date of Event", required=True)
    shift = fields.Selection(selection=[('day', 'Day'),
                                        ('afternoon', 'Afternoon'),
                                        ('night', 'Night')],
                             string="Shift", required=True)
    hours_worked = fields.Float(string="Hours worked since arrival at work",
                                help="Employees and self-employed persons only.")
    hr_accident_event_mechanism_id = fields.Many2one("hr.accident.event.mechanism",
                                                     string="Mechanism of Event", required=True)
    hr_accident_event_agency_id = fields.Many2one("hr.accident.event.agency",
                                                  string="Agency of Event", required=True)
    hr_accident_body_part_id = fields.Many2one("hr.accident.body.part", string="Body Part", required=True)
    hr_accident_nature_ids = fields.Many2many("hr.accident.nature",
                                              relation="hr_accident_nature_rel",
                                              string="Nature of injury or disease",
                                              required=True, help="Specify all.")
    description = fields.Text(string="Description of Event", required=True,
                              help="Where and how did the accident / serious harm happen?")
    work_zone = fields.Selection(selection=[('depot', 'Depot'), ('site', 'Site'),
                                            ('road', 'Road'), ('other', 'Other')], string="Work Zone")
    investigated = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No')],
                                    string="Investigation carried out", help="If notification is from an employer.")
    action_reqd = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No')],
                                   string="Action Required", help="Was action required after investigation.")
    lost_time_injury = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No')],
                                        string="Lost Time Injury", help="Lost Time with Injury.")
    lost_time = fields.Float(string="Lost Time (days off work)", help="Enter in days in 0.5d intervals.")
    hazard = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No')],
                              string="Significant hazard involved", help="If notification is from an employer.")
    environment_damage = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No')],
                                          string="Environmental Damage", help="Damage or pollution.")
    partner = fields.Char(string="Partner", size=256, help="Customer or supplier.")
    address = fields.Text(string="Address")
    manager = fields.Text(string="Manager")
    date = fields.Date(string="Finalised Date", required=False)
    company_id = fields.Many2one("res.company", string="Company",
                                 default=lambda self: self.env['res.users'].company_id.id)
    state = fields.Selection(selection=[('open', 'Open'),
                                        ('done', 'Done'),
                                        ('deleted', 'Deleted')],
                             string="State", required=True, readonly=True, help="State of accident report.",
                             default=lambda *args: 'open')
    hr_hazard_id = fields.Many2one('hr.hazard', string="Hazard")

    # Analysis and Investigation
    analysis = fields.Text(string='Analysis', help='What were the causes of the accident?')

    seriousness = fields.Selection(selection=[("minor", "Minor"),
                                              ("serious", "Serious"),
                                              ("Very Serious", "very")],
                                   string='How serious could it have been?',
                                   help='How serious could it have been.')

    future_probability = fields.Selection(selection=[("not often", "Not often"),
                                                     ("occasionally", "Occasionally"),
                                                     ("often", "Often")],
                                          string='How often is it likely to happen again?',
                                          help='How often is this likely to happen again.')

    actioned_state = fields.Selection(selection=[("running", "In progress"),
                                                 ("done", "Complete")],
                                      string='Investigation Status',
                                      default='running')

    worksafe_advised = fields.Selection(selection=[('yes', 'Yes'),
                                                   ('no', 'No')],
                                        string='Worksafe Advised')

    corrective_action_ids = fields.One2many('hr.accident.corrective.action',
                                            inverse_name='accident_id',
                                            string='What action has or will be taken to prevent a recurrence?',
                                            help='What action has or will be taken to prevent recurrence?')

    actioned_person = fields.Char(string='By Whom')
    actioned_date = fields.Date(string='By When')
    treatment_description = fields.Text(string='Description of treatment provided')
    medical_entity = fields.Char(string='Doctor/Hospital')
    assisting_attendee = fields.Char(string='Name of person giving first aid', help='Name of person giving first aid.')
    first_aid_items = fields.Text(string='First Aid items used ')
    internal_investigator = fields.Many2one('hr.employee', string='Investigation by(internal)')
    investigation_date = fields.Date(string='Date')

    _order = 'event_datetime desc, id desc'

    def unlink(self):
        for accident in self:
            accident.write({'state': 'deleted'})

        return True

    def mark_incident_done(self):
        for accident in self:
            accident.write({'state': 'done'})

    def mark_incident_open(self):
        for accident in self:
            accident.write({'state': 'open'})
