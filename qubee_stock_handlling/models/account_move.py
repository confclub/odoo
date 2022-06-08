# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from itertools import groupby


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    variant_package_id = fields.Many2one('variant.package', 'Package')