# -*- coding: utf-8 -*-

from odoo import models, fields, api



class ProductType(models.Model):
    _name = 'product.type'

    name = fields.Char()
    description = fields.Char()
