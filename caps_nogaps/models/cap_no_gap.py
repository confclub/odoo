# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import xlrd


class CapNoGap(models.Model):

    _name = 'cap.no.gap'

    product_id = fields.Many2one("product.product")
    package_id = fields.Many2one("variant.package")
    name = fields.Char(related='product_id.name')
    pcs_per_day = fields.Float()
    pcs_per_bag = fields.Integer()
    bags_per_carton = fields.Integer()
    pcs_per_carton = fields.Integer()