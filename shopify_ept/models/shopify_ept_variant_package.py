# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShopifyVariantPackage(models.Model):
    _name = 'shopify.variant.package'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code/Sku')
    price = fields.Float(string='price')
    qty = fields.Float(string='Quantity')
    company_id = fields.Many2one('res.company', 'Company')
    shopify_product_id = fields.Many2one('shopify.product.product.ept', 'Shopify Product')
