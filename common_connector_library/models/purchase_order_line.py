# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from itertools import groupby
from ...shopify_ept import shopify


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        instance = self.env['shopify.instance.ept'].search([], limit=1, order='id desc')
        location_id = self.env["shopify.location.ept"].search([("instance_id", "=", instance.id)], limit=1)
        instance.connect_in_shopify()
        if self.order_line:
            for line in self.order_line:
                if line.variant_package_id:
                    if line.product_id.product_tmpl_id.temp_checkbox:
                        forcast_qty = line.variant_package_id.product_id.virtual_available
                        packs = line.variant_package_id.product_id.variant_package_ids
                        # for product stock Update on shopify
                        shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                   line.product_id.inventory_item_id,
                                                   int(forcast_qty))
                        # for packs stock Update on shopify
                        if packs:
                            for pac in packs:
                                shopify.InventoryLevel.set(location_id.shopify_location_id, pac.inventory_item_id,
                                                           int(forcast_qty / pac.qty))
                # if product and no pack stock Update on shopify
                else:
                    if line.product_id.product_tmpl_id.temp_checkbox:
                        forcast_qty = line.product_id.virtual_available
                        packs = line.product_id.variant_package_ids
                        # for product
                        shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                   line.product_id.inventory_item_id,
                                                   int(forcast_qty))
                        # for packs
                        if packs:
                            for pac in packs:
                                shopify.InventoryLevel.set(location_id.shopify_location_id, pac.inventory_item_id,
                                                           int(forcast_qty / pac.qty))
        return res
