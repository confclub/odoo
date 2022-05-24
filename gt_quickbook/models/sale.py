# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _

class sale_order(models.Model):
    _inherit = "sale.order"

    qbook_id =  fields.Char('Quickbooks ID', readonly=True)
    payment_method = fields.Many2one('payment.method','Payment Method')
    to_be_exported = fields.Boolean(string="To be exported?")
                                   
    # shop_id=fields.Many2one('sale.shop','Shop ID')
    # order_status = fields.Selection([('pending','Pending payment'),('processing','Processing'),('on-hold','On hold'),('completed','Completed'),('cancelled','Cancelled'),('refunded','Refunded'),('failed','Failed')], string="Status")
    # payment_mode=fields.Many2one('payment.gatway',string='Payment mode')
    # carrier=fields.Many2one('delivery.carrier',string='Carrier In Woocommerce')
    # qbook_order=fields.Boolean('Qbook Order')
    
    

class sale_order_line(models.Model):
    _inherit='sale.order.line'
    
    qbook_id = fields.Char(string="Quickbooks ID", readonly=True)
