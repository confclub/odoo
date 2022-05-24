# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import api, fields, models, _

class Account_Invoice(models.Model):
    _inherit = "account.move"

    qbook_id =  fields.Char('Quickbooks ID', readonly=True)
    # invoice_no = fields.Char('Invoice No', readonly=True)
    qbook_id_vendor =  fields.Char('Quickbooks ID', readonly=True)
    to_be_exported = fields.Boolean(string="To be exported?")


class Account_Invoice_Line(models.Model):
    _inherit='account.move.line'
    
    qbook_id = fields.Char(string="Quickbooks ID", readonly=True)
    line_customer = fields.Many2one('res.partner', string='Line Customer')
    is_billable = fields.Boolean('Billable', readonly=True)


class Account_Payment(models.Model):
    _inherit = "account.payment"

    qbook_id = fields.Char(string="Quickbooks ID", readonly=True)

    qbook_id_vendor =  fields.Char('Quickbooks ID', readonly=True)

    # journal_id = fields.Many2one('account.journal', string='Payment Journal', domain=[('type', 'in', ('bank', 'cash','Check','CreditCard'))])


# class AccountJournal(models.Model):
#     _inherit = "account.journal"

#     qbook_id = fields.Char(string="Quickbooks ID", readonly=True)

#     type = fields.Selection([
#             ('sale', 'Sale'),
#             ('purchase', 'Purchase'),
#             ('cash', 'Cash'),
#             ('bank', 'Bank'),
#             ('general', 'Miscellaneous'),
#             ('Check', 'Check'),
#             ('CreditCard', 'CreditCard'),
#         ], required=True,
#         help="Select 'Sale' for customer invoices journals.\n"\
#         "Select 'Purchase' for vendor bills journals.\n"\
#         "Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments.\n"\
#         "Select 'General' for miscellaneous operations journals.")