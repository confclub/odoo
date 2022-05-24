# -*- coding: utf-8 -*-
# from odoo import http


# class CapsNogaps(http.Controller):
#     @http.route('/caps_nogaps/caps_nogaps/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/caps_nogaps/caps_nogaps/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('caps_nogaps.listing', {
#             'root': '/caps_nogaps/caps_nogaps',
#             'objects': http.request.env['caps_nogaps.caps_nogaps'].search([]),
#         })

#     @http.route('/caps_nogaps/caps_nogaps/objects/<model("caps_nogaps.caps_nogaps"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('caps_nogaps.object', {
#             'object': obj
#         })
