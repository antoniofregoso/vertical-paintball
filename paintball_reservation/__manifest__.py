# -*- coding: utf-8 -*-
{
    'name': "Paintball Reservation",

    'summary': "",

    'author': "Antonio Fregoso",
    'website': "https://antoniofregoso.com",
    'version': '13.0.0.0.0',
    'depends': ['paintball'],
    'data': [
        'security/ir.model.access.csv',
        'views/paintball_reservation_views.xml',
        'views/assets.xml',
        'data/email_template_view.xml',
        'data/paintball_reservation_data.xml',
        'data/paintball_reservation_sequence.xml',
        'data/paintball_scheduler.xml',
        'report/checkin_report_template.xml',
        'report/checkout_report_template.xml',
        'report/paintball_reservation_report_template.xml',
        'report/report_view.xml',
        'report/zone_max_report_template.xml',
        'wizard/paintball_reservation_wizard.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
