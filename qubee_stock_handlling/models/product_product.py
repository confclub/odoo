# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Product(models.Model):
    _inherit = 'product.product'

    variant_package_ids = fields.One2many('variant.package', 'product_id')
