# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from itertools import groupby
from ...shopify_ept import shopify


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        instance = self.env['shopify.instance.ept'].search([('is_cap_no_gap', '=', False)], limit=1)
        location_id = self.env["shopify.location.ept"].search([("instance_id", "=", instance.id)], limit=1)
        instance.connect_in_shopify()
        if self.order_line:
            for line in self.order_line:
                # if line.variant_package_id:
                #     if line.product_id.product_tmpl_id.temp_checkbox:
                #         forcast_qty = line.variant_package_id.product_id.virtual_available
                #         packs = line.variant_package_id.product_id.variant_package_ids
                #         # for product stock Update on shopify
                #         if line.product_id.inventory_item_id:
                #             shopify.InventoryLevel.set(location_id.shopify_location_id,
                #                                        line.product_id.inventory_item_id,
                #                                        int(forcast_qty))
                #         # for packs stock Update on shopify
                #         # for pac in packs:
                #         #     if pac.inventory_item_id:
                #         #         shopify.InventoryLevel.set(location_id.shopify_location_id, pac.inventory_item_id,
                #         #                                    int(forcast_qty / pac.qty))
                #
                # # if product and no pack stock Update on shopify
                # else:
                if line.product_id.product_tmpl_id.temp_checkbox:
                    product_id = line.product_id
                    bom_id = line.product_id.bom_ids.filtered(lambda l: l.product_id.id == product_id.id)
                    if bom_id and len(bom_id) == 1 and bom_id.type == 'phantom' and len(bom_id.bom_line_ids) == 1 \
                            and bom_id.bom_line_ids.product_id.product_tmpl_id.id == bom_id.product_tmpl_id.id:
                        product_id = bom_id.bom_line_ids.product_id
                    mrp_lines = self.env['mrp.bom.line'].search([('product_id', '=', product_id.id)])
                    if product_id.inventory_item_id:
                        shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                   product_id.inventory_item_id,
                                                   int(product_id.virtual_available))

                    for mr_line in mrp_lines:
                        bom_id = mr_line.bom_id
                        if bom_id.type == 'phantom' and len(bom_id.bom_line_ids) == 1 and mr_line.product_id.product_tmpl_id.id == bom_id.product_tmpl_id.id:
                            if bom_id.product_id.inventory_item_id:
                                shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                           bom_id.product_id.inventory_item_id,
                                                           int(bom_id.product_id.virtual_available))


                    # for packs
                    # for pac in packs:
                    #     if pac.inventory_item_id:
                    #         shopify.InventoryLevel.set(location_id.shopify_location_id, pac.inventory_item_id,
                    #                                    int(forcast_qty / pac.qty))

        return res
