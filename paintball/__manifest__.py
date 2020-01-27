# -*- coding: utf-8 -*-
{
    'name': "Paintball",

    'summary': "Paintball park management",



    'author': "Antonio Fregoso",
    'website': "https://antoniofregoso.com",
    'category': 'Paintball',
    'version': '13.0.0.0.0',
    'depends': ['sale_stock', 'point_of_sale'],
    'license': 'AGPL-3',
    

    'data': [
        'security/paintball_security.xml',
        'security/ir.model.access.csv',
        'views/paintball_views.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],
}
