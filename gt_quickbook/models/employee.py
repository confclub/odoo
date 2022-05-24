# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _

class HR_Employee(models.Model):
    _inherit = "hr.employee"
                
   
    qbook_id = fields.Char('Quickbooks ID',readonly=True)
    print_on_check_name = fields.Char('Print On Check Name')
    to_be_exported = fields.Boolean(string="To be exported?")
