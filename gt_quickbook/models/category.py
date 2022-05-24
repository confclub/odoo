# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _
 
class ProductCategory(models.Model):
     
    _inherit = 'product.category'

    qbook_id = fields.Char(string="Quickbooks ID" ,readonly=True)
    # dept_name = fields.Char(string="Name")
    # sub_department = fields.Boolean(string="Is Sub Department" ,readonly=True)
    shop_ids = fields.Many2many('quickbook.integration', 'qbook_category_shop_rel', 'categ_id', 'shop_id', string="Shop")
    to_be_exported = fields.Boolean(string="To be exported?")