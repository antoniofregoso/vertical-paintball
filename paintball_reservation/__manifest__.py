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
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
