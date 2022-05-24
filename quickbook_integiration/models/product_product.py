# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductInherit(models.Model):
    _inherit = 'product.product'

    # varient_name = fields.Char()
    # varient_description = fields.Text()
    qb_varient_id = fields.Char()
    # weight_value = fields.Char()
    # labels
    # option1_label = fields.Char()
    # option2_label = fields.Char()
    # option3_label = fields.Char()

    # values
    # option1_value = fields.Char()
    # option2_value = fields.Char()
    # option3_value = fields.Char()

    # buy_price = fields.Float()
    # wholesale_price = fields.Float()
    # retail_price = fields.Float()


