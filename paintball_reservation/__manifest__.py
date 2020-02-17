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
        'data/paintball_scheduler.xml',
        'data/paintball_reservation_sequence.xml',
        'views/paintball_reservation_views.xml',
        'data/email_template_view.xml',
        'report/checkin_report_template.xml',
        'report/checkout_report_template.xml',
        'report/zone_max_report_template.xml',
        'report/paintball_reservation_report_template.xml',
        'report/report_view.xml',
        #'data/paintball_reservation_data.xml',
        'views/assets.xml',
        #'wizards/paintball_reservation_wizard.xml',
        
    ],
    'qweb': [
        "static/src/xml/paintball_zone_summary.xml",
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
