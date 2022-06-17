# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models
from ...shopify_ept import shopify


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        """
        Added comment by Udit
        create and paid invoice on the basis of auto invoice work flow
        when invoicing policy is 'delivery'.
        """
        result = super(StockPicking, self)._action_done()

        for picking in self:
            if picking.sale_id.invoice_status == 'invoiced':
                continue

            order = picking.sale_id
            work_flow_process_record = order and order.auto_workflow_process_id
            delivery_lines = picking.move_line_ids.filtered(lambda l: l.product_id.invoice_policy == 'delivery')

            if work_flow_process_record and delivery_lines and work_flow_process_record.create_invoice and \
                    picking.picking_type_id.code == 'outgoing':
                order.validate_and_paid_invoices_ept(work_flow_process_record)
        return result

    def send_to_shipper(self):
        """
        usage: If auto_processed_orders_ept = True passed in Context then we can not call send shipment from carrier
        This change is used in case of Import Shipped Orders for all connectors.
        @author: Keyur Kanani
        """
        context = dict(self._context)
        if context.get('auto_processed_orders_ept', False):
            return True
        return super(StockPicking, self).send_to_shipper()

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        instance = self.env['shopify.instance.ept'].search([], limit=1, order='id desc')
        location_id = self.env["shopify.location.ept"].search([("instance_id", "=", instance.id)], limit=1)
        instance.connect_in_shopify()
        for line in self.move_ids_without_package:
            if line.variant_package_id:
                if line.product_id.product_tmpl_id.temp_checkbox:
                    forcast_qty = line.variant_package_id.product_id.virtual_available
                    packs = line.variant_package_id.product_id.variant_package_ids
                    # for product stock Update on shopify
                    if line.product_id.inventory_item_id:
                        shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                   line.product_id.inventory_item_id,
                                                   int(forcast_qty))
                    # for packs stock Update on shopify
                    for pac in packs:
                        if pac.inventory_item_id:
                            shopify.InventoryLevel.set(location_id.shopify_location_id, pac.inventory_item_id,
                                                       int(forcast_qty / pac.qty))

            # if product and no pack stock Update on shopify
            else:
                if line.product_id.product_tmpl_id.temp_checkbox:
                    forcast_qty = line.product_id.virtual_available
                    packs = line.product_id.variant_package_ids
                    # for product
                    if line.product_id.inventory_item_id:
                        shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                   line.product_id.inventory_item_id,
                                                   int(forcast_qty))
                    # for packs
                    for pac in packs:
                        if pac.inventory_item_id:
                            shopify.InventoryLevel.set(location_id.shopify_location_id, pac.inventory_item_id,
                                                       int(forcast_qty / pac.qty))

        return res
