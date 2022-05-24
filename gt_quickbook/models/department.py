# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _
 
# class depatrment(models.Model):
     
#     _name = 'department'

#     qbooks_id = fields.Char(string="Quickbooks ID" ,readonly=True)
#     dept_name = fields.Char(string="Name")
#     sub_department = fields.Boolean(string="Is Sub Department" ,readonly=True)

class HR_Depatrment(models.Model):
     
    _inherit = 'hr.department'

    qbook_id = fields.Char(string="Quickbooks ID" ,readonly=True)
    sub_department = fields.Boolean(string="Is Sub Department" ,readonly=True)
    to_be_exported = fields.Boolean(string="To be exported?")
    