# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round


class StockReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    variant_package_id = fields.Many2one('variant.package', 'Package')
    qty = fields.Float(string='Quantity')

    # @api.onchange('qty')
    # def _onchange_qty_done(self):
    #     if self.variant_package_id:
    #         self.quantity = self.qty * self.variant_package_id.qty
    #     else:
    #         self.quantity = self.qty


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    # @api.model
    # def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
    #     quantity = stock_move.product_qty
    #     for move in stock_move.move_dest_ids:
    #         if move.origin_returned_move_id and move.origin_returned_move_id != stock_move:
    #             continue
    #         if move.state in ('partially_available', 'assigned'):
    #             quantity -= sum(move.move_line_ids.mapped('product_qty'))
    #         elif move.state in ('done'):
    #             quantity -= move.product_qty
    #     quantity = float_round(quantity, precision_rounding=stock_move.product_id.uom_id.rounding)
    #     return {
    #         'product_id': stock_move.product_id.id,
    #         'quantity': quantity,
    #         'variant_package_id': stock_move.variant_package_id.id,
    #         'qty': stock_move.qty,
    #         'move_id': stock_move.id,
    #         'uom_id': stock_move.product_id.uom_id.id,
    #     }
    #
    # def _prepare_move_default_values(self, return_line, new_picking):
    #     vals = {
    #         'product_id': return_line.product_id.id,
    #         'product_uom_qty': return_line.quantity,
    #         'product_uom': return_line.product_id.uom_id.id,
    #         'variant_package_id': return_line.variant_package_id.id,
    #         'qty': return_line.qty,
    #         'package_qty_done': 0,
    #         'picking_id': new_picking.id,
    #         'state': 'draft',
    #         'date': fields.Datetime.now(),
    #         'location_id': return_line.move_id.location_dest_id.id,
    #         'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
    #         'picking_type_id': new_picking.picking_type_id.id,
    #         'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
    #         'origin_returned_move_id': return_line.move_id.id,
    #         'procure_method': 'make_to_stock',
    #     }
    #     return vals
