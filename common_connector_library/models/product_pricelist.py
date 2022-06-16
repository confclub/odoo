# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    price_check_box = fields.Boolean(default=False)
    pack_ids = fields.One2many('product.pricelist.pack.item', 'pricelist_id')

    def create(self, vals):
        if vals.get('price_check_box'):
            price_list = self.env['product.pricelist'].search([('price_check_box', '=', True)])
            if len(price_list):
                raise ValidationError("sorry you cant")
        return super(ProductPricelist, self).create(vals)

    def write(self, vals):
        if vals.get('price_check_box'):
            price_list = self.env['product.pricelist'].search([('price_check_box', '=', True)])
            if len(price_list):
                raise ValidationError("sorry you cant")
        return super(ProductPricelist, self).write(vals)




    def get_product_price_ept(self, product, partner=False):
        """
        Gives price of a product from pricelist(self).
        :param product: product id
        :param partner: partner id or False
        :return: price
        Migration done by twinkalc August 2020
        """
        price = self.get_product_price(product, 1.0, partner=partner, uom_id=product.uom_id.id)
        return price

    def set_product_price_ept(self, product_id, price, min_qty=1):
        """
        Creates or updates price for product in Pricelist.
        :param product_id: Id of product.
        :param price: Price
        :param min_qty: qty
        :return: product_pricelist_item
        Migration done by twinkalc August 2020
        """
        product_pricelist_item_obj = self.env['product.pricelist.item']
        domain = [('pricelist_id', '=', self.id), ('product_id', '=', product_id), ('min_quantity', '=', min_qty)]

        product_pricelist_item = product_pricelist_item_obj.search(domain)

        if product_pricelist_item:
            product_pricelist_item.write({'fixed_price': price})
        else:
            vals = {
                'pricelist_id': self.id,
                'applied_on': '0_product_variant',
                'product_id': product_id,
                'min_quantity': min_qty,
                'fixed_price': price,
            }
            new_record = product_pricelist_item_obj.new(vals)
            new_record._onchange_product_id()
            new_vals = product_pricelist_item_obj._convert_to_write(
                {name: new_record[name] for name in new_record._cache})
            product_pricelist_item = product_pricelist_item_obj.create(new_vals)
        return product_pricelist_item


class ProductPricelistPackItem(models.Model):
    _name = "product.pricelist.pack.item"


    product_id = fields.Many2one(
        'product.product', 'Product')
    variant_package_ids = fields.One2many(related='product_id.variant_package_ids')  # for domain purpose only
    package_id = fields.Many2one('variant.package', 'Package', domain="[('id', 'in', variant_package_ids)]")
    min_quantity = fields.Float(
        'Min. Quantity', default=0)
    fixed_price = fields.Float(default=0)
    pricelist_id = fields.Many2one('product.pricelist')
    date_start = fields.Datetime('Start Date', help="Starting datetime for the pricelist item validation\n"
                                                    "The displayed value depends on the timezone set in your preferences.")
    date_end = fields.Datetime('End Date', help="Ending datetime for the pricelist item validation\n"
                                                "The displayed value depends on the timezone set in your preferences.")




