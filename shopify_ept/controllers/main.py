# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger("Shopify")


class Main(http.Controller):

    @http.route("/shopify_odoo_webhook_for_product_update", csrf=False, auth="public", type="json")
    def update_product_webhook(self):
        """
        Route for handling the product update webhook of Shopify.
        @author: Dipak Gogiya on Date 10-Jan-2020.
        """
        res, instance = self.get_basic_info("shopify_odoo_webhook_for_product_update")

        if not res:
            return

        _logger.info("PRODUCT WEBHOOK call for product: %s" % res.get("title"))

        shopify_template = request.env["shopify.product.template.ept"].with_context(
            active_test=False).search([("shopify_tmpl_id", "=", res.get("id")),
                                       ("shopify_instance_id", "=", instance.id)], limit=1)

        if shopify_template or (res.get("published_scope") == "web" and res.get("published_at")):
            request.env["shopify.product.data.queue.ept"].sudo().create_shopify_product_queue_from_webhook(
                res, instance)

        return

    @http.route("/shopify_odoo_webhook_for_product_delete", csrf=False, auth="public", type="json")
    def delete_product_webhook(self):
        """
        Route for handling the product delete webhook for Shopify
        @author: Dipak Gogiya on Date 10-Jan-2020.
        """
        res, instance = self.get_basic_info("shopify_odoo_webhook_for_product_delete")

        if not res:
            return

        _logger.info("DELETE PRODUCT WEBHOOK call for product: %s" % res.get("title"))
        shopify_template = request.env["shopify.product.template.ept"].search(
            [("shopify_tmpl_id", "=", res.get("id")),
             ("shopify_instance_id", "=", instance.id)], limit=1)
        if shopify_template:
            shopify_template.write({"active": False})
        return

    @http.route("/shopify_odoo_webhook_for_customer_create", csrf=False, method="POST",
                auth="public", type="json")
    def shopify_odoo_webhook_for_customer_create(self):
        res, instance = self.get_basic_info("shopify_odoo_webhook_for_customer_create")
        if not res:
            return

        _logger.info(
            "CREATE CUSTOMER WEBHOOK call for Customer: %s" % (res.get("first_name") + " " + res.get("last_name")))
        self.customer_webhook_process(res, instance)
        return

    @http.route("/shopify_odoo_webhook_for_customer_update", csrf=False, method="POST", auth="public", type="json")
    def shopify_odoo_webhook_for_customer_update(self):
        """
        Controller for customer update webhook.
        @change: By Maulik Barad on Date 23-Sep-2020.
        """
        res, instance = self.get_basic_info("shopify_odoo_webhook_for_customer_update")
        if not res:
            return

        _logger.info(
            "UPDATE CUSTOMER WEBHOOK call for Customer: %s" % (res.get("first_name") + " " + res.get("last_name")))
        self.customer_webhook_process(res, instance)
        return

    def customer_webhook_process(self, response, instance):
        """
        Method used for Create & Update customer webhook.
        @author: Maulik Barad on Date 23-Sep-2020.
        """
        process_import_export_model = request.env["shopify.process.import.export"].sudo()
        process_import_export_model.webhook_customer_create_process(response, instance)
        return True

    @http.route("/shopify_odoo_webhook_for_orders_partially_updated", csrf=False, auth="public", type="json")
    def update_order_webhook(self):
        """
        Route for handling the order update webhook of Shopify.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 13-Jan-2020..
        """
        res, instance = self.get_basic_info("shopify_odoo_webhook_for_orders_partially_updated")
        if not res:
            return

        _logger.info("UPDATE ORDER WEBHOOK call for order: %s" % res.get("name"))

        fulfillment_status = res.get("fulfillment_status") or "unfulfilled"
        if request.env["sale.order"].sudo().search_read([("shopify_instance_id", "=", instance.id),
                                                         ("shopify_order_id", "=", res.get("id")),
                                                         ("shopify_order_number", "=",
                                                          res.get("order_number"))],
                                                        ["id"]):
            request.env["sale.order"].sudo().process_shopify_order_via_webhook(res, instance, True)
        elif fulfillment_status in ["fulfilled", "unfulfilled"]:
            res["fulfillment_status"] = fulfillment_status
            request.env["sale.order"].sudo().process_shopify_order_via_webhook(res, instance)
        return

    def get_basic_info(self, route):
        """
        This method is used return basic info. It will return response and instance.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 10-Jan-2020..
        """
        res = request.jsonrequest
        host = request.httprequest.headers.get("X-Shopify-Shop-Domain")
        instance = request.env["shopify.instance.ept"].sudo().with_context(
            active_test=False).search([("shopify_host", "ilike", host)], limit=1)

        webhook = request.env["shopify.webhook.ept"].sudo().search(
            [("delivery_url", "ilike", route), ("instance_id", "=", instance.id)],
            limit=1)

        if not instance.active or not webhook.state == "active":
            _logger.info("The method is skipped. It appears the instance:%s is not active or that "
                         "the webhook %s is not active." % (instance.name, webhook.webhook_name))
            res = False
        return res, instance
