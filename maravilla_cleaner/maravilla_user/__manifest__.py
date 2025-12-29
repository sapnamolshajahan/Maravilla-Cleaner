{
    'name': "maravilla_user",
    'summary': "Short (1 phrase/line) summary of the module's purpose",
    'description': """Long description of module's purpose""",
    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': [
        'base','project','hr','industry_fsm','web','website_sale',
        'sale','portal', 'hr_timesheet', 'account','hr_payroll'
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/project_task_security.xml',
        'security/employee_group.xml',
        'security/portal_timesheet_access.xml',
        'security/portal_projets.xml',
        'views/website_sale.xml',
        'views/fsm_task_view.xml',
        'views/project_task_view.xml',
        'views/task_timesheet.xml',
        'views/dashboard_template.xml'

    ],

    'assets': {
            'web.assets_frontend': [

                'maravilla_user/static/src/js/portal_timesheet.js',
                'maravilla_user/static/src/js/task_timer.js',
                'https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.css',
                'maravilla_user/static/src/css/dashboard.css',
                'https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.js',
                'maravilla_user/static/src/js/dashboard.js',
            ],
        },


    'demo': [
         'demo/demo.xml'
    ],
}

