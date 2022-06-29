# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from itertools import groupby


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
















class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    variant_package_ids = fields.One2many(related='product_id.variant_package_ids')
    variant_package_id = fields.Many2one('variant.package', 'Package', domain="[('id', 'in', variant_package_ids)]")
    qty = fields.Float(string='Qty')

    # @api.onchange('qty', 'variant_package_id')
    # def _onchange_qty(self):
    #     if self.variant_package_id:
    #         self.product_qty = self.qty * self.variant_package_id.qty
    #     else:
    #         self.product_qty = self.qty

    # @api.onchange('variant_package_id', 'product_id')
    # def _onchange_variant_package_id(self):
    #     if self.variant_package_id:
    #         self.price_unit = self.variant_package_id.price
    #     else:
    #         self.price_unit = self.product_id.lst_price


    def _prepare_compute_all_values(self):
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency_id': self.order_id.currency_id,
            'product_qty': self.qty, # quantity changed
            'product': self.product_id,
            'partner': self.order_id.partner_id,
        }




    # def _create_stock_moves(self, picking):
    #     res = super(PurchaseOrderLine, self)._create_stock_moves(picking)
    #
    #     for stock in res:
    #         for purchase_line in self:
    #             if stock.product_id == purchase_line.product_id:
    #                 stock['qty'] = purchase_line.qty
    #                 stock['variant_package_id'] = purchase_line.variant_package_id.id
    #     return res


    # def _prepare_account_move_line(self, move=False):
    #     res = super(PurchaseOrderLine, self)._prepare_account_move_line(move=False)
    #     res['quantity'] = self.qty
    #     res['variant_package_id'] = self.variant_package_id.id
    #     return res





