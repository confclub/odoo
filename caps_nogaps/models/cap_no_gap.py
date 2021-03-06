# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import xlrd


class CapNoGap(models.Model):

    _name = 'cap.no.gap'

    name = fields.Char(related='product_id.name')
    product_id = fields.Many2one("product.product")
    product_carton_id = fields.Many2one("product.product")
    # package_id = fields.Many2one("variant.package")
    daily_pack = fields.Char()
    daily_pack_sku = fields.Char()
    pcs_per_day = fields.Float()
    pcs_per_bag = fields.Integer()
    bags_per_carton = fields.Integer()
    pcs_per_carton = fields.Integer()