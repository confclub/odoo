# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo import models, fields
from .. import shopify

_logger = logging.getLogger("Shopify")


class ShopifyProductDataQueueLineEpt(models.Model):
    _name = "shopify.product.data.queue.line.ept"
    _description = "Shopify Product Data Queue Line"

    shopify_instance_id = fields.Many2one("shopify.instance.ept", string="Instance")
    last_process_date = fields.Datetime()
    synced_product_data = fields.Text()
    product_data_id = fields.Char()
    state = fields.Selection([("draft", "Draft"), ("failed", "Failed"), ("done", "Done"),
                              ("cancel", "Cancelled")],
                             default="draft")
    product_data_queue_id = fields.Many2one("shopify.product.data.queue.ept", required=True,
                                            ondelete="cascade", copy=False)
    common_log_lines_ids = fields.One2many("common.log.lines.ept",
                                           "shopify_product_data_queue_line_id",
                                           help="Log lines created against which line.")
    name = fields.Char(string="Product", help="It contain the name of product")

    def auto_import_product_queue_line_data(self):
        """
        This method used to process synced shopify product data in batch of 100 queue lines.
        @author: Maulik Barad on Date 31-Aug-2020.
        """
        product_data_queue_obj = self.env["shopify.product.data.queue.ept"]
        ir_model_obj = self.env["ir.model"]
        common_log_book_obj = self.env["common.log.book.ept"]

        query = """select queue.id
                from shopify_product_data_queue_line_ept as queue_line
                inner join shopify_product_data_queue_ept as queue on queue_line.product_data_queue_id = queue.id
                where queue_line.state='draft' and queue.is_action_require = 'False'
                ORDER BY queue_line.create_date ASC limit 1"""
        self._cr.execute(query)
        product_data_queue_id = self._cr.fetchone()
        if not product_data_queue_id:
            return

        queue = product_data_queue_obj.browse(product_data_queue_id)
        product_data_queue_line_ids = queue.product_data_queue_lines

        # For counting the queue crashes and creating schedule activity for the queue.
        queue.queue_process_count += 1
        if queue.queue_process_count > 3:
            queue.is_action_require = True
            note = "<p>Need to process this product queue manually.There are 3 attempts been made by " \
                   "automated action to process this queue,<br/>- Ignore, if this queue is already processed.</p>"
            queue.message_post(body=note)
            if queue.shopify_instance_id.is_shopify_create_schedule:
                model_id = ir_model_obj.search([("model", "=", "shopify.product.data.queue.ept")]).id
                common_log_book_obj.create_crash_queue_schedule_activity(queue, model_id, note)
            return

        self._cr.commit()
        product_data_queue_line_ids.process_product_queue_line_data()
        return

    def process_product_queue_line_data(self):
        """
        This method processes product queue lines.
        @author: Maulik Barad on Date 31-Aug-2020.
        """
        shopify_product_template_obj = self.env["shopify.product.template.ept"]
        common_log_book_obj = self.env["common.log.book.ept"]
        model_id = common_log_book_obj.log_lines.get_model_id("shopify.product.template.ept")

        queue_id = self.product_data_queue_id if len(self.product_data_queue_id) == 1 else False

        if queue_id:
            shopify_instance = queue_id.shopify_instance_id
            if not shopify_instance.active:
                _logger.info("Instance '{}' is not active.".format(shopify_instance.name))
                return True
            if queue_id.common_log_book_id:
                log_book_id = queue_id.common_log_book_id
            else:
                log_book_id = common_log_book_obj.create({"type": "import",
                                                          "module": "shopify_ept",
                                                          "shopify_instance_id": shopify_instance.id,
                                                          "model_id": model_id,
                                                          "active": True})
            self.env.cr.execute(
                """update shopify_product_data_queue_ept set is_process_queue = False where is_process_queue = True""")
            self._cr.commit()
            commit_count = 0
            for product_queue_line in self:
                commit_count += 1
                if commit_count == 10:
                    queue_id.is_process_queue = True
                    self._cr.commit()
                    commit_count = 0
                # Loop on Products
                shopify_product_template_obj.shopify_sync_products(product_queue_line,
                                                                   False,
                                                                   shopify_instance,
                                                                   log_book_id)
                queue_id.is_process_queue = False
            queue_id.common_log_book_id = log_book_id
            if queue_id.common_log_book_id and not queue_id.common_log_book_id.log_lines:
                queue_id.common_log_book_id.unlink()
        return True

    def replace_product_response(self):
        """
        This method used to replace the product data response in the failed queue line. It will
        call from the product queue line button.
        @author: Haresh Mori @Emipro Technologies Pvt.Ltd on date 21/1/2020.
        """
        instance = self.shopify_instance_id
        if not instance.active:
            _logger.info("Instance '{}' is not active.".format(instance.name))
            return True
        instance.connect_in_shopify()
        if not self.product_data_id:
            return True
        result = shopify.Product().find(self.product_data_id)
        result = result.to_dict()
        data = json.dumps(result)
        self.write({"synced_product_data": data, "state": "draft"})
        self._cr.commit()
        self.process_product_queue_line_data()
        return True
