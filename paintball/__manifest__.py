# -*- coding: utf-8 -*-
{
    'name': "Paintball",

    'summary': "Paintball park management",



    'author': "Antonio Fregoso",
    'website': "https://antoniofregoso.com",
    'category': 'Paintball',
    'version': '13.0.0.0.0',
    'depends': ['sale_stock'],
    'license': 'AGPL-3',
    

    'data': [
        'security/paintball_security.xml',
        'security/ir.model.access.csv',
        'views/paintball_views.xml',
        'data/paintball_sequence.xml',
        'report/paintball_report_templates.xml',
        'report/paintball_report.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
