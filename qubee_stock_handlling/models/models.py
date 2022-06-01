# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class qubee_stock_handlling(models.Model):
#     _name = 'qubee_stock_handlling.qubee_stock_handlling'
#     _description = 'qubee_stock_handlling.qubee_stock_handlling'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
