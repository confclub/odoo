# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _
from odoo.osv import expression


class product_template(models.Model):
    _inherit = 'product.template'

    qbooks_id = fields.Char('Quickbooks ID', readonly=True)
    to_be_exported = fields.Boolean(string="To be exported?")


# class product_images(models.Model):
#     _inherit ='product.images'

#     product_t_id=fields.Many2one('product.template','Product Images')
#     # product_v_id = fields.Many2one('product.product', 'Product Images')
#     image_url=fields.Char('Image URL')
#     image=fields.Binary('Image')
#     woocom_img_id=fields.Integer('Img ID')
#     shop_ids = fields.Many2many('sale.shop', 'img_shop_rel', 'img_id', 'shop_id', string="Shop")
#     write_date = fields.Datetime(string="Write Date")
