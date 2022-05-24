# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _
 
class AccountAccount(models.Model):
    _inherit = "account.account"

    qbooks_id = fields.Char(string="Quickbooks ID" ,readonly=True)
    to_be_exported = fields.Boolean(string="To be exported?")
    # sub_department = fields.Boolean(string="Is Sub Department" ,readonly=True)


class AccountTax(models.Model):
    _inherit = "account.tax"

    qbook_id = fields.Char(string="Quickbooks ID" ,readonly=True)
    # sub_department = fields.Boolean(string="Is Sub Department" ,readonly=True)
    account_agency = fields.Many2one('account.agency',string="Agency")
    to_be_exported = fields.Boolean(string="To be exported?")

class AccountAgency(models.Model):
    _name = "account.agency"

    name = fields.Char(string="Agency Name" ,readonly=True)
    qbook_id = fields.Char(string="Quickbooks ID" ,readonly=True)
    