# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import json
import logging
import pytz
import time

from datetime import datetime
from dateutil import parser

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .. import shopify
from ..shopify.pyactiveresource.connection import ClientError

utc = pytz.utc

_logger = logging.getLogger("Shopify")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_shopify_order_status(self):
        """
        Set updated_in_shopify of order from the pickings.
        @author: Maulik Barad on Date 06-05-2020.
        """
        for order in self:
            if order.shopify_instance_id:
                pickings = order.picking_ids.filtered(lambda x: x.state != "cancel")
                if pickings:
                    outgoing_picking = pickings.filtered(
                        lambda x: x.location_dest_id.usage == "customer")
                    if all(outgoing_picking.mapped("updated_in_shopify")):
                        order.updated_in_shopify = True
                        continue
                order.updated_in_shopify = False
                continue
            order.updated_in_shopify = False

    def _search_shopify_order_ids(self, operator, value):
        query = """
                    select so.id from stock_picking sp
                    inner join sale_order so on so.procurement_group_id=sp.group_id                   
                    inner join stock_location on stock_location.id=sp.location_dest_id and stock_location.usage='customer'
                    where sp.updated_in_shopify = %s and sp.state != 'cancel' and
                    so.shopify_instance_id notnull
                """ % value
        self._cr.execute(query)
        results = self._cr.fetchall()
        order_ids = []
        for result_tuple in results:
            order_ids.append(result_tuple[0])
        order_ids = list(set(order_ids))
        return [('id', 'in', order_ids)]

    shopify_order_id = fields.Char("Shopify Order Ref", copy=False)
    shopify_order_number = fields.Char("Shopify Order Number", copy=False)
    shopify_instance_id = fields.Many2one("shopify.instance.ept", "Instance", copy=False)
    shopify_order_status = fields.Char("Shopify Order Status", copy=False, tracking=True,
                                       help="Shopify order status when order imported in odoo at the moment order"
                                            "status in Shopify.")
    shopify_payment_gateway_id = fields.Many2one('shopify.payment.gateway.ept',
                                                 string="Payment Gateway", copy=False)

    sale_api_data = fields.Text('All api data')

    risk_ids = fields.One2many("shopify.order.risk", 'odoo_order_id', "Risks", copy=False)
    shopify_location_id = fields.Many2one("shopify.location.ept", "Shopify Location", copy=False)
    checkout_id = fields.Char("Checkout Id", copy=False)
    is_risky_order = fields.Boolean("Risky Order?", default=False, copy=False)
    updated_in_shopify = fields.Boolean("Updated In Shopify ?", compute=_get_shopify_order_status,
                                        search='_search_shopify_order_ids')
    closed_at_ept = fields.Datetime("Closed At", copy=False)
    canceled_in_shopify = fields.Boolean("Canceled In Shopify", default=False, copy=False)
    is_pos_order = fields.Boolean("POS Order ?", copy=False, default=False)
    is_service_tracking_updated = fields.Boolean("Service Tracking Updated", default=False, copy=False)

    _sql_constraints = [('unique_shopify_order',
                         'unique(shopify_instance_id,shopify_order_id,shopify_order_number)',
                         "Shopify order must be Unique.")]

    def create_shopify_log_line(self, message, queue_line, log_book, order_name):
        """
        Creates log line with the message and makes the queue line fail, if queue line is passed.
        @author: Maulik Barad on Date 11-Sep-2020.
        """
        common_log_line_obj = self.env["common.log.lines.ept"]

        common_log_line_obj.shopify_create_order_log_line(message, log_book.model_id.id, queue_line, log_book,
                                                          order_name)
        if queue_line:
            queue_line.write({"state": "failed", "processed_at": datetime.now()})

        return

    def prepare_shopify_customer_and_addresses(self, order_response, pos_order, instance, order_data_line, log_book):
        """
        Searches for existing customer in Odoo and creates in odoo, if not found.
        @author: Maulik Barad on Date 11-Sep-2020.
        """
        res_partner_obj = self.env["res.partner"]
        shopify_res_partner_obj = self.env["shopify.res.partner.ept"]

        if pos_order:
            if order_response.get("customer"):
                partner = res_partner_obj.create_shopify_pos_customer(order_response, log_book, instance)
            else:
                partner = instance.shopify_default_pos_customer_id
        else:
            partner = order_response.get("customer", {}) and shopify_res_partner_obj.shopify_create_contact_partner(
                order_response.get("customer"), instance, False, log_book)

        if partner and partner.parent_id:
            partner = partner.parent_id
        if not partner:
            message = "Customer details are not available in %s Order." % (
                order_response.get(
                    "order_number"))
            if pos_order:
                message = "Default POS Customer is not set.\nPlease set Default POS Customer in " \
                          "Shopify Configuration."
            self.create_shopify_log_line(message, order_data_line, log_book, order_response.get("name"))
            _logger.info(message)
            return False, False, False

        invoice_address = order_response.get("billing_address",
                                             {}) and shopify_res_partner_obj.shopify_create_or_update_address(
            order_response.get("billing_address"), instance, partner, "invoice")
        if not invoice_address:
            invoice_address = partner

        delivery_address = order_response.get("shipping_address",
                                              {}) and shopify_res_partner_obj.shopify_create_or_update_address(
            order_response.get("shipping_address"), instance, partner, "delivery")
        if not delivery_address:
            delivery_address = invoice_address

        return partner, delivery_address, invoice_address

    def set_shopify_location_and_warehouse(self, order_response, instance, pos_order):
        """
        This method sets shopify location and warehouse related to that location in order.
        @author: Maulik Barad on Date 11-Sep-2020.
        """
        shopify_location = shopify_location_obj = self.env["shopify.location.ept"]
        if order_response.get("location_id"):
            shopify_location_id = order_response.get("location_id")
        elif order_response.get("fulfillments"):
            shopify_location_id = order_response.get("fulfillments")[0].get("location_id")
        else:
            shopify_location_id = False

        if shopify_location_id:
            shopify_location = shopify_location_obj.search(
                [("shopify_location_id", "=", shopify_location_id),
                 ("instance_id", "=", instance.id)],
                limit=1)

        if shopify_location and shopify_location.warehouse_for_order:
            warehouse_id = shopify_location.warehouse_for_order.id
        else:
            warehouse_id = instance.shopify_warehouse_id.id

        return {"shopify_location_id": shopify_location and shopify_location.id or False,
                "warehouse_id": warehouse_id, "is_pos_order": pos_order}

    def create_shopify_order_lines(self, lines, order_response, instance):
        """
        This method creates sale order line and discount line for Shopify order.
        @author: Maulik Barad on Date 11-Sep-2020.
        """
        total_discount = order_response.get("total_discounts", 0.0)
        order_number = order_response.get("order_number")

        for line in lines:
            # shopify_product = self.search_shopify_product_for_order_line(line, instance)
            # product = shopify_product.product_id
            product = self.env['product.product'].search([('default_code', '=', line.get('sku'))], limit=1)
            package_id = False
            # if not product:
            #     package_id = self.env['variant.package'].search([('code', '=', line.get('sku'))])
            #     product = package_id.product_id

            order_line = self.shopify_create_sale_order_line(line, product, line.get("quantity"),
                                                             product.name, line.get("price"),
                                                             order_response, package=package_id)
            if float(total_discount) > 0.0:
                discount_amount = 0.0
                for discount_allocation in line.get("discount_allocations"):
                    discount_amount += float(discount_allocation.get("amount"))
                if discount_amount > 0.0:
                    _logger.info("Creating discount line for Odoo order(%s) and Shopify order is (%s)"
                                 % (self.name, order_number))
                    self.shopify_create_sale_order_line({}, instance.discount_product_id, 1,
                                                        product.name, float(discount_amount) * -1,
                                                        order_response, previous_line=order_line,
                                                        is_discount=True)
                    _logger.info("Created discount line for Odoo order(%s) and Shopify order is (%s)"
                                 % (self.name, order_number))
        return

    def create_shopify_shipping_lines(self, order_response, instance):
        """
        Creates shipping lines for shopify orders.
        @author: Maulik Barad on Date 11-Sep-2020.
        """
        delivery_carrier_obj = self.env["delivery.carrier"]
        for line in order_response.get("shipping_lines", []):
            carrier = delivery_carrier_obj.shopify_search_create_delivery_carrier(line, instance)
            if carrier:
                self.write({"carrier_id": carrier.id})
                shipping_product = carrier.product_id
                self.shopify_create_sale_order_line(line, shipping_product, 1,
                                                    shipping_product.name or line.get("title"),
                                                    line.get("price"), order_response, is_shipping=True)
        return

    def import_shopify_orders(self, order_data_lines, log_book, is_queue_line=True):# is_queue line true mean direck order create
        """
        This method used to create a sale orders in Odoo.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 11/11/2019.
        Task Id : 157350
        @change: By Maulik Barad on Date 21-Sep-2020.
        """
        order_risk_obj = self.env["shopify.order.risk"]

        order_ids = []
        commit_count = 0
        instance = log_book.shopify_instance_id
        #ak yaha chnage ki hy
        instance.auto_import_product = True
        instance.connect_in_shopify()

        for order_data_line in order_data_lines:
            #if order if from caps no gaps
            if order_data_line.is_cap_no_gap:
                customer = self.env['res.partner'].search([('name', '=', order_data_line.customer_name), ('email', '=',order_data_line.customer_email)], limit=1)
                if not customer:
                    customer = self.env['res.partner'].create({
                        "name": order_data_line.customer_name,
                        "email": order_data_line.customer_email
                    })
                order_response = json.loads(order_data_line.order_data)
                order_date = parser.parse(order_response.get('created_at')).astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
                cap_contract = self.env['cap.contract'].search([('shopify_order_id', '=', order_response.get("id"))])
                if not cap_contract:
                    cap_contract = self.env['cap.contract'].create({
                        "name": order_response.get("name"),
                        "customer_id": customer.id,
                        "start_date": order_date,
                        "order_months": int(order_response.get('note_attributes')[0].get('value')),
                        "shopify_order_id": order_response.get("id"),
                        "company_id": instance.shopify_company_id.id,
                    })
                    #contract lines of caps no gaps
                    lines = order_response.get("line_items")
                    for line in lines:
                        product = self.env['cap.no.gap'].search([('daily_pack_sku', '=', line.get("sku"))])
                        if product:
                            self.env['contract.product'].create({
                                "product_pack_id": product.id,
                                "total_funding": float(line.get('price')),
                                "contract_id": cap_contract.id,
                            })
                            order_data_line.state = "done"
                        # if product not found in odoo
                        else:
                            message = "Product not found for order [" \
                                      "%s]" % order_response.get("name")
                            common_log_line_obj = self.env["common.log.lines.ept"]
                            model_id = common_log_line_obj.get_model_id(self._name)
                            common_log_line_obj.shopify_create_order_log_line(message, model_id,
                                                                              order_data_line, log_book)
                            order_data_line.write({'state': 'failed', 'processed_at': datetime.now()})
                            cap_contract.unlink()
                    cap_contract.action_start_contract()
                #when order is from confidence club
            else:

                commit_count += 1
                if commit_count == 5:
                    self._cr.commit()
                    commit_count = 0
                if is_queue_line:
                    order_data = order_data_line.order_data
                    order_response = json.loads(order_data)
                else:
                    if not isinstance(order_data_line, dict):
                        order_response = order_data_line.to_dict()
                    else:
                        order_response = order_data_line
                    order_data_line = False

                order_number = order_response.get("order_number")
                _logger.info("Started processing Shopify order(%s) and order id is(%s)"
                             % (order_number, order_response.get("id")))
                sale_order = self.search([("shopify_order_id", "=", order_response.get("id")),
                                          ("shopify_instance_id", "=", instance.id),
                                          ("shopify_order_number", "=", order_number)])
                if not sale_order:
                    sale_order = self.search([("shopify_instance_id", "=", instance.id),
                                              ("client_order_ref", "=", order_response.get("name"))])

                if not sale_order:
                    sale_order = self.search([("name", "=", order_response.get("name"))])

                if sale_order:
                    if order_data_line:
                        order_data_line.write({"state": "done", "processed_at": datetime.now(),
                                               "sale_order_id": sale_order.id})
                        self._cr.commit()
                    _logger.info("Done the Process of order Because Shopify Order(%s) is exist in Odoo and "
                                 "Odoo order is(%s)" % (order_number, sale_order.name))
                    # continue  # Skip existing order
                if not sale_order:
                    pos_order = True if order_response.get("source_name", "") == "pos" else False
                    partner, delivery_address, invoice_address = self.prepare_shopify_customer_and_addresses(
                        order_response, pos_order, instance, order_data_line, log_book)
                    if not partner:
                        continue

                    lines = order_response.get("line_items")
                    if self.check_mismatch_details(lines, instance, order_number, order_data_line, log_book):
                        _logger.info("Mismatch details found in this Shopify Order(%s) and id (%s)" % (
                            order_number, order_response.get("id")))
                        if order_data_line:
                            order_data_line.write({"state": "failed", "processed_at": datetime.now()})
                            #ak yeh change kiya hy
                        continue

                    sale_order = self.shopify_create_order(instance, partner, delivery_address, invoice_address,
                                                           order_data_line, order_response, log_book)
                    if not sale_order:
                        message = "Configuration missing in Odoo while importing Shopify Order(%s) and id (%s)" % (
                            order_number, order_response.get("id"))
                        _logger.info(message)
                        self.create_shopify_log_line(message, order_data_line, log_book, order_response.get("name"))
                        continue
                    order_ids.append(sale_order.id)

                    location_vals = self.set_shopify_location_and_warehouse(order_response, instance, pos_order)
                    sale_order.write(location_vals)

                    risk_result = shopify.OrderRisk().find(order_id=order_response.get("id"))
                    if risk_result:
                        order_risk_obj.shopify_create_risk_in_order(risk_result, sale_order)
                        risk = sale_order.risk_ids.filtered(lambda x: x.recommendation != "accept")
                        if risk:
                            sale_order.is_risky_order = True

                    _logger.info("Creating order lines for Odoo order(%s) and Shopify order is (%s)." % (
                        sale_order.name, order_number))
                    sale_order.create_shopify_order_lines(lines, order_response, instance)  # Order Line create here

                    _logger.info("Created order lines for Odoo order(%s) and Shopify order is (%s)"
                                 % (sale_order.name, order_number))

                    sale_order.create_shopify_shipping_lines(order_response, instance)
                    _logger.info("Created Shipping lines for order (%s)." % sale_order.name)

                    _logger.info("Starting auto workflow process for Odoo order(%s) and Shopify order is (%s)"
                                 % (sale_order.name, order_number))

                # if not sale_order.is_risky_order:

                    # if sale_order.shopify_order_status == "fulfilled":
                sale_order.sale_api_data = str(order_data_line.order_data) if order_data_line else str(order_response)
                if not sale_order.auto_workflow_process_id:
                    sale_order.auto_workflow_process_id = self.env['sale.workflow.process.ept'].search([], limit =1).id

                sale_order.auto_workflow_process_id.shipped_order_workflow_ept(sale_order)

                    # elif sale_order.shopify_order_status == "partial":
                    #     sale_order.auto_workflow_process_id.shipped_order_workflow_ept(sale_order)
                    #
                    # else:
                    #     sale_order.process_orders_and_invoices_ept()

                _logger.info("Done auto workflow process for Odoo order(%s) and Shopify order is (%s)"
                             % (sale_order.name, order_number))

                if order_data_line:
                    order_data_line.write({"state": "done", "processed_at": datetime.now(),
                                           "sale_order_id": sale_order.id})
                _logger.info("Processed the Odoo Order %s process and Shopify Order (%s)"
                             % (sale_order.name, order_number))

        return order_ids

    def check_mismatch_details(self, lines, instance, order_number, order_data_queue_line,
                               log_book_id):
        """This method used to check the mismatch details in the order lines.
            @param : self, lines, instance, order_number, order_data_queue_line
            @return:
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 11/11/2019.
            Task Id : 157350
        """
        shopify_product_obj = self.env["shopify.product.product.ept"]
        shopify_product_template_obj = self.env["shopify.product.template.ept"]
        #odoo Objects
        product_obj = self.env["product.product"]
        # product_package_obj = self.env["variant.package"]
        mismatch = False

        for line in lines:
            # shopify_variant = False
            product_package = False
            product_variant = False
            # sku = line.get("sku") or False
            # if line.get("variant_id"):
            #     product_variant = product_obj.search([("shopify_variant_id", "=", line.get("variant_id")), ("default_code", "=", line.get("sku"))])
            #     product_package = product_package_obj.search([("shopify_variant_id", "=", line.get("variant_id")), ("code", "=", line.get("sku"))])
            # else:
            product_variant = product_obj.search([("default_code", "=", line.get("sku"))])
            # product_package = product_package_obj.search([("code", "=", line.get("sku"))])

            if product_variant:
                continue
            # elif product_package:
            #     continue

            if not product_variant:
                line_variant_id = line.get("variant_id", False)
                line_product_id = line.get("product_id", False)
                if line_product_id and line_variant_id:
                    # shopify_product_template_obj.shopify_sync_products(False, line_product_id,
                    #                                                    instance, log_book_id,
                    #                                                    order_data_queue_line)
                    # if line.get("variant_id"):
                    #     product_variant = product_obj.search(
                    #         [("shopify_variant_id", "=", line.get("variant_id"))])
                    #
                    #     product_package = product_package_obj.search(
                    #         [("shopify_variant_id", "=", line.get("variant_id"))])

                    if not product_variant:
                        # message = "Product [%s][%s] not found for Order %s" % (
                        #     line.get("sku"), line.get("name"), order_number)
                        # self.create_shopify_log_line(message, order_data_queue_line, log_book_id, order_number)
                        # mismatch = True
                        # break
                        self.env['product.template'].create({
                            "name": line.get('name'),
                            "default_code": line.get('sku'),
                            "list_price": line.get('price'),
                            "invoice_policy": 'order',
                        })
                    # if not product_package:
                    #     message = "Product [%s][%s] not found for Order %s" % (
                    #         line.get("sku"), line.get("name"), order_number)
                    #     self.create_shopify_log_line(message, order_data_queue_line, log_book_id, order_number)
                    #     mismatch = True
                    #     break
                else:
                    # message = "Product ID is not available in %s Order line response. It might " \
                    #           "have happened that product has been deleted after order was " \
                    #           "placed." % order_number
                    # self.create_shopify_log_line(message, order_data_queue_line, log_book_id, order_number)
                    # mismatch = True
                    # break
                    self.env['product.template'].create({
                        "name": line.get('name'),
                        "default_code": line.get('sku'),
                        "list_price": line.get('price'),
                        "invoice_policy": 'order',
                    })
        return mismatch

    def shopify_create_order(self, instance, partner, shipping_address, invoice_address,
                             order_data_queue_line, order_response, log_book_id):
        """This method used to create a sale order.
            @param : self, instance, partner, shipping_address, invoice_address,order_data_queue_line, order_response
            @return: order
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 12/11/2019.
            Task Id : 157350
        """
        payment_gateway_obj = self.env["shopify.payment.gateway.ept"]
        payment_gateway, workflow = payment_gateway_obj.shopify_search_create_gateway_workflow(instance,
                                                                                               order_data_queue_line,
                                                                                               order_response,
                                                                                               log_book_id)

        if not all([payment_gateway, workflow]):
            return False

        order_vals = self.prepare_shopify_order_vals(instance, partner, shipping_address,
                                                     invoice_address, order_response,
                                                     payment_gateway,
                                                     workflow)

        order = self.create(order_vals)
        return order

    def prepare_shopify_order_vals(self, instance, partner, shipping_address,
                                   invoice_address, order_response, payment_gateway,
                                   workflow):
        """
        This method used to Prepare a order vals.
        @param : self, instance, partner, shipping_address,invoice_address, order_response, payment_gateway,workflow
        @return: order_vals
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 13/11/2019.
        Task Id : 157350
        """
        if order_response.get("created_at", False):
            order_date = order_response.get("created_at", False)
            date_order = parser.parse(order_date).astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
        else:
            date_order = time.strftime("%Y-%m-%d %H:%M:%S")
            date_order = str(date_order)

        pricelist_id = self.shopify_set_pricelist(order_response=order_response, instance=instance)
        ordervals = {
            "company_id": instance.shopify_company_id.id if instance.shopify_company_id else False,
            "partner_id": partner.ids[0],
            "partner_invoice_id": invoice_address.ids[0],
            "partner_shipping_id": shipping_address.ids[0],
            "warehouse_id": instance.shopify_warehouse_id.id if instance.shopify_warehouse_id else False,
            "date_order": date_order,
            "state": "draft",
            "pricelist_id": pricelist_id.id if pricelist_id else False,
            "team_id": instance.shopify_section_id.id if instance.shopify_section_id else False,
            "client_order_ref": order_response.get("name")
        }
        ordervals = self.create_sales_order_vals_ept(ordervals)

        ordervals.update({
            "checkout_id": order_response.get("checkout_id"),
            "note": order_response.get("note"),
            "shopify_order_id": order_response.get("id"),
            "shopify_order_number": order_response.get("order_number"),
            "shopify_payment_gateway_id": payment_gateway and payment_gateway.id or False,
            "shopify_instance_id": instance.id,
            "shopify_order_status": order_response.get("fulfillment_status") or "unfulfilled",
            "picking_policy": workflow.picking_policy or False,
            "auto_workflow_process_id": workflow and workflow.id
        })

        if not instance.is_use_default_sequence:
            if instance.shopify_order_prefix:
                name = "%s_%s" % (instance.shopify_order_prefix, order_response.get("name"))
            else:
                name = order_response.get("name")
            ordervals.update({"name": name})
        return ordervals

    def shopify_set_pricelist(self, instance, order_response):
        """
        Author:Bhavesh Jadav 09/12/2019 for the for set price list based on the order response currency because of if
        order currency different then the erp currency so we need to set proper pricelist for that sale order
        otherwise set pricelist based on instance configurations
        """
        currency_obj = self.env["res.currency"]
        pricelist_obj = self.env["product.pricelist"]
        order_currency = order_response.get("currency") or False
        if order_currency:
            currency = currency_obj.search([("name", "=", order_currency)])
            if not currency:
                currency = currency_obj.search(
                    [("name", "=", order_currency), ("active", "=", False)])
                if currency:
                    currency.write({"active": True})
                    pricelist = pricelist_obj.search(
                        [("currency_id", "=", currency.id), ("company_id", "=", instance.shopify_company_id.id)],
                        limit=1)
                    if pricelist:
                        return pricelist
                    else:
                        pricelist_vals = {"name": currency.name,
                                          "currency_id": currency.id,
                                          "company_id": instance.shopify_company_id.id}
                        pricelist = pricelist_obj.create(pricelist_vals)
                        return pricelist
                pricelist = instance.shopify_pricelist_id.id if instance.shopify_pricelist_id else False
                return pricelist
            pricelist = pricelist_obj.search([("currency_id", "=", currency.id)], limit=1)
            return pricelist
        pricelist = instance.shopify_pricelist_id.id if instance.shopify_pricelist_id else False
        return pricelist

    def search_shopify_product_for_order_line(self, line, instance):
        """This method used to search shopify product for order line.
            @param : self, line, instance
            @return: shopify_product
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 14/11/2019.
            Task Id : 157350
        """
        shopify_product_obj = self.env["shopify.product.product.ept"]
        variant_id = line.get("variant_id")
        shopify_product = shopify_product_obj.search(
            [("shopify_instance_id", "=", instance.id), ("variant_id", "=", variant_id)])
        if shopify_product:
            return shopify_product
        shopify_product = shopify_product_obj.search([("shopify_instance_id", "=", instance.id),
                                                      ("default_code", "=", line.get("sku"))])
        shopify_product and shopify_product.write({"variant_id": variant_id})
        if shopify_product:
            return shopify_product

    def shopify_create_sale_order_line(self, line, product, quantity, product_name, price,
                                       order_response, is_shipping=False, previous_line=False,
                                       is_discount=False, package=False):
        """
        This method used to create a sale order line.
        @param : self, line, product, quantity,product_name, order_id,price, is_shipping=False
        @return: order_line_id
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 14/11/2019.
        Task Id : 157350
        """
        sale_order_line_obj = self.env["sale.order.line"]
        instance = self.shopify_instance_id

        uom_id = product and product.uom_id and product.uom_id.id or False
        line_vals = {
            "product_id": product and product.ids[0] or False,
            "order_id": self.id,
            "company_id": self.company_id.id,
            "product_uom": uom_id,
            "name": product_name,
            "price_unit": price,
            "order_qty": quantity,
        }
        order_line_vals = sale_order_line_obj.create_sale_order_line_ept(line_vals)
        if instance.apply_tax_in_order == "create_shopify_tax":
            taxes_included = order_response.get("taxes_included") or False
            tax_ids = []
            if line and line.get("tax_lines"):
                if line.get("taxable"):
                    # This is used for when the one product is taxable and another product is not
                    # taxable
                    tax_ids = self.shopify_get_tax_id_ept(instance,
                                                          line.get("tax_lines"),
                                                          taxes_included)
                else:
                    tax = self.env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 0.0), (
                    "company_id", "=", instance.shopify_warehouse_id.company_id.id)], limit=1)
                    tax_ids = [(6, 0, [tax.id])]

                if is_shipping:
                    # In the Shopify store there is configuration regarding tax is applicable on shipping or not, if applicable then this use.
                    # tax_ids = self.shopify_get_tax_id_ept(instance,
                    #                                       line.get("tax_lines"),
                    #                                       taxes_included)
                    tax = self.env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 10.00), (
                    "company_id", "=", instance.shopify_warehouse_id.company_id.id)], limit=1)
                    tax_ids = [(6, 0, [tax.id])]
            elif not line:
                tax_ids = self.shopify_get_tax_id_ept(instance,
                                                      order_response.get("tax_lines"),
                                                      taxes_included)
            else:
                tax = self.env["account.tax"].search([("type_tax_use", "=", "sale"),("amount", "=", 0.0),("company_id", "=", instance.shopify_warehouse_id.company_id.id)], limit=1)
                tax_ids = [(6, 0, [tax.id])]

            order_line_vals["tax_id"] = tax_ids
            # When the one order with two products one product with tax and another product
            # without tax and apply the discount on order that time not apply tax on discount
            # which is
            if is_discount and not previous_line.tax_id:
                tax = self.env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 0.0),
                                                      ("company_id", "=", instance.shopify_warehouse_id.company_id.id)],
                                                     limit=1)
                tax_ids = [(6, 0, [tax.id])]
                order_line_vals["tax_id"] = tax_ids
        else:
            if is_shipping and not line.get("tax_lines", []):
                tax = self.env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 0.0),
                                                      ("company_id", "=", instance.shopify_warehouse_id.company_id.id)],
                                                     limit=1)
                tax_ids = [(6, 0, [tax.id])]
                order_line_vals["tax_id"] = tax_ids

        if is_discount:
            order_line_vals["name"] = "Discount for " + str(product_name)
            if instance.apply_tax_in_order == "odoo_tax" and is_discount:
                # tax = self.env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 0.0),
                #                                       ("company_id", "=", instance.shopify_warehouse_id.company_id.id)],
                #                                      limit=1)
                # tax_ids = [(6, 0, [tax.id])]
                order_line_vals["tax_id"] = previous_line.tax_id
         # description to sku while creating sale order line

        product = self.env['product.product'].search([('id', '=', order_line_vals['product_id'])])
        order_line_vals.update({
            "shopify_line_id": line.get("id"),
            "is_delivery": is_shipping,
            "name": product.default_code,
            "qty": quantity,
            # "variant_package_id": package.id if package else False,
            # 'display_type': 'line_note'
        })
        order_line = sale_order_line_obj.create(order_line_vals)
        # order_line._onchange_qty()
        return order_line

    @api.model
    def shopify_get_tax_id_ept(self, instance, tax_lines, tax_included):
        """This method used to search tax in Odoo.
            @param : self,instance,order_line,tax_included
            @return: tax_id
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 18/11/2019.
            Task Id : 157350
        """
        tax_id = []
        taxes = []
        company = instance.shopify_warehouse_id.company_id
        for tax in tax_lines:
            rate = float(tax.get("rate", 0.0))
            price = float(tax.get('price', 0.0))
            title = tax.get("title")
            rate = rate * 100
            if rate != 0.0 and price != 0.0:
                if tax_included:
                    name = "%s_(%s %s included)_%s" % (title, str(rate), "%", company.name)
                else:
                    name = "%s_(%s %s excluded)_%s" % (title, str(rate), "%", company.name)
                tax_id = self.env["account.tax"].search(
                    [("price_include", "=", tax_included), ("type_tax_use", "=", "sale"),
                     ("amount", "=", rate), ("name", "=", name),
                     ("company_id", "=", instance.shopify_warehouse_id.company_id.id)], limit=1)
                if not tax_id:
                    tax_id = self.sudo().shopify_create_account_tax(instance, rate, tax_included,
                                                                    company, name)
                if tax_id:
                    taxes.append(tax_id.id)
        if taxes:
            tax_id = [(6, 0, taxes)]
        return tax_id

    @api.model
    def shopify_create_account_tax(self, instance, value, price_included, company, name):
        """This method used to create tax in Odoo when importing orders from Shopify to Odoo.
            @param : self, value, price_included, company, name
            @return: account_tax_id
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 18/11/2019.
            Task Id : 157350
        """
        account_tax_obj = self.env["account.tax"]

        account_tax_id = account_tax_obj.create({"name": name, "amount": float(value),
                                                 "type_tax_use": "sale", "price_include": price_included,
                                                 "company_id": company.id})

        account_tax_id.mapped("invoice_repartition_line_ids").write(
            {"account_id": instance.invoice_tax_account_id.id if instance.invoice_tax_account_id else False})
        account_tax_id.mapped("refund_repartition_line_ids").write(
            {"account_id": instance.credit_tax_account_id.id if instance.credit_tax_account_id else False})

        return account_tax_id

    @api.model
    def closed_at(self, instance):
        sales_orders = self.search([('warehouse_id', '=', instance.shopify_warehouse_id.id),
                                    ('shopify_order_id', '!=', False),
                                    ('shopify_instance_id', '=', instance.id),
                                    ('state', '=', 'done'), ('closed_at_ept', '=', False)],
                                   order='date_order')

        instance.connect_in_shopify()

        for sale_order in sales_orders:
            order = shopify.Order.find(sale_order.shopify_order_id)
            order.close()
            sale_order.write({'closed_at_ept': datetime.now()})
        return True

    def get_shopify_carrier_code(self, picking):
        """
        Gives carrier name from picking, if available.
        @author: Maulik Barad on Date 16-Sep-2020.
        """
        carrier_name = ""
        if picking.carrier_id:
            carrier_name = picking.carrier_id.shopify_tracking_company or picking.carrier_id.shopify_source or picking.carrier_id.name or ''
        return carrier_name

    def prepare_tracking_numbers_and_lines_for_fulfilment(self, picking):
        """
        This method prepares tracking numbers' list and list of dictionaries of shopify line id and
        fulfilled qty for that.
        @author: Maulik Barad on Date 17-Sep-2020.
        """
        tracking_numbers = []
        line_items = []

        shopify_line_ids = not self.is_service_tracking_updated and self.order_line.filtered(
            lambda l: l.shopify_line_id and l.product_id.type == "service" and not l.is_delivery).mapped(
            "shopify_line_id") or []

        if picking.mapped("package_ids").filtered(lambda l: l.tracking_no):
            multi_tracking_order = True
        else:
            multi_tracking_order = False

        moves = picking.move_lines
        if not multi_tracking_order:
            product_moves = moves.filtered(
                lambda x: x.sale_line_id.product_id.id == x.product_id.id and x.state == "done")
            for move in product_moves:
                shopify_line_id = move.sale_line_id.shopify_line_id

                line_items.append({"id": shopify_line_id, "quantity": int(move.product_qty)})
                tracking_numbers.append(picking.carrier_tracking_ref or "")

            kit_sale_lines = moves.filtered(
                lambda x: x.sale_line_id.product_id.id != x.product_id.id and x.state == "done").sale_line_id
            for kit_sale_line in kit_sale_lines:
                shopify_line_id = kit_sale_line.shopify_line_id
                line_items.append({"id": shopify_line_id, "quantity": int(kit_sale_line.product_qty)})
                tracking_numbers.append(picking.carrier_tracking_ref or "")
        else:
            product_moves = moves.filtered(
                lambda x: x.sale_line_id.product_id.id == x.product_id.id and x.state == "done")
            for move in product_moves:
                total_qty = 0
                shopify_line_id = move.sale_line_id.shopify_line_id

                for move_line in move.move_line_ids:
                    tracking_no = move_line.result_package_id.tracking_no or ""
                    total_qty += move_line.qty_done
                    tracking_numbers.append(tracking_no)

                line_items.append({"id": shopify_line_id, "quantity": int(total_qty)})

            kit_move_lines = moves.filtered(
                lambda x: x.sale_line_id.product_id.id != x.product_id.id and x.state == "done")
            existing_sale_line_ids = []
            for move in kit_move_lines:
                if move.sale_line_id.id in existing_sale_line_ids:
                    continue

                shopify_line_id = move.sale_line_id.shopify_line_id
                existing_sale_line_ids.append(move.sale_line_id.id)

                tracking_no = move.move_line_ids.result_package_id.mapped("tracking_no") or []
                tracking_no = tracking_no and tracking_no[0] or ""
                line_items.append({"id": shopify_line_id, "quantity": int(move.sale_line_id.product_uom_qty)})
                tracking_numbers.append(tracking_no)

        for line in shopify_line_ids:
            quantity = sum(
                self.order_line.filtered(lambda l: l.shopify_line_id == line).mapped("product_uom_qty"))
            line_items.append({"id": line, "quantity": int(quantity)})
            self.write({"is_service_tracking_updated": True})

        return tracking_numbers, line_items

    def update_order_status_in_shopify(self, instance):
        """
        find the picking with below condition
            1. shopify_instance_id = instance.id
            2. updated_in_shopify = False
            3. state = Done
            4. location_dest_id.usage = customer
        get order line data from the picking and process on that. Process on only those products which type is not service.
        get carrier_name from the picking
        get product qty from move lines. If one move having multiple move lines then total qty of all the move lines.
        shopify_line_id wise set the product qty_done
        set tracking details
        using shopify Fulfillment API update the order status
        @author: Maulik Barad on Date 16-Sep-2020.
        Task Id : 157905
        """
        common_log_book_obj = self.env["common.log.book.ept"]
        common_log_line_obj = self.env["common.log.lines.ept"]
        location_obj = self.env["stock.location"]
        stock_picking_obj = self.env["stock.picking"]
        shopify_location_obj = self.env["shopify.location.ept"]

        model_id = common_log_line_obj.get_model_id(self._name)
        notify_customer = instance.notify_customer

        log_book = common_log_book_obj.create({"type": "export",
                                               "module": "shopify_ept",
                                               "model_id": model_id,
                                               "shopify_instance_id": instance.id})
        _logger.info(_("Update Order Status process start for '%s' Instance") % instance.name)

        instance.connect_in_shopify()
        customer_locations = location_obj.search([("usage", "=", "customer")])
        picking_ids = stock_picking_obj.search([("shopify_instance_id", "=", instance.id),
                                                ("updated_in_shopify", "=", False),
                                                ("state", "=", "done"),
                                                ("location_dest_id", "in", customer_locations.ids)],
                                               order="date")
        for picking in picking_ids:
            carrier_name = self.get_shopify_carrier_code(picking)
            sale_order = picking.sale_id

            _logger.info("We are processing Sale order '%s' and Picking '%s'" % (sale_order.name, picking.name))

            try:
                order = shopify.Order.find(sale_order.shopify_order_id)
                order_data = order.to_dict()
                if order_data.get('fulfillment_status') == 'fulfilled':
                    _logger.info('Order %s is already fulfilled' % sale_order.name)
                    sale_order.picking_ids.filtered(lambda l: l.state == 'done').write({'updated_in_shopify': True})
                    continue
            except Exception as e:
                continue

            order_lines = sale_order.order_line
            if order_lines and order_lines.filtered(lambda s: s.product_id.type != 'service' and not s.shopify_line_id):
                message = (_(
                    "- Order status could not be updated for order %s.\n- Possible reason can be, Shopify order line reference is missing, which is used to update Shopify order status at Shopify store. "
                    "\n- This might have happen because user may have done changes in order "
                    "manually, after the order was imported." %
                    sale_order.name))
                _logger.info(message)
                self.create_shopify_log_line(message, False, log_book, sale_order.client_order_ref)
                continue

            tracking_numbers, line_items = sale_order.prepare_tracking_numbers_and_lines_for_fulfilment(picking)

            if not line_items:
                message = "No order lines found for the update order shipping status for order [%s]" \
                          % sale_order.name
                _logger.info(message)
                self.create_shopify_log_line(message, False, log_book, sale_order.client_order_ref)
                continue

            shopify_location_id = sale_order.shopify_location_id or False
            if not shopify_location_id:
                shopify_location_id = shopify_location_obj.search(
                    [("warehouse_for_order", "=", sale_order.warehouse_id.id), ("instance_id", "=", instance.id)])
                if not shopify_location_id:
                    shopify_location_id = shopify_location_obj.search([("is_primary_location", "=", True),
                                                                       ("instance_id", "=", instance.id)])
                if not shopify_location_id:
                    message = "Primary Location not found for instance %s while update order " \
                              "shipping status." % (
                                  instance.name)
                    _logger.info(message)
                    self.create_shopify_log_line(message, False, log_book, sale_order.client_order_ref)
                    continue

            try:
                fulfillment_vals = {"order_id": sale_order.shopify_order_id,
                                    "location_id": shopify_location_id.shopify_location_id,
                                    "tracking_numbers": list(set(tracking_numbers)),
                                    "tracking_urls": [picking.carrier_tracking_url or ''],
                                    "tracking_company": carrier_name, "line_items": line_items,
                                    "notify_customer": notify_customer}

                new_fulfillment = shopify.Fulfillment(fulfillment_vals)
                fulfillment_result = new_fulfillment.save()
                if not fulfillment_result:
                    message = "Order [%s] status not updated due to some issue in fulfillment " \
                              "request/response." % (
                                  sale_order.name)
                    _logger.info(message)
                    self.create_shopify_log_line(message, False, log_book, sale_order.client_order_ref)
                    continue

            except ClientError as e:
                if hasattr(e, "response"):
                    if e.response.code == 429 and e.response.msg == "Too Many Requests":
                        time.sleep(5)
                        fulfillment_result = new_fulfillment.save()
            except Exception as e:
                message = "%s" % str(e)
                _logger.info(message)
                self.create_shopify_log_line(message, False, log_book, sale_order.client_order_ref)
                continue

            picking.write({"updated_in_shopify": True})
            sale_order.shopify_location_id = shopify_location_id

        if not log_book.log_lines:
            log_book.unlink()

        self.closed_at(instance)
        return True

    @api.model
    def process_shopify_order_via_webhook(self, order_data, instance, update_order=False):
        """
        Creates order data queue and process it.
        This method is for order imported via create and update webhook.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 10-Jan-2020..
        @param order_data: Dictionary of order's data.
        @param instance: Instance of Shopify.
        @param update_order: If update order webhook id called.
        """
        shopify_order_queue_obj = self.env['shopify.order.data.queue.ept']

        if not update_order:
            order_ids = shopify_order_queue_obj.process_shopify_orders_directly([order_data], instance)
            if order_ids:
                _logger.info("Imported order {0} of {1} via Webhook Successfully".format(order_data.get("id"),
                                                                                         instance.name))
            else:
                _logger.info("Couldn't import order {0} of {1} via Webhook. Please check the log once.".format(
                    order_data.get("id"),
                    instance.name))
            return True

        shopify_order_queue_line_obj = self.env["shopify.order.data.queue.line.ept"]
        shopify_order_queue_line_obj.create_order_data_queue_line([order_data],
                                                                  instance,
                                                                  created_by='webhook',
                                                                  is_cap=instance.is_cap_no_gap)
        self._cr.commit()
        return True

    @api.model
    def update_shopify_order(self, queue_lines, log_book):
        """
        This method will update order as per its status got from Shopify.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 13-Jan-2020..
        @param queue_lines: Order Data Queue Line.
        @param log_book: Common Log Book.
        @return: Updated Sale order.
        """
        orders = self
        for queue_line in queue_lines:
            message = ""
            shopify_instance = queue_line.shopify_instance_id
            order_data = json.loads(queue_line.order_data)
            shopify_status = order_data.get("financial_status")
            order = self.search([("shopify_instance_id", "=", shopify_instance.id),
                                 ("shopify_order_id", "=", order_data.get("id"))])

            if not order:
                self.import_shopify_orders(queue_line, log_book, is_queue_line=True)
                return True

            # Below condition use for, In shopify store there is full refund.
            if order_data.get('cancel_reason'):
                cancelled = order.cancel_shopify_order()
                if not cancelled:
                    message = "System can not cancel the order {0} as one of the Delivery Order " \
                              "related to it is in the 'Done' status.".format(order.name)
            if shopify_status == "refunded":
                if not message:
                    total_refund = 0.0
                    for refund in order_data.get('refunds'):
                        # We take[0] because we got one transaction in one refund. If there are multiple refunds then
                        # each transaction attaches with a refund.
                        if refund.get('transactions') and refund.get('transactions')[0].get('kind') == \
                                'refund' and refund.get('transactions')[0].get('status') == 'success':
                            refunded_amount = refund.get('transactions')[0].get('amount')
                            total_refund += float(refunded_amount)
                    refunded = order.create_shopify_refund(order_data.get("refunds"), total_refund)
                    if refunded[0] == 0:
                        message = "- Refund can only be generated if it's related order " \
                                  "invoice is found.\n- For order [%s], system could not find the " \
                                  "related order invoice. " % (order_data.get('name'))
                    elif refunded[0] == 2:
                        message = "- Refund can only be generated if it's related order " \
                                  "invoice is in 'Post' status.\n- For order [%s], system found " \
                                  "related invoice but it is not in 'Post' status." % (
                                      order_data.get('name'))
                    elif refunded[0] == 3:
                        message = "- Partial refund is received from Shopify for order [%s].\n " \
                                  "- System do not process partial refunds.\n" \
                                  "- Either create partial refund manually in Odoo or do full " \
                                  "refund in Shopify." % (order_data.get('name'))
            # Below condition use for, In shopify store there is fulfilled order.
            elif order_data.get('fulfillment_status') == 'fulfilled':
                fulfilled = order.fulfilled_shopify_order()
                if isinstance(fulfilled, bool) and not fulfilled:
                    message = "There is not enough stock to complete Delivery for order [" \
                              "%s]" % order_data.get('name')
                elif not fulfilled:
                    message = "There is not enough stock to complete Delivery for order [" \
                              "%s]" % order_data.get('name')

            if message:
                common_log_line_obj = self.env["common.log.lines.ept"]
                model_id = common_log_line_obj.get_model_id(self._name)
                common_log_line_obj.shopify_create_order_log_line(message, model_id,
                                                                  queue_line, log_book)
                queue_line.write({'state': 'failed', 'processed_at': datetime.now()})
            else:
                queue_line.state = "done"
        return orders

    def cancel_shopify_order(self):
        """
        Cancelled the sale order when it is cancelled in Shopify Store with full refund.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 13-Jan-2020..
        """
        if "done" in self.picking_ids.mapped("state"):
            return False
        self.action_cancel()
        self.canceled_in_shopify = True
        return True

    def create_shopify_refund(self, refunds_data, total_refund):
        """
        Creates refund of shopify order, when order is refunded in Shopify.
        It will need invoice created and posted for creating credit note in Odoo, otherwise it will
        create log and generate activity as per configuration.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 13-Jan-2020..
        @param refunds_data: Data of refunds.
        @param total_refund: Total refund amount.
        @return:[0] : When no invoice is created.
                [1] : When invoice is not posted.
                [2] : When partial refund was made in Shopify.
                [True]:When credit notes are created or partial refund is done.
        """
        if not self.invoice_ids:
            return [0]
        invoices = self.invoice_ids.filtered(lambda x: x.move_type == "out_invoice")
        refunds = self.invoice_ids.filtered(lambda x: x.move_type == "out_refund")
        if refunds:
            return [True]

        for invoice in invoices:
            if not invoice.state == "posted":
                return [2]
        if self.amount_total == total_refund:
            move_reversal = self.env["account.move.reversal"].with_context({"active_model": "account.move",
                                                                            "active_ids": invoices.ids}).create(
                {"refund_method": "cancel",
                 "reason": "Refunded from shopify"
                 if len(refunds_data) > 1 else
                 refunds_data[0].get("note")})
            move_reversal.reverse_moves()
            move_reversal.new_move_ids.message_post(
                body="Credit note generated by Webhook as Order refunded in Shopify.")
            return [True]
        return [3]

    def fulfilled_shopify_order(self):
        """
        If order is not confirmed yet, confirms it first.
        Make the picking done, when order will be fulfilled in Shopify.
        This method is used for Update order webhook.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 13-Jan-2020..
        """
        if self.state not in ["sale", "done", "cancel"]:
            self.action_confirm()
        return self.fulfilled_picking_for_shopify(self.picking_ids.filtered(lambda x:
                                                                            x.location_dest_id.usage
                                                                            == "customer"))

    def fulfilled_picking_for_shopify(self, pickings):
        """
        It will make the pickings done.
        This method is used for Update order webhook.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 13-Jan-2020..
        """
        for picking in pickings.filtered(lambda x: x.state not in ['cancel', 'done']):
            if picking.state != "assigned":
                if picking.move_lines.move_orig_ids:
                    completed = self.fulfilled_picking_for_shopify(picking.move_lines.move_orig_ids.picking_id)
                    if not completed:
                        return False
                picking.action_assign()
                # # Add by Vrajesh Dt.01/04/2020 automatically validate delivery when import POS
                # order in shopify
                if picking.sale_id and (
                        picking.sale_id.is_pos_order or picking.sale_id.shopify_order_status == "fulfilled"):
                    for move_id in picking.move_ids_without_package:
                        picking.move_line_ids.create({
                            'product_id': move_id.product_id.id,
                            'product_uom_id': move_id.product_id.uom_id.id,
                            'qty_done': move_id.product_uom_qty,
                            'location_id': move_id.location_id.id,
                            'picking_id': picking.id,
                            'location_dest_id': move_id.location_dest_id.id,
                        })
                    picking.action_done()
                    return True
                if picking.state != "assigned":
                    return False
            result = picking.button_validate()
            if isinstance(result, dict):
                context = result.get("context")
                context.update({"skip_sms": True})
                model = result.get("res_model", "")
                # model can be stock.immediate.transfer or stock backorder.confirmation
                if model:
                    record = self.env[model].with_context(context).create({})
                    record.process()
            if picking.state == "done":
                picking.message_post(body="Picking is done by Webhook as Order is fulfilled in Shopify.")
                pickings.updated_in_shopify = True
                return result
        return True

    def _prepare_invoice(self):
        """This method used set a shopify instance in customer invoice.
            @param : self
            @return: inv_val
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 20/11/2019.
            Task Id : 157911
        """
        inv_val = super(SaleOrder, self)._prepare_invoice()
        if self.shopify_instance_id:
            inv_val.update({'shopify_instance_id': self.shopify_instance_id.id})
        return inv_val

    def cancel_in_shopify(self):
        """This method used to open a wizard to cancel order in Shopify.
            @param : self
            @return: action
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 20/11/2019.
            Task Id : 157911
        """
        view = self.env.ref('shopify_ept.view_shopify_cancel_order_wizard')
        context = dict(self._context)
        context.update({'active_model': 'sale.order', 'active_id': self.id, 'active_ids': self.ids})
        return {
            'name': _('Cancel Order In Shopify'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shopify.cancel.refund.order.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    shopify_line_id = fields.Char("Shopify Line", copy=False)

    def unlink(self):
        """
        @author: Haresh Mori on date:17/06/2020
        """
        for record in self:
            if record.order_id.shopify_order_id:
                msg = _(
                    "You can not delete this line because this line is Shopify order line and we need Shopify line id while we are doing update order status")
                raise UserError(msg)
        return super(SaleOrderLine, self).unlink()
