# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    employee_id = fields.Char()
    b2b = fields.Boolean()
    company_typeee = fields.Selection([('consumer', 'Consumer'), ('supplier', 'Supplier'), ('business', 'Business')])
    description = fields.Text()

