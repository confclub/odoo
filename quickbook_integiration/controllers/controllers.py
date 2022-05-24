# -*- coding: utf-8 -*-
# from odoo import http


# class QuickbookIntegiration(http.Controller):
#     @http.route('/quickbook_integiration/quickbook_integiration/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/quickbook_integiration/quickbook_integiration/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('quickbook_integiration.listing', {
#             'root': '/quickbook_integiration/quickbook_integiration',
#             'objects': http.request.env['quickbook_integiration.quickbook_integiration'].search([]),
#         })

#     @http.route('/quickbook_integiration/quickbook_integiration/objects/<model("quickbook_integiration.quickbook_integiration"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('quickbook_integiration.object', {
#             'object': obj
#         })
