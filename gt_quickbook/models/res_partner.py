# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _

class res_partner(models.Model):
    _inherit = "res.partner"
                
   
    qbook_id = fields.Char('Quickbooks ID',readonly=True)

    is_taxable = fields.Boolean(string="Is a Taxable Customer")
    print_on_check_name = fields.Char('Print On Check Name')
    preferred_delivery_method = fields.Selection([('Print','Print Later'),('Email', 'Send Later'),('None', 'None')],string='Preferred Delivery Method')
    balance = fields.Char(string='Balance')
    balance_job = fields.Char(string='Balance with Job')

    vendor1099  = fields.Boolean(string="Is a vendor1099", placeholder= "This vendor is an independent contractor; someone who is given a 1099-MISC form at the end of the year. A 1099 vendor is paid with regular checks, and taxes are not withheld on their behalf.")
    acc_num  = fields.Char(string='Account Number')

    to_be_exported = fields.Boolean(string="To be exported?")

