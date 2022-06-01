# -*- coding: utf-8 -*-
# from odoo import http


# class QubeeStockHandlling(http.Controller):
#     @http.route('/qubee_stock_handlling/qubee_stock_handlling', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/qubee_stock_handlling/qubee_stock_handlling/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('qubee_stock_handlling.listing', {
#             'root': '/qubee_stock_handlling/qubee_stock_handlling',
#             'objects': http.request.env['qubee_stock_handlling.qubee_stock_handlling'].search([]),
#         })

#     @http.route('/qubee_stock_handlling/qubee_stock_handlling/objects/<model("qubee_stock_handlling.qubee_stock_handlling"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('qubee_stock_handlling.object', {
#             'object': obj
#         })
