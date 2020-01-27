# -*- coding: utf-8 -*-
# from odoo import http


# class Paintball(http.Controller):
#     @http.route('/paintball/paintball/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/paintball/paintball/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('paintball.listing', {
#             'root': '/paintball/paintball',
#             'objects': http.request.env['paintball.paintball'].search([]),
#         })

#     @http.route('/paintball/paintball/objects/<model("paintball.paintball"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('paintball.object', {
#             'object': obj
#         })
