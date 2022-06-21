# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrderInherit(models.Model):

    _inherit = "sale.order"

    from_excel = fields.Boolean(default=False)