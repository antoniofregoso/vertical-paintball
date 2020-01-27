# -*- coding: utf-8 -*-
# from odoo import http


# class PaintballRestaurant(http.Controller):
#     @http.route('/paintball_restaurant/paintball_restaurant/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/paintball_restaurant/paintball_restaurant/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('paintball_restaurant.listing', {
#             'root': '/paintball_restaurant/paintball_restaurant',
#             'objects': http.request.env['paintball_restaurant.paintball_restaurant'].search([]),
#         })

#     @http.route('/paintball_restaurant/paintball_restaurant/objects/<model("paintball_restaurant.paintball_restaurant"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('paintball_restaurant.object', {
#             'object': obj
#         })
