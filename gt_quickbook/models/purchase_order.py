# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _

class purchase_order(models.Model):
    _inherit = "purchase.order"

    qbook_id =  fields.Char('Quickbooks ID', readonly=True)

    addr_l1 =  fields.Char('Line1', readonly=True)
    addr_l2 =  fields.Char('Line2', readonly=True)
    addr_l3 =  fields.Char('Line3', readonly=True)
    addr_l4 =  fields.Char('Line4', readonly=True)
    to_be_exported = fields.Boolean(string="To be exported?")


class purchase_order_line(models.Model):
    _inherit='purchase.order.line'
    
    qbook_id = fields.Char(string="Quickbooks ID", readonly=True)
    line_customer = fields.Many2one('res.partner','Line Customer')
