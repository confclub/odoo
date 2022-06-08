# -*- coding: utf-8 -*-

from odoo import models, fields, api


class VariantPackage(models.Model):
    _name = 'variant.package'
    _rec_name = 'code'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code/Sku')
    price = fields.Float(string='price')
    qty = fields.Float(string='Quantity')
    company_id = fields.Many2one('res.company', 'Company')
    value_name = fields.Char()
    qb_variant_id = fields.Char()
    product_id = fields.Many2one('product.product', 'Product')
    inventory_item_id = fields.Char()
    shopify_variant_id = fields.Char()
