# -*- coding: utf-8 -*-

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _stock_account_get_anglo_saxon_price_unit(self):
        price_unit = super(AccountMoveLine, self)._stock_account_get_anglo_saxon_price_unit()

        so_line = self.sale_line_ids and self.sale_line_ids[-1] or False
        if so_line:
            # bom = so_line.product_id.product_tmpl_id.bom_ids.filtered(lambda b: not b.company_id or b.company_id == so_line.company_id)[:1]
            bom = so_line.product_id.product_tmpl_id.bom_ids.filtered(lambda l: l.product_id.id == so_line.product_id.id)
            if not bom:
                price_unit = so_line.product_id.standard_price
        return price_unit

