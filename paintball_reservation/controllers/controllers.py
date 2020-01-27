# -*- coding: utf-8 -*-
# from odoo import http


# class PaintballReservation(http.Controller):
#     @http.route('/paintball_reservation/paintball_reservation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/paintball_reservation/paintball_reservation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('paintball_reservation.listing', {
#             'root': '/paintball_reservation/paintball_reservation',
#             'objects': http.request.env['paintball_reservation.paintball_reservation'].search([]),
#         })

#     @http.route('/paintball_reservation/paintball_reservation/objects/<model("paintball_reservation.paintball_reservation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('paintball_reservation.object', {
#             'object': obj
#         })
