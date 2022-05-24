# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProdTemplateInherit(models.Model):
    _inherit = 'product.template'

    # qb_product_type = fields.Char()
    # supplier = fields.Char()
    # brand = fields.Char()
    qb_templ_id = fields.Char()

