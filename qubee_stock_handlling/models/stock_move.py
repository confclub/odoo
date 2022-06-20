# -*- coding: utf-8 -*-

from odoo import models, fields, api
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import OrderedSet
from ...shopify_ept import shopify

class StockMove(models.Model):
    _inherit = 'stock.move'

    variant_package_id = fields.Many2one('variant.package', 'Package')
    qty = fields.Float(string='Quantity')
    package_qty_done = fields.Float(string='Done')

    @api.onchange('package_qty_done')
    def _onchange_qty_done(self):
        if self.variant_package_id:
            self.quantity_done = self.package_qty_done * self.variant_package_id.qty
        else:
            self.quantity_done = self.package_qty_done

    # def _action_done(self, cancel_backorder=False):
    #     self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
    #     moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
    #     moves_ids_todo = OrderedSet()
    #
    #     # Cancel moves where necessary ; we should do it before creating the extra moves because
    #     # this operation could trigger a merge of moves.
    #     for move in moves:
    #         if move.quantity_done <= 0 and not move.inventory_id:
    #             if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
    #                 move._action_cancel()
    #
    #     # Create extra moves where necessary
    #     for move in moves:
    #         if move.state == 'cancel' or (move.quantity_done <= 0 and not move.inventory_id):
    #             continue
    #
    #         moves_ids_todo |= move._create_extra_move().ids
    #
    #     moves_todo = self.browse(moves_ids_todo)
    #     moves_todo._check_company()
    #     # Split moves where necessary and move quants
    #     backorder_moves_vals = []
    #     for move in moves_todo:
    #         # To know whether we need to create a backorder or not, round to the general product's
    #         # decimal precision and not the product's UOM.
    #         rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
    #             # Need to do some kind of conversion here
    #             qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
    #             new_move_vals = move._split(qty_split)
    #             backorder_moves_vals += new_move_vals
    #     backorder_moves = self.env['stock.move'].create(backorder_moves_vals)
    #     # The backorder moves are not yet in their own picking. We do not want to check entire packs for those
    #     # ones as it could messed up the result_package_id of the moves being currently validated
    #     backorder_moves.with_context(bypass_entire_pack=True)._action_confirm(merge=False)
    #     if cancel_backorder:
    #         backorder_moves.with_context(moves_todo=moves_todo)._action_cancel()
    #     moves_todo.mapped('move_line_ids').sorted()._action_done()
    #     # Check the consistency of the result packages; there should be an unique location across
    #     # the contained quants.
    #     for result_package in moves_todo\
    #             .mapped('move_line_ids.result_package_id')\
    #             .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
    #         if len(result_package.quant_ids.filtered(lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity), precision_rounding=q.product_uom_id.rounding)).mapped('location_id')) > 1:
    #             raise UserError(_('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
    #     picking = moves_todo.mapped('picking_id')
    #     moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})
    #
    #     new_push_moves = moves_todo.filtered(lambda m: m.picking_id.immediate_transfer)._push_apply()
    #     if new_push_moves:
    #         new_push_moves._action_confirm()
    #     move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
    #     for move_dest in moves_todo.move_dest_ids:
    #         move_dests_per_company[move_dest.company_id.id] |= move_dest
    #     for company_id, move_dests in move_dests_per_company.items():
    #         move_dests.sudo().with_company(company_id)._action_assign()
    #
    #     # We don't want to create back order for scrap moves
    #     # Replace by a kwarg in master
    #     if self.env.context.get('is_scrap'):
    #         return moves_todo
    #
    #     if picking and not cancel_backorder:
    #         backorder = picking._create_backorder()
    #         if any([m.state == 'assigned' for m in backorder.move_lines]):
    #            backorder._check_entire_pack()
    #     return moves_todo

    def _split(self, qty, restrict_partner_id=False):
        """ Splits `self` quantity and return values for a new moves to be created afterwards

        :param qty: float. quantity to split (given in product UoM)
        :param restrict_partner_id: optional partner that can be given in order to force the new move to restrict its choice of quants to the ones belonging to this partner.
        :returns: list of dict. stock move values """
        self.ensure_one()
        if self.state in ('done', 'cancel'):
            raise UserError(_('You cannot split a stock move that has been set to \'Done\'.'))
        elif self.state == 'draft':
            # we restrict the split of a draft move because if not confirmed yet, it may be replaced by several other moves in
            # case of phantom bom (with mrp module). And we don't want to deal with this complexity by copying the product that will explode.
            raise UserError(_('You cannot split a draft move. It needs to be confirmed first.'))
        if float_is_zero(qty, precision_rounding=self.product_id.uom_id.rounding) or self.product_qty <= qty:
            return []

        decimal_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # `qty` passed as argument is the quantity to backorder and is always expressed in the
        # quants UOM. If we're able to convert back and forth this quantity in the move's and the
        # quants UOM, the backordered move can keep the UOM of the move. Else, we'll create is in
        # the UOM of the quants.
        uom_qty = self.product_id.uom_id._compute_quantity(qty, self.product_uom, rounding_method='HALF-UP')
        if float_compare(qty, self.product_uom._compute_quantity(uom_qty, self.product_id.uom_id, rounding_method='HALF-UP'), precision_digits=decimal_precision) == 0:
            defaults = self._prepare_move_split_vals(uom_qty)
        else:
            defaults = self.with_context(force_split_uom_id=self.product_id.uom_id.id)._prepare_move_split_vals(qty)

        if restrict_partner_id:
            defaults['restrict_partner_id'] = restrict_partner_id

        # TDE CLEANME: remove context key + add as parameter
        if self.env.context.get('source_location_id'):
            defaults['location_id'] = self.env.context['source_location_id']
        new_move_vals = self.copy_data(defaults)

        # Update the original `product_qty` of the move. Use the general product's decimal
        # precision and not the move's UOM to handle case where the `quantity_done` is not
        # compatible with the move's UOM.
        new_product_qty = self.product_id.uom_id._compute_quantity(self.product_qty - qty, self.product_uom, round=False)
        new_product_qty = float_round(new_product_qty, precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure'))
        self.with_context(do_not_unreserve=True).write({'product_uom_qty': new_product_qty})
        return new_move_vals

    def _prepare_move_split_vals(self, qty):
        vals = {
            'package_qty_done': 0,
            'product_uom_qty': qty,
            'qty': qty / self.variant_package_id.qty if self.variant_package_id and self.variant_package_id.qty else qty,
            'procure_method': 'make_to_stock',
            'move_dest_ids': [(4, x.id) for x in self.move_dest_ids if x.state not in ('done', 'cancel')],
            'move_orig_ids': [(4, x.id) for x in self.move_orig_ids],
            'origin_returned_move_id': self.origin_returned_move_id.id,
            'price_unit': self.price_unit,
        }
        if self.env.context.get('force_split_uom_id'):
            vals['product_uom'] = self.env.context['force_split_uom_id']
        return vals

    def _action_done(self, cancel_backorder=False):
        # self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
        # moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
        # moves_ids_todo = OrderedSet()
        #
        # # Cancel moves where necessary ; we should do it before creating the extra moves because
        # # this operation could trigger a merge of moves.
        # for move in moves:
        #     if move.quantity_done <= 0:
        #         if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
        #             move._action_cancel()
        #
        # # Create extra moves where necessary
        # for move in moves:
        #     if move.state == 'cancel' or (move.quantity_done <= 0):
        #         continue
        #
        #     moves_ids_todo |= move._create_extra_move().ids
        #
        # moves_todo = self.browse(moves_ids_todo)
        # moves_todo._check_company()
        # # Split moves where necessary and move quants
        # backorder_moves_vals = []
        # for move in moves_todo:
        #     # To know whether we need to create a backorder or not, round to the general product's
        #     # decimal precision and not the product's UOM.
        #     rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        #     if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
        #         # Need to do some kind of conversion here
        #         qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
        #         new_move_vals = move._split(qty_split)
        #         backorder_moves_vals += new_move_vals
        # backorder_moves = self.env['stock.move'].create(backorder_moves_vals)
        # # The backorder moves are not yet in their own picking. We do not want to check entire packs for those
        # # ones as it could messed up the result_package_id of the moves being currently validated
        # backorder_moves.with_context(bypass_entire_pack=True)._action_confirm(merge=False)
        # if cancel_backorder:
        #     backorder_moves.with_context(moves_todo=moves_todo)._action_cancel()
        # moves_todo.mapped('move_line_ids').sorted()._action_done()
        # # Check the consistency of the result packages; there should be an unique location across
        # # the contained quants.
        # for result_package in moves_todo\
        #         .mapped('move_line_ids.result_package_id')\
        #         .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
        #     if len(result_package.quant_ids.filtered(lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity), precision_rounding=q.product_uom_id.rounding)).mapped('location_id')) > 1:
        #         raise UserError(_('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
        # picking = moves_todo.mapped('picking_id')
        # moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})
        #
        # new_push_moves = moves_todo.filtered(lambda m: m.picking_id.immediate_transfer)._push_apply()
        # if new_push_moves:
        #     new_push_moves._action_confirm()
        # move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
        # for move_dest in moves_todo.move_dest_ids:
        #     move_dests_per_company[move_dest.company_id.id] |= move_dest
        # for company_id, move_dests in move_dests_per_company.items():
        #     move_dests.sudo().with_company(company_id)._action_assign()
        #
        # # We don't want to create back order for scrap moves
        # # Replace by a kwarg in master
        # if self.env.context.get('is_scrap'):
        #     return moves_todo
        #
        # if picking and not cancel_backorder:
        #     backorder = picking._create_backorder()
        #     if any([m.state == 'assigned' for m in backorder.move_lines]):
        #        backorder._check_entire_pack()
        moves_todo = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        for move in moves_todo:
            if move.variant_package_id and move.variant_package_id.qty:
                move.qty = move.product_uom_qty / move.variant_package_id.qty
                move.package_qty_done = move.quantity_done / move.variant_package_id.qty
                # move.package_qty_done = 0.00
            else:
                move.qty = move.product_uom_qty
                move.package_qty_done = move.quantity_done
        for move in moves_todo:
            if move.product_id.product_tmpl_id.temp_checkbox:
                instance = self.env['shopify.instance.ept'].search([('is_cap_no_gap', '=', False)], limit=1)
                location_id = self.env["shopify.location.ept"].search([("instance_id", "=", instance.id)], limit=1)
                instance.connect_in_shopify()
                packs = move.product_id.variant_package_ids
                forcast_qty = move.product_id.virtual_available
                # for product
                if move.product_id.inventory_item_id:
                    shopify.InventoryLevel.set(location_id.shopify_location_id,
                                               move.product_id.inventory_item_id,
                                               int(forcast_qty))
                # for packs
                for pac in packs:
                    if pac.inventory_item_id:
                        shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                   pac.inventory_item_id,
                                                   int(forcast_qty / pac.qty))

        return moves_todo

    # def write(self, vals):
    #     if "package_qty_done" in vals.keys():
    #         if vals.get('package_qty_done') and vals["package_qty_done"] > 0:
    #             if self.variant_package_id:
    #                 vals["quantity_done"] = vals["package_qty_done"] * self.variant_package_id.qty
    #             else:
    #                 vals["quantity_done"] = vals["package_qty_done"]
    #     move = super(StockMove, self).write(vals)
    #     return move
