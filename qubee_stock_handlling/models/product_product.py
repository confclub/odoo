# -*- coding: utf-8 -*-

from odoo import models, fields, api



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    temp_checkbox = fields.Boolean(default=False)
    shopify_product_type = fields.Many2one('product.type')


class Product(models.Model):
    _inherit = 'product.product'

    variant_package_ids = fields.One2many('variant.package', 'product_id')
    inventory_item_id = fields.Char()
    shopify_variant_id = fields.Char()
    product_not_found = fields.Boolean(default=False)






