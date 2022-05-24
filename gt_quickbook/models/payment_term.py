# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _


class AccountPaymentTerm(models.Model):
	_inherit = 'account.payment.term'

	qbooks_id = fields.Char(string="Quickbooks ID" ,readonly=True)
	payment_term_type = fields.Selection([('STANDARD','STANDARD'), ('DATE_DRIVEN','DATE DRIVEN')], string='Payment Term')

	
 
# class payment_method(models.Model):
     
#     _name = 'payment.term'

#     qbooks_id = fields.Char(string="Quickbooks ID" ,readonly=True)
#     term_name = fields.Char(string="Name")
#     payment_term_type = delivery_type = fields.Selection([('STANDARD','STANDARD'), ('DATE_DRIVEN','DATE DRIVEN')], string='Payment Term')

