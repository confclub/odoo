# -*- coding: utf-8 -*-
# from odoo import http


# class WebsiteCustomization(http.Controller):
#     @http.route('/website_customization/website_customization/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/website_customization/website_customization/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('website_customization.listing', {
#             'root': '/website_customization/website_customization',
#             'objects': http.request.env['website_customization.website_customization'].search([]),
#         })

#     @http.route('/website_customization/website_customization/objects/<model("website_customization.website_customization"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('website_customization.object', {
#             'object': obj
#         })
