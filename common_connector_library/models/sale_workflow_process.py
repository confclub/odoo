# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.tests import Form, tagged
import json
import pytz
from dateutil import parser
from ...shopify_ept import shopify
utc = pytz.utc



class SaleWorkflowProcess(models.Model):
    _name = "sale.workflow.process.ept"
    _description = "sale workflow process"

    def _update_qty_on_shopify(self, product_id, pack_id):
        pass

    @api.model
    def _default_journal(self):
        """
        It will return sales journal of company passed in context or user's company.
        Migration done by twinkalc August 2020.
        """
        account_journal_obj = self.env['account.journal']
        company_id = self._context.get('company_id', self.env.company.id)
        domain = [('type', '=', "sale"), ('company_id', '=', company_id)]
        return account_journal_obj.search(domain, limit=1)

    name = fields.Char(size=64)
    validate_order = fields.Boolean("Confirm Quotation", default=False,
                                    help="If it's checked, Order will be Validated.")
    create_invoice = fields.Boolean('Create & Validate Invoice', default=False,
                                    help="If it's checked, Invoice for Order will be Created and Posted.")
    register_payment = fields.Boolean(default=False, help="If it's checked, Payment will be registered for Invoice.")
    invoice_date_is_order_date = fields.Boolean('Force Invoice Date', help="If it's checked, then the invoice date "
                                                                           "will be the same as the order date")
    journal_id = fields.Many2one('account.journal', string='Payment Journal', domain=[('type', 'in', ['cash', 'bank'])])
    sale_journal_id = fields.Many2one('account.journal', string='Sales Journal', default=_default_journal,
                                      domain=[('type', '=', 'sale')])
    picking_policy = fields.Selection([('direct', 'Deliver each product when available'),
                                       ('one', 'Deliver all products at once')], string='Shipping Policy',
                                      default="one")
    inbound_payment_method_id = fields.Many2one('account.payment.method', string="Debit Method",
                                                domain=[('payment_type', '=', 'inbound')],
                                                help="Means of payment for collecting money. Odoo modules offer various"
                                                     "payments handling facilities, but you can always use the 'Manual'"
                                                     "payment method in order to manage payments outside of the"
                                                     "software.")

    @api.onchange("validate_order")
    def onchange_validate_order(self):
        """
        Onchange of Confirm Quotation field.
        If 'Confirm Quotation' is unchecked, the 'Create & Validate Invoice' will be unchecked too.
        """
        for record in self:
            if not record.validate_order:
                record.create_invoice = False

    @api.onchange("create_invoice")
    def onchange_create_invoice(self):
        """
       Onchange of Create & Validate Invoice field.
       If 'Create & Validate Invoice' is unchecked, the 'Register Payment' and 'Force Invoice Date' will be unchecked
       too.
       """
        for record in self:
            if not record.create_invoice:
                record.register_payment = False
                record.invoice_date_is_order_date = False

    @api.model
    def auto_workflow_process_ept(self, auto_workflow_process_id=False, order_ids=[]):
        """
        Added comment by Udit
        This method will find draft sale orders which are not having invoices yet, confirmed it and done the payment
        according to the auto invoice workflow configured in sale order.
        :param auto_workflow_process_id: auto workflow process id
        :param order_ids: ids of sale orders
        Migration done by twinkalc August 2020
        """
        sale_order_obj = self.env['sale.order']
        workflow_process_obj = self.env['sale.workflow.process.ept']
        if not auto_workflow_process_id:
            work_flow_process_records = workflow_process_obj.search([])
        else:
            work_flow_process_records = workflow_process_obj.browse(auto_workflow_process_id)

        if not order_ids:
            orders = sale_order_obj.search([('auto_workflow_process_id', 'in', work_flow_process_records.ids),
                                            ('state', 'not in', ('done', 'cancel', 'sale')),
                                            ('invoice_status', '!=', 'invoiced')])
        else:
            orders = sale_order_obj.search([('auto_workflow_process_id', 'in', work_flow_process_records.ids),
                                            ('id', 'in', order_ids)])
        orders.process_orders_and_invoices_ept()

        return True

    def shipped_order_workflow_ept(self, orders):
        """
        This method is for processing the shipped orders.
        :param orders: list of order objects
        :return: True
        Migration done by twinkalc August 2020
        """
        self.ensure_one()
        module_obj = self.env['ir.module.module']
        stock_location_obj = self.env["stock.location"]

        mrp_module = module_obj.sudo().search([('name', '=', 'mrp'), ('state', '=', 'installed')])
        customer_location = stock_location_obj.search([("usage", "=", "customer")], limit=1)
        # All shipment
        data_dic = json.loads(orders.sale_api_data)
        if not orders.picking_ids and orders.order_line:
            orders.action_confirm()
            created_date = data_dic.get("created_at", False)
            date_order = parser.parse(created_date).astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
            orders.date_order = date_order
        instance = self.env['shopify.instance.ept'].search([('is_cap_no_gap', '=', False)], limit=1)
        location_id = self.env["shopify.location.ept"].search([("instance_id", "=", instance.id)], limit=1)
        instance.connect_in_shopify()
        for order_line in orders.order_line:
            #if pack
            if order_line.variant_package_id:
                if order_line.product_id.product_tmpl_id.temp_checkbox:
                    forcast_qty = order_line.variant_package_id.product_id.virtual_available
                    packs = order_line.variant_package_id.product_id.variant_package_ids
                    # for product stock Update on shopify
                    if order_line.product_id.inventory_item_id:
                        shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                   order_line.product_id.inventory_item_id,
                                                   int(forcast_qty))
                    #for packs stock Update on shopify
                    for pac in packs:
                        if pac.inventory_item_id:
                            shopify.InventoryLevel.set(location_id.shopify_location_id, pac.inventory_item_id,
                                               int(forcast_qty/pac.qty))
            # if product and no pack stock Update on shopify
            else:
                if order_line.product_id.product_tmpl_id.temp_checkbox:
                    forcast_qty = order_line.product_id.virtual_available
                    packs = order_line.product_id.variant_package_ids
                    #for product
                    if order_line.product_id.inventory_item_id:
                        shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                   order_line.product_id.inventory_item_id,
                                                   int(forcast_qty))
                    # for packs stock Update on shopify
                    for pac in packs:
                        if pac.inventory_item_id:
                            shopify.InventoryLevel.set(location_id.shopify_location_id, pac.inventory_item_id,
                                                       int(forcast_qty / pac.qty))

        if data_dic.get('fulfillment_status') == 'fulfilled':
            for pick in orders.picking_ids.filtered(lambda line: line.state not in ['done']):
                for ful_fill_list in data_dic.get('fulfillments'):
                    if str(ful_fill_list.get("id")) != pick.shopify_delivery_id and pick.state != 'done':
                        for line in pick.move_ids_without_package:
                            line.package_qty_done = line.qty
                            line.quantity_done = line.qty * line.variant_package_id.qty if line.variant_package_id else line.qty
                            line._onchange_qty_done()
                        pick.action_assign()
                        pick.button_validate()
                        pick.shopify_delivery_id = ful_fill_list.get("id")

                Form(self.env['stock.immediate.transfer']).save().process()

            orders.state = 'sale'

        elif data_dic.get('fulfillment_status') == 'partial':
            dict_of_shopify = {}
            dilevries = orders.picking_ids.filtered(lambda line: line.state in ['done'])
            delivery_list = [delivery.shopify_delivery_id for delivery in dilevries]
            if data_dic.get('fulfillments'):
                for ful_fill_list in data_dic.get('fulfillments'):
                    if str(ful_fill_list.get("id")) not in delivery_list:
                        for item_line in ful_fill_list.get('line_items'):
                             dict_of_shopify[item_line.get('sku')] = item_line.get('quantity')

                for pick in orders.picking_ids.filtered(lambda line: line.state not in ['done']):
                    for line in pick.move_ids_without_package:
                        code = line.variant_package_id.code if line.variant_package_id else line.product_id.default_code
                        if code in list(dict_of_shopify):
                            line.package_qty_done = dict_of_shopify[code]
                            line.quantity_done = dict_of_shopify[code] * line.variant_package_id.qty if line.variant_package_id else dict_of_shopify[code]
                            line._onchange_qty_done()

                    pick.action_assign()
                    res_dict = pick.button_validate()
                    pick.shopify_delivery_id = ful_fill_list.get("id")
                    Form(self.env['stock.backorder.confirmation'].with_context(res_dict['context'])).save().process()

        # only restock items without payments
        if data_dic.get('refunds'):
            odoo_refund_list = [refund.shopify_refund_id for refund in self.env['stock.move'].search([('origin', '=', orders.name)])]
            for refund in data_dic.get('refunds'):
                if str(refund['id']) not in odoo_refund_list:
                    if refund.get("restock"):
                        for item in refund.get('refund_line_items'):
                            for line in orders.order_line:
                                if line.variant_package_id:
                                    if line.variant_package_id.code == item.get('line_item')['sku']:
                                        product = line.variant_package_id.product_id
                                        product_qty = (item.get('quantity') * line.variant_package_id.qty)
                                        product_uom = line.product_uom
                                        if product and product_qty and product_uom:
                                            vals = {
                                                'name': _('Auto processed move : %s') % product.display_name,
                                                'company_id': self.env.company.id,
                                                'origin': line.order_id.name,
                                                'product_id': product.id if product else False,
                                                'product_uom_qty': product_qty,
                                                'product_uom': product_uom.id if product_uom else False,
                                                'location_id': self.env.ref("shopify_ept.customer_location").id,
                                                'location_dest_id': self.env.ref("shopify_ept.customer_stock_location").id,
                                                'state': 'confirmed',
                                                'shopify_refund_id': refund['id'],
                                                'variant_package_id': line.variant_package_id.id,
                                                'sale_line_id': line.id
                                            }
                                            stock_move = self.env['stock.move'].create(vals)
                                            stock_move._action_assign()
                                            stock_move._set_quantity_done(product_qty)
                                            stock_move._action_done()
                                    # proccess for updating stock of pack in shopify
                                    if line.product_id.product_tmpl_id.temp_checkbox:
                                        forcast_qty = line.variant_package_id.product_id.virtual_available
                                        packs = line.variant_package_id.product_id.variant_package_ids
                                        # for product
                                        if line.product_id.inventory_item_id:
                                            shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                                       line.product_id.inventory_item_id,
                                                                       int(forcast_qty))
                                        for pac in packs:
                                            if pac.inventory_item_id:
                                                shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                                           pac.inventory_item_id,
                                                                           int(forcast_qty / pac.qty))

                                else:
                                    if line.product_id.default_code == item.get('line_item')['sku']:
                                        product = line.product_id
                                        product_qty = item.get('quantity')
                                        product_uom = line.product_uom
                                        if product and product_qty and product_uom:
                                            vals = {
                                                'name': _('Auto processed move : %s') % product.name,
                                                'company_id': self.env.company.id,
                                                'origin': line.order_id.name,
                                                'product_id': product.id if product else False,
                                                'product_uom_qty': product_qty,
                                                'product_uom': product_uom.id if product_uom else False,
                                                'location_id': self.env.ref("shopify_ept.customer_location").id,
                                                'location_dest_id': self.env.ref("shopify_ept.customer_stock_location").id,
                                                'state': 'confirmed',
                                                'shopify_refund_id': refund['id'],
                                                'sale_line_id': line.id
                                            }
                                            stock_move = self.env['stock.move'].create(vals)
                                            stock_move._action_assign()
                                            stock_move._set_quantity_done(product_qty)
                                            stock_move._action_done()

                                    # proccess for updating stock in shopify
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
                                                shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                                           pac.inventory_item_id,
                                                                           int(forcast_qty / pac.qty))

        # elif data_dic.get('fulfillment_status') == 'partial':
        #     dict_of_shopify = {}
        #     dict_of_odoo = {}
        #     if data_dic.get('fulfillments'):
        #         for ful_fill_list in data_dic.get('fulfillments'):
        #             for item_line in ful_fill_list.get('line_items'):
        #                  dict_of_shopify[item_line.get('sku')] = item_line.get('quantity')
        #
        #     for pick in orders.picking_ids.filtered(lambda line: line.state not in ['done']):
        #         for line in pick.move_ids_without_package:
        #             dict_of_odoo[line.product_id.default_code] = line.quantity_done if line.quantity_done else line.product_uom_qty
        #
        #     need_to_sync = {}
        #     for shopify in dict_of_shopify:
        #         for odoo in dict_of_odoo:
        #             if odoo == shopify:
        #                 need_to_sync[shopify] = dict_of_shopify[shopify]
        #
        #     list(dict_of_odoo)
        #     for pick in orders.picking_ids.filtered(lambda line: line.state not in ['done']):
        #         lines_sync = False
        #         for line in pick.move_ids_without_package:
        #             if line.product_id.default_code in list(need_to_sync):
        #                 lines_sync = True
        #                 line.quantity_done = need_to_sync[line.product_id.default_code]
        #             else:
        #                 line.quantity_done = 0
        #         if lines_sync:
        #             # pass
        #             pick.action_assign()
        #             res_dict = pick.button_validate()
        #             Form(self.env['stock.backorder.confirmation'].with_context(res_dict['context'])).save().process()


        if data_dic.get('financial_status') == 'paid':
            if orders.order_line.filtered(lambda l: l.product_id.invoice_policy == 'order'):
                if orders.invoice_ids and orders.invoice_ids[0] and orders.invoice_ids[0].state != 'posted':
                    if orders.invoice_ids and orders.invoice_ids[0] and orders.invoice_ids[0].state == 'draft':
                        orders.invoice_ids[0].action_post()
                        action_data = orders.invoice_ids[0].action_register_payment()
                        wizard = self.env['account.payment.register'].with_context(action_data['context']).create({})
                        wizard.action_create_payments()
                elif orders.invoice_ids and orders.invoice_ids[0] and orders.invoice_ids[0].state == 'draft':
                    orders.invoice_ids[0].action_post()
                    action_data = orders.invoice_ids[0].action_register_payment()
                    wizard = self.env['account.payment.register'].with_context(action_data['context']).create({})
                    wizard.action_create_payments()

                elif not orders.invoice_ids:
                    orders.validate_and_paid_invoices_ept(self)

        # elif data_dic.get('financial_status') == "refunded":
        #     invoice = orders.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type == 'out_invoice')
        #     if invoice:
        #         for inv in invoice:
        #             inv.action_reverse()
        #             move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move",
        #                                                                            active_ids=inv.ids).create({
        #                 'reason': 'no reason',
        #                 'refund_method': 'refund',
        #             })
        #             reversal = move_reversal.reverse_moves()
        #             reverse_move = self.env['account.move'].browse(reversal['res_id'])

        elif data_dic.get('financial_status') in ["partially_refunded", "refunded"]:

            odoo_refund_list = [refund.shopify_refund_id for refund in self.env['stock.move'].search([('origin', '=', orders.name)])]

            if data_dic.get('refunds'):
                for refund in data_dic.get('refunds'):
                    if str(refund['id']) not in odoo_refund_list:
                        if refund.get("restock"):
                            for item in refund.get('refund_line_items'):
                                for line in orders.order_line:
                                    if line.variant_package_id:
                                        if line.variant_package_id.code == item.get('line_item')['sku']:
                                            product = line.variant_package_id.product_id
                                            product_qty = (item.get('quantity') * line.variant_package_id.qty)
                                            product_uom = line.product_uom
                                            if product and product_qty and product_uom:
                                                vals = {
                                                    'name': _('Auto processed move : %s') % product.display_name,
                                                    'company_id': self.env.company.id,
                                                    'origin': line.order_id.name,
                                                    'product_id': product.id if product else False,
                                                    'product_uom_qty': product_qty,
                                                    'product_uom': product_uom.id if product_uom else False,
                                                    'location_id': self.env.ref("shopify_ept.customer_location").id,
                                                    'location_dest_id': self.env.ref("shopify_ept.customer_stock_location").id,
                                                    'state': 'confirmed',
                                                    'shopify_refund_id': refund['id'],
                                                    'variant_package_id':line.variant_package_id.id,
                                                    'sale_line_id': line.id
                                                }
                                                stock_move = self.env['stock.move'].create(vals)
                                                stock_move._action_assign()
                                                stock_move._set_quantity_done(product_qty)
                                                stock_move._action_done()
                                        # proccess for updating stock of pack in shopify
                                        if line.product_id.product_tmpl_id.temp_checkbox:
                                            forcast_qty = line.variant_package_id.product_id.virtual_available
                                            packs = line.variant_package_id.product_id.variant_package_ids
                                            # for product
                                            if line.product_id.inventory_item_id:
                                                shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                                           line.product_id.inventory_item_id,
                                                                           int(forcast_qty))
                                            for pac in packs:
                                                if pac.inventory_item_id:
                                                    shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                                               pac.inventory_item_id,
                                                                               int(forcast_qty / pac.qty))

                                    else:
                                        if line.product_id.default_code == item.get('line_item')['sku']:
                                            product = line.product_id
                                            product_qty = item.get('quantity')
                                            product_uom = line.product_uom
                                            if product and product_qty and product_uom:
                                                vals = {
                                                    'name': _('Auto processed move : %s') % product.name,
                                                    'company_id': self.env.company.id,
                                                    'origin': line.order_id.name,
                                                    'product_id': product.id if product else False,
                                                    'product_uom_qty': product_qty,
                                                    'product_uom': product_uom.id if product_uom else False,
                                                    'location_id': self.env.ref("shopify_ept.customer_location").id,
                                                    'location_dest_id': self.env.ref("shopify_ept.customer_stock_location").id,
                                                    'state': 'confirmed',
                                                    'shopify_refund_id': refund['id'],
                                                    'sale_line_id': line.id
                                                }
                                                stock_move = self.env['stock.move'].create(vals)
                                                stock_move._action_assign()
                                                stock_move._set_quantity_done(product_qty)
                                                stock_move._action_done()

                                        #proccess for updating stock in shopify
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
                                                    shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                                               pac.inventory_item_id,
                                                                               int(forcast_qty / pac.qty))
            #proccess for refund invoices
            invoice = orders.invoice_ids.filtered(
                        lambda r: r.move_type == 'out_invoice' and r.state == 'posted')

            if not invoice:
                if not orders.invoice_ids:
                    orders.validate_and_paid_invoices_ept(self)
                    invoice = orders.invoice_ids[0]
                else:
                    orders.invoice_ids[0].action_post()
                    action_data = orders.invoice_ids[0].action_register_payment()
                    wizard = self.env['account.payment.register'].with_context(action_data['context']).create({})
                    wizard.action_create_payments()
                    invoice = orders.invoice_ids[0]

            refund_invoice = orders.invoice_ids.filtered(
                        lambda r: r.move_type == 'out_refund' and r.state == 'posted')

            odoo_refund_list = [refund.shopify_refund_id for refund in refund_invoice]


            if data_dic.get('refunds'):
                for refund in data_dic.get('refunds'):
                    if str(refund['id']) not in odoo_refund_list:
                        invoice.action_reverse()
                        move_reversal = self.env['account.move.reversal'].with_context(
                            active_model="account.move",
                            active_ids=invoice.ids).create({
                            'reason': 'shopify reason',
                            'refund_method': 'refund',
                        })
                        reversal = move_reversal.reverse_moves()
                        reverse_move = self.env['account.move'].browse(reversal['res_id'])
                        reverse_move.shopify_refund_id = refund['id']
                        dict_of_refund = {}
                        if refund.get('refund_line_items'):
                            for item in refund.get('refund_line_items'):
                                dict_of_refund[item.get('line_item')['sku']] = item.get('quantity')

                            for line in reverse_move.invoice_line_ids:
                                if line.variant_package_id:
                                    if line.variant_package_id.code in dict_of_refund.keys():
                                        ctx = dict(self._context or {})
                                        ctx["check_move_validity"] = False
                                        line.with_context(ctx).write(
                                            {'quantity': dict_of_refund[line.variant_package_id.code]})
                                        line.move_id.with_context(ctx)._onchange_invoice_line_ids()
                                        line.with_context(ctx)._onchange_mark_recompute_taxes()
                                        line.with_context(ctx)._onchange_price_subtotal()
                                    else:
                                        ctx = dict(self._context or {})
                                        ctx["check_move_validity"] = False
                                        line.with_context(ctx).unlink()
                                else:
                                    if line.product_id.code in dict_of_refund.keys():
                                        ctx = dict(self._context or {})
                                        ctx["check_move_validity"] = False
                                        line.with_context(ctx).write(
                                            {'quantity': dict_of_refund[line.product_id.code]})
                                        line.move_id.with_context(ctx)._onchange_invoice_line_ids()
                                        line.with_context(ctx)._onchange_mark_recompute_taxes()
                                        line.with_context(ctx)._onchange_price_subtotal()
                                    else:
                                        ctx = dict(self._context or {})
                                        ctx["check_move_validity"] = False
                                        line.with_context(ctx).unlink()

                        else:
                            first = True
                            for i in reverse_move.invoice_line_ids:
                                if first:
                                    ctx = dict(self._context or {})
                                    ctx["check_move_validity"] = False
                                    i.with_context(ctx).write(
                                        {'quantity': 1,
                                         'product_id': self.env.ref('shopify_ept.product_product_manual_refund').id,
                                         # 'product_uom_id': self.env.ref('shopify_ept.product_product_manual_refund').uom_id.id,
                                         "price_unit": float(refund.get('transactions')[0]['amount'])})
                                    i.move_id.with_context(ctx)._onchange_invoice_line_ids()
                                    i.with_context(ctx)._onchange_mark_recompute_taxes()
                                    i.with_context(ctx)._onchange_price_subtotal()
                                    first = False
                                else:
                                    ctx = dict(self._context or {})
                                    ctx["check_move_validity"] = False

                                    i.with_context(ctx).write(
                                        {'quantity': 0})
                                    i.move_id.with_context(ctx)._onchange_invoice_line_ids()
                                    i.with_context(ctx)._onchange_mark_recompute_taxes()
                                    i.with_context(ctx)._onchange_price_subtotal()


                            # product = self.env.ref('shopify_ept.product_product_manual_refund')
                            # account = self.env['account.account'].search([('id', '=', 47)])
                            # ctx = dict(self._context or {})
                            # ctx["check_move_validity"] = False
                            # line = reverse_move.invoice_line_ids.with_context(ctx).create({
                            #     "product_id": product.id,
                            #     "name": product.name,
                            #     'quantity': 0,
                            #     "price_unit": float(refund.get('transactions')[0]['amount']),
                            #     "product_uom_id": product.uom_id.id,
                            #     "account_id": account.id,
                            #     'currency_id': reverse_move.currency_id.id,
                            #     "move_id": reverse_move.id,
                            # })
                            # line.with_context(ctx).write(
                            #     {'quantity': 1})
                            # line.move_id.with_context(ctx)._onchange_invoice_line_ids()
                            # line.with_context(ctx)._onchange_mark_recompute_taxes()
                            # line.with_context(ctx)._onchange_price_subtotal()

                        reverse_move.with_context(ctx)._onchange_invoice_line_ids()
                        if reverse_move.amount_total:
                            reverse_move.action_post()
                            action_data = reverse_move.action_register_payment()
                            wizard = self.env['account.payment.register'].with_context(action_data['context']).create({})
                            wizard.action_create_payments()





                # if invoice:
                #     for invo in invoice:
                #         if invo.shopify_refund_id not in list_of_odoo:
                #             invo.shopify_refund_id = refund['id']
                #             invo.action_reverse()
                #             move_reversal = self.env['account.move.reversal'].with_context(
                #                 active_model="account.move",
                #                 active_ids=invo.ids).create({
                #                 'reason': 'shopify reason',
                #                 'refund_method': 'refund',
                #             })
                #             reversal = move_reversal.reverse_moves()
                #             reverse_move = self.env['account.move'].browse(reversal['res_id'])
                #             # if reverse_move.invoice_line_ids:
                #             #     for line in reverse_move.invoice_line_ids:
                #             #         dict_of_odoo[line.product_id.default_code] = line.quantity
                #             #
                #             # need_to_chnage = {}
                #             # for shopify in dict_of_shopify:
                #             #     for odoo in dict_of_odoo:
                #             #         if odoo == shopify:
                #             #             need_to_chnage[shopify] = dict_of_shopify[shopify]
                #
                #             for line in reverse_move.invoice_line_ids:
                #                 for ref in refund['refund_line_items']:
                #                     if ref['line_item']['sku'] == line.product_id.default_code:
                #                         ctx = dict(self._context or {})
                #                         ctx["check_move_validity"] = False
                #                         line.with_context(ctx).write(
                #                             {'quantity': ref['quantity']})
                #                         line.move_id.with_context(ctx)._onchange_invoice_line_ids()
                #                         line.with_context(ctx)._onchange_mark_recompute_taxes()
                #                         line.with_context(ctx)._onchange_price_subtotal()
                #             reverse_move.action_post()
                #             action_data = reverse_move.action_register_payment()
                #             wizard = Form(self.env['account.payment.register'].with_context(
                #                 action_data['context'])).save()
                #             wizard.action_create_payments()
                #                             # line.with_context(ctx)._get_fields_onchange_balance_model()
                #                             # line._onchange_price_subtotal()
                #
                #
                #
                #     # if id in refund
                #
                #
                #     # for item in refund.get('refund_line_items'):
                #     #     dict_of_shopify[item.get('line_item')['sku']] = item.get('quantity')
                #     #
                #     # invoice = orders.invoice_ids.filtered(
                #     #     lambda r: r.move_type == 'out_invoice' and r.state == 'posted')
                #     #
                #     # credit_notes = orders.invoice_ids.filtered(
                #     #     lambda r: r.move_type == 'out_refund' and r.state == 'posted')
                #     #
                #     # if credit_notes:
                #     #     for credit in credit_notes:
                #     #         for cr in credit.invoice_line_ids:
                #     #             if cr.product_id.default_code in dict_of_odoo:
                #     #                 dict_of_odoo[cr.product_id.default_code] += cr.quantity
                #     #             else:
                #     #                 dict_of_odoo[cr.product_id.default_code] = cr.quantity
                #
                #     # dict_of_shopify - dict_of_odoo
                #
                #     # Odoo Dic qty for all Credit note
                #     # Shopify qty  - odoo qty <= 0 Ignore else make credit note
                #
                #             # reverse_move._check_balanced()

        else:
            if not orders.invoice_ids:
                orders._create_invoices()

        # if data_dic.get('financial_status') == "refunded":
        #     dict_of_shopify = {}
        #     dict_of_odoo = {}
        #     if data_dic.get('fulfillments'):
        #         for ful_fill_list in data_dic.get('fulfillments'):
        #             for item_line in ful_fill_list.get('line_items'):
        #                 dict_of_shopify[item_line.get('sku')] = item_line.get('quantity')
        #
        #     for pick in orders.picking_ids:
        #         if pick.state == 'done' and pick.location_id.usage == 'internal':
        #             for line in pick.move_ids_without_package:
        #                 dict_of_odoo[line.product_id.default_code] = line.quantity_done if line.quantity_done else line.product_uom_qty
        #
        #     need_to_sync = {}
        #     for shopify in dict_of_shopify:
        #         for odoo in dict_of_odoo:
        #             if odoo == shopify:
        #                 need_to_sync[shopify] = dict_of_shopify[shopify]
        #
        #     for pick in orders.picking_ids:
        #         stock_return_picking_form = Form(self.env['stock.return.picking']
        #                                          .with_context(active_ids=pick.ids, active_id=pick.id,
        #                                                        active_model='stock.picking'))
        #         return_wiz = stock_return_picking_form.save()
        #         for return_move in return_wiz.product_return_moves:
        #             if return_move.product_id.default_code in list(need_to_sync):
        #                 return_move.write({
        #                     'quantity': need_to_sync[return_move.product_id.default_code],
        #                     'to_refund': True
        #                 })
        #
        #         res = return_wiz.create_returns()
        #         return_pick = self.env['stock.picking'].browse(res['res_id'])

        # if data_dic.get('financial_status') in ["partially_refunded", "refunded"]:
        #     dict_of_shopify = {}
        #     dict_of_odoo = {}
        #     if data_dic.get('refunds'):
        #         for refund in data_dic.get('refunds'):
        #             for item in refund.get('refund_line_items'):
        #                 dict_of_shopify[item.get('line_item')['sku']] = item.get('quantity')
        #
        #     #  dict_of_shopify Update Deli destination type internal
        #         for pick in orders.picking_ids:
        #             if pick.state == 'done' and pick.location_dest_id.usage == 'internal':
        #                 for line in pick.move_ids_without_package:
        #                     for shopify in dict_of_shopify:
        #                         if line.quantity_done == dict_of_shopify[shopify]:
        #                             dict_of_shopify[line.product_id.default_code] = dict_of_shopify[line.product_id.default_code] - line.quantity_done # yaha sy confirm kr lyna usman bhai sy
        #     # fecthing data of odoo orders line in dictionery
        #     for pick in orders.picking_ids:
        #         if pick.state == 'done' and pick.location_id.usage == 'internal':
        #             for line in pick.move_ids_without_package:
        #                 dict_of_odoo[
        #                     line.product_id.default_code] = line.quantity_done if line.quantity_done else line.product_uom_qty
        #
        #     need_to_sync = {}
        #     for shopify in dict_of_shopify:
        #         for odoo in dict_of_odoo:
        #             if odoo == shopify:
        #                 need_to_sync[shopify] = dict_of_shopify[shopify]
        #     # creating return of products
        #     for pick in orders.picking_ids:
        #         if dict_of_shopify[shopify] > 0.0:
        #             stock_return_picking_form = Form(self.env['stock.return.picking']
        #                                              .with_context(active_ids=pick.ids, active_id=pick.id,
        #                                                            active_model='stock.picking'))
        #             return_wiz = stock_return_picking_form.save()
        #             for return_move in return_wiz.product_return_moves:
        #                 if return_move.product_id.default_code in list(dict_of_shopify):
        #                     if return_move.quantity - dict_of_shopify[return_move.product_id.default_code] <= 0:
        #                         given_qty = dict_of_shopify[return_move.product_id.default_code]
        #                         dict_of_shopify[return_move.product_id.default_code] = 0
        #                     else:
        #                         given_qty = dict_of_shopify[return_move.product_id.default_code]
        #                         dict_of_shopify[return_move.product_id.default_code] = return_move.quantity - dict_of_shopify[return_move.product_id.default_code]
        #
        #                     return_move.write({
        #                         'quantity': given_qty,
        #                         'to_refund': True
        #                     })
        #
        #             res = return_wiz.create_returns()
        #             return_pick = self.env['stock.picking'].browse(res['res_id'])
        #             dict_of_shopify = {}
        #         else:
        #             break




        # Remove this line because it create stock move.
        # order.auto_shipped_order_ept(customer_location, mrp_module)
        # delivered_lines = orders.order_line.filtered(lambda l: l.product_id.invoice_policy != 'order')
        # if delivered_lines:
        #     orders.validate_and_paid_invoices_ept(self)
        return True
