# -*- coding: utf-8 -*-
# from odoo import http


# class ExcelReport(http.Controller):
#     @http.route('/excel_report/excel_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/excel_report/excel_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('excel_report.listing', {
#             'root': '/excel_report/excel_report',
#             'objects': http.request.env['excel_report.excel_report'].search([]),
#         })

#     @http.route('/excel_report/excel_report/objects/<model("excel_report.excel_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('excel_report.object', {
#             'object': obj
#         })
