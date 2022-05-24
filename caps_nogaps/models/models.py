# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class caps_nogaps(models.Model):
#     _name = 'caps_nogaps.caps_nogaps'
#     _description = 'caps_nogaps.caps_nogaps'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
