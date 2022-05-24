# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _
 
class payment_method(models.Model):
     
    _name = 'payment.method'
    _rec_name = 'title'

    qbooks_id = fields.Char(string="Quickbooks ID" ,readonly=True)
    title = fields.Char(string="Name", required=True)
    # descrp = fields.Text(string="Description")
    payment_type = fields.Selection([('CREDIT_CARD', 'CREDIT CARD'), ('NON_CREDIT_CARD', 'NON CREDIT CARD')], string='Payment Type', required=True)
    to_be_exported = fields.Boolean(string="To be exported?")