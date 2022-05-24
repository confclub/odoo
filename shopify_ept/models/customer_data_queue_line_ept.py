# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import json
import logging
from datetime import datetime

from odoo import models, fields, api

_logger = logging.getLogger("Shopify")


class ShopifyCustomerDataQueueLineEpt(models.Model):
    _name = "shopify.customer.data.queue.line.ept"
    _description = "Shopify Synced Customer Data Line"

    state = fields.Selection([("draft", "Draft"), ("failed", "Failed"), ("done", "Done"),
                              ("cancel", "Cancelled")], default="draft")
    shopify_synced_customer_data = fields.Char(string="Shopify Synced Data")
    shopify_customer_data_id = fields.Text(string="Customer ID")
    synced_customer_queue_id = fields.Many2one("shopify.customer.data.queue.ept",
                                               string="Shopify Customer",
                                               ondelete="cascade")
    last_process_date = fields.Datetime()
    shopify_instance_id = fields.Many2one("shopify.instance.ept", string="Instance")
    common_log_lines_ids = fields.One2many("common.log.lines.ept",
                                           "shopify_customer_data_queue_line_id",
                                           help="Log lines created against which line.")
    name = fields.Char(string="Customer", help="Shopify Customer Name")

    def shopify_create_multi_queue(self, customer_queue_id, customer_ids):
        """
        Create customer queue and queue line as per the requirement.
        @author: Angel Patel @Emipro Technologies Pvt. Ltd on date 23/10/2019.
        :Task ID: 157065
        :param customer_queue_id:
        :param customer_ids:
        :return: True
        """
        if customer_queue_id:
            for result in customer_ids:
                result = result.to_dict()
                self.shopify_customer_data_queue_line_create(result, customer_queue_id)
        return True

    def shopify_customer_data_queue_line_create(self, result, customer_queue_id):
        """
        This method is used for create customer queue line using the result param and customer_queue_id.
        :param result:
        :param customer_queue_id:
        @author: Angel Patel @Emipro Technologies Pvt. Ltd on date 13/01/2020.
        """
        synced_shopify_customers_line_obj = self.env["shopify.customer.data.queue.line.ept"]
        name = "%s %s" % (result.get("first_name") or "", result.get("last_name") or "")
        customer_id = result.get("id")
        data = json.dumps(result)
        line_vals = {
            "synced_customer_queue_id": customer_queue_id.id,
            "shopify_customer_data_id": customer_id or "",
            "name": name.strip(),
            "shopify_synced_customer_data": data,
            "shopify_instance_id": self.shopify_instance_id.id,
            "last_process_date": datetime.now(),
        }
        return synced_shopify_customers_line_obj.create(line_vals)

    @api.model
    def sync_shopify_customer_into_odoo(self):
        """
        Change the queue and queue line record state using this compute method
        :author: Angel Patel @Emipro Technologies Pvt.Ltd on date 02/11/2019.
        :Task ID: 157065
        """
        shopify_customer_queue_obj = self.env["shopify.customer.data.queue.ept"]
        common_log_book_obj = self.env["common.log.book.ept"]
        ir_model_obj = self.env["ir.model"]
        customer_queue_ids = []

        query = """select queue.id
            from shopify_customer_data_queue_line_ept as queue_line
            inner join shopify_customer_data_queue_ept as queue on queue_line.synced_customer_queue_id = queue.id
            where queue_line.state='draft' and queue.is_action_require = 'False'
            ORDER BY queue_line.create_date ASC limit 500"""
        self._cr.execute(query)
        customer_data_queue_list = self._cr.fetchall()
        if not customer_data_queue_list:
            return True

        for customer_data_queue_id in customer_data_queue_list:
            if customer_data_queue_id[0] not in customer_queue_ids:
                customer_queue_ids.append(customer_data_queue_id[0])

        queues = shopify_customer_queue_obj.browse(customer_queue_ids)
        for queue in queues:
            results = queue.synced_customer_queue_line_ids.filtered(lambda x: x.state == "draft")

            queue.queue_process_count += 1
            if queue.queue_process_count > 3:
                queue.is_action_require = True
                note = "<p>Need to process this customer queue manually.There are 3 attempts been made by " \
                       "automated action to process this queue,<br/>- Ignore, if this queue is already processed.</p>"
                queue.message_post(body=note)
                if queue.shopify_instance_id.is_shopify_create_schedule:
                    model_id = ir_model_obj.search([("model", "=", "shopify.customer.data.queue.ept")]).id
                    common_log_book_obj.create_crash_queue_schedule_activity(queue, model_id, note)
                continue
            self._cr.commit()
            results.process_customer_queue_lines()
        return True

    def process_customer_queue_lines(self):
        """
        This method process the queue lines.
        """
        shopify_partner_obj = self.env["shopify.res.partner.ept"]
        common_log_book_obj = self.env["common.log.book.ept"]
        queues = self.synced_customer_queue_id

        for queue in queues:
            instance = queue.shopify_instance_id
            if not instance.active:
                _logger.info("Instance '{}' is not active.".format(instance.name))
                return True

            if queue.common_log_book_id:
                log_book_id = queue.common_log_book_id
            else:
                model_id = common_log_book_obj.log_lines.get_model_id("res.partner")
                log_book_id = common_log_book_obj.create({"type": "import",
                                                          "module": "shopify_ept",
                                                          "shopify_instance_id": instance.id,
                                                          "model_id": model_id})
                self.env.cr.execute("""update shopify_product_data_queue_ept set is_process_queue = False where 
                is_process_queue = True""")
                self._cr.commit()

            commit_count = 0
            for line in self:
                commit_count += 1
                if commit_count == 10:
                    queue.is_process_queue = True
                    self._cr.commit()
                    commit_count = 0

                customer_data = json.loads(line.shopify_synced_customer_data)
                main_partner = shopify_partner_obj.shopify_create_contact_partner(customer_data, instance, line,
                                                                                  log_book_id)
                if main_partner:
                    for address in customer_data.get("addresses"):
                        if address.get("default"):
                            continue
                        shopify_partner_obj.shopify_create_or_update_address(address, instance, main_partner)

                    line.update({"state": "done", "last_process_date": datetime.now()})
                else:
                    line.update({"state": "failed", "last_process_date": datetime.now()})
                queue.is_process_queue = False

            queue.common_log_book_id = log_book_id
            _logger.info("Customer Queue %s is processed." % queue.name)
            if log_book_id and not log_book_id.log_lines:
                log_book_id.unlink()
        return True
