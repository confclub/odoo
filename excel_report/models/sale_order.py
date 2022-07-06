# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrderInherit(models.Model):

    _inherit = "sale.order"

    from_excel = fields.Boolean(default=False)
    invoiced = fields.Boolean(default=False)
    delivery = fields.Boolean(default=False)
    after_live = fields.Boolean(default=False)
    error_in_order = fields.Boolean(default=False)