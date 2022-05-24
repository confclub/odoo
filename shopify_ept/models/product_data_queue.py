# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import time
import json
import logging
import re
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .. import shopify
from ..shopify.pyactiveresource.connection import ClientError

_logger = logging.getLogger("Shopify")


class ShopifyProductDataQueue(models.Model):
    _name = "shopify.product.data.queue.ept"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Shopify Product Data Queue"

    name = fields.Char(size=120)
    shopify_instance_id = fields.Many2one("shopify.instance.ept", string="Instance")
    state = fields.Selection([("draft", "Draft"), ("partially_completed", "Partially Completed"),
                              ("completed", "Completed"), ("failed", "Failed")], default="draft",
                             compute="_compute_queue_state", store=True, tracking=True)
    product_data_queue_lines = fields.One2many("shopify.product.data.queue.line.ept",
                                               "product_data_queue_id",
                                               string="Product Queue Lines")
    common_log_book_id = fields.Many2one("common.log.book.ept",
                                         help="""Related Log book which has all logs for current queue.""")
    common_log_lines_ids = fields.One2many(related="common_log_book_id.log_lines")
    queue_line_total_records = fields.Integer(string="Total Records",
                                              compute="_compute_queue_line_record")
    queue_line_draft_records = fields.Integer(string="Draft Records",
                                              compute="_compute_queue_line_record")
    queue_line_fail_records = fields.Integer(string="Fail Records",
                                             compute="_compute_queue_line_record")
    queue_line_done_records = fields.Integer(string="Done Records",
                                             compute="_compute_queue_line_record")
    queue_line_cancel_records = fields.Integer(string="Cancelled Records",
                                               compute="_compute_queue_line_record")
    created_by = fields.Selection([("import", "By Import Process"), ("webhook", "By Webhook")],
                                  help="Identify the process that generated a queue.",
                                  default="import")
    is_process_queue = fields.Boolean("Is Processing Queue", default=False)
    running_status = fields.Char(default="Running...")
    is_action_require = fields.Boolean(default=False)
    queue_process_count = fields.Integer(string="Queue Process Times",
                                         help="it is used know queue how many time processed")
    skip_existing_product = fields.Boolean(string="Do Not Update Existing Products")

    @api.depends("product_data_queue_lines.state")
    def _compute_queue_line_record(self):
        """This is used for count of total record of product queue line.
            @param : self
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 2/11/2019.
        """
        for product_queue in self:
            queue_lines = product_queue.product_data_queue_lines
            product_queue.queue_line_total_records = len(queue_lines)
            product_queue.queue_line_draft_records = len(
                queue_lines.filtered(lambda x: x.state == "draft"))
            product_queue.queue_line_fail_records = len(
                queue_lines.filtered(lambda x: x.state == "failed"))
            product_queue.queue_line_done_records = len(
                queue_lines.filtered(lambda x: x.state == "done"))
            product_queue.queue_line_cancel_records = len(
                queue_lines.filtered(lambda x: x.state == "cancel"))

    @api.depends("product_data_queue_lines.state")
    def _compute_queue_state(self):
        """
        Computes state from different states of queue lines.
        @author: Haresh Mori on Date 25-Dec-2019.
        """
        for record in self:
            if record.queue_line_total_records == record.queue_line_done_records + record.queue_line_cancel_records:
                record.state = "completed"
            elif record.queue_line_draft_records == record.queue_line_total_records:
                record.state = "draft"
            elif record.queue_line_total_records == record.queue_line_fail_records:
                record.state = "failed"
            else:
                record.state = "partially_completed"

    @api.model
    def create(self, vals):
        """This method used to create a sequence for synced shopify data.
            @param : self,vals
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 05/10/2019.
        """
        sequence_id = self.env.ref("shopify_ept.seq_product_queue_data").ids
        if sequence_id:
            record_name = self.env["ir.sequence"].browse(sequence_id).next_by_id()
        else:
            record_name = "/"
        vals.update({"name": record_name or ""})
        return super(ShopifyProductDataQueue, self).create(vals)

    def create_product_queues(self, instance, results, skip_existing_product, template_ids=""):
        """
        Creates product queues and adds queue lines in it.
        @author: Maulik Barad on Date 28-Aug-2020.
        @param instance: Shopify Instance.
        @param results: Response of Products from shopify.
        @param template_ids: List of ids of templates.
        @return: List of Product queues.
        """
        product_queue_list = []
        bus_bus_obj = self.env["bus.bus"]
        count = 125
        for result in results:
            if count == 125:
                product_queue = self.shopify_create_product_queue(instance, skip_existing_product=skip_existing_product)
                product_queue_list.append(product_queue.id)
                message = "Product Queue Created {}".format(product_queue.name)
                bus_bus_obj.sendone((self._cr.dbname, "res.partner", self.env.user.partner_id.id),
                                    {"type": "simple_notification", "title": "Shopify Connector",
                                     "message": message, "sticky": False, "warning": True})
                _logger.info(message)
                count = 0
                if template_ids:
                    product_queue.message_post(body="%s products are not imported" % (",".join(template_ids)))
            self.shopify_create_product_data_queue_line(result, instance, product_queue)
            count = count + 1
        self._cr.commit()
        return product_queue_list

    def shopify_create_product_data_queue(self, instance, skip_existing_product=False, template_ids=""):
        """
        This method used to create a product data queue while syncing product from Shopify to Odoo.
        @author: Maulik Barad on Date 28-Aug-2020.
        @return: List of Product queues.
        """
        instance.connect_in_shopify()
        product_queue_list = []
        if template_ids:
            # Below one line is used to find only character values from template ids.
            re.findall("[a-zA-Z]+", template_ids)
            if len(template_ids.split(",")) <= 100:
                # The template_ids is a list of all template ids which response did not given by
                # shopify.
                template_ids = list(set(re.findall(re.compile(r"(\d+)"), template_ids)))
                results = shopify.Product().find(ids=",".join(template_ids))
                if results:
                    _logger.info(
                        "Length of Shopify Products %s import from instance : %s" % (len(results), instance.name))
                    template_ids = [template_id.strip() for template_id in template_ids]
                    # Below process to identify which id response did not give by Shopify.
                    [template_ids.remove(str(result.id)) for result in results if str(result.id) in template_ids]
                    product_queue_list += self.create_product_queues(instance, results, False, template_ids)
            else:
                raise UserError(_("Please enter the product template ids 100 or less"))
        else:
            if not instance.shopify_last_date_product_import:
                results = shopify.Product().find(limit=250)
            else:
                results = shopify.Product().find(updated_at_min=instance.shopify_last_date_product_import, limit=250)

            product_queue_list += self.create_product_queues(instance, results, skip_existing_product)

            if len(results) >= 250:
                product_queue_list += self.shopify_list_all_products(instance, results, skip_existing_product)
            if results:
                instance.shopify_last_date_product_import = datetime.now()
        if not results:
            _logger.info("No Products found to be imported from Shopify.")
            return False

        return product_queue_list

    def shopify_list_all_products(self, instance, result, skip_existing_product):
        """This method used to call the page wise data of product to import from Shopify to Odoo.
            @param : self,result
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 14/10/2019.
            Modify on date 27/12/2019 Taken pagination changes.
        """
        product_queue_list = []
        catch = ""
        while result:
            page_info = ""
            link = shopify.ShopifyResource.connection.response.headers.get("Link")
            if not link or not isinstance(link, str):
                return product_queue_list
            for page_link in link.split(","):
                if page_link.find("next") > 0:
                    page_info = page_link.split(";")[0].strip("<>").split("page_info=")[1]
                    try:
                        result = shopify.Product().find(page_info=page_info, limit=250)
                    except ClientError as error:
                        if hasattr(error, "response"):
                            if error.response.code == 429 and error.response.msg == "Too Many Requests":
                                time.sleep(5)
                                result = shopify.Product().find(page_info=page_info, limit=250)
                    except Exception as error:
                        raise UserError(error)
                    if result:
                        product_queue_list += self.create_product_queues(instance, result, skip_existing_product)
            if catch == page_info:
                break
        return product_queue_list

    def shopify_create_product_queue(self, instance, created_by="import", skip_existing_product=False):
        """
        This method used to create a product queue as per the split requirement of the
        queue. It is used for process the queue manually.
        @param instance: Shopify Instance.
        @param created_by: By which process, we are creating the queue.
        @author: Maulik Barad on Date 28-Aug-2020.
        """
        product_queue_vals = {
            "shopify_instance_id": instance and instance.id or False,
            "created_by": created_by,
            "skip_existing_product": skip_existing_product
        }
        return self.create(product_queue_vals)

    def shopify_create_product_data_queue_line(self, result, instance, product_data_queue):
        """
        This method used to create a product data queue line.
        @param result: Response of a product from shopify.
        @param instance: Shopify Instance.
        @param product_data_queue: Product data queue to attach the queue line with.
        @author: Maulik Barad on Date 01-Sep-2020.
        """
        product_data_queue_line_obj = self.env["shopify.product.data.queue.line.ept"]
        product_queue_line_vals = {}

        # No need to convert the response into dictionary, when response is coming from webhook.
        if not isinstance(result, dict):
            result = result.to_dict()
        data = json.dumps(result)
        product_queue_line_vals.update({"product_data_id": result.get("id"),
                                        "shopify_instance_id": instance and instance.id or False,
                                        "name": result.get("title"),
                                        "synced_product_data": data,
                                        "product_data_queue_id": product_data_queue and product_data_queue.id or False,
                                        })
        product_data_queue_line_obj.create(product_queue_line_vals)
        return True

    def create_schedule_activity_for_product(self, queue_line, from_sale=False):
        """
        author: Bhavesh Jadav 13/12/2019 for create schedule activity will product has extra attribute
        queue_line: is use for order queue_line or product queue_line
        from_sale:is use for identify its from sale process or product process
        """
        mail_activity_obj = self.env['mail.activity']
        ir_model_obj = self.env['ir.model']
        if from_sale:
            queue_id = queue_line.shopify_order_data_queue_id
            model_id = ir_model_obj.search([('model', '=', 'shopify.order.data.queue.ept')])
            data_ref = queue_line.shopify_order_id
            note = 'Your order has not been imported because of the product of order Has a new attribute Shopify ' \
                   'Order Reference : %s' % data_ref
        else:
            queue_id = queue_line.product_data_queue_id
            model_id = ir_model_obj.search([('model', '=', 'shopify.product.data.queue.ept')])
            data_ref = queue_line.product_data_id
            note = 'Your product was not synced because you tried to add new attribute | Product Data Reference ' \
                   ': %s' % data_ref

        activity_type_id = queue_id and queue_id.shopify_instance_id.shopify_activity_type_id.id
        date_deadline = datetime.strftime(
            datetime.now() + timedelta(days=int(queue_id.shopify_instance_id.shopify_date_deadline)), "%Y-%m-%d")
        if queue_id:
            note_2 = "<p>" + note + '</p>'
            for user_id in queue_id.shopify_instance_id.shopify_user_ids:
                mail_activity = mail_activity_obj.search(
                    [('res_model_id', '=', model_id.id), ('user_id', '=', user_id.id), ('res_name', '=', queue_id.name),
                     ('activity_type_id', '=', activity_type_id)])
                duplicate_note = mail_activity.filtered(lambda x: x.note == note_2)
                if not mail_activity or not duplicate_note:
                    vals = {'activity_type_id': activity_type_id,
                            'note': note,
                            'res_id': queue_id.id,
                            'user_id': user_id.id or self._uid,
                            'res_model_id': model_id.id,
                            'date_deadline': date_deadline}
                    try:
                        mail_activity_obj.create(vals)
                    except Exception as error:
                        _logger.info("Couldn't create schedule activity :%s" % str(error))
        return True

    def create_shopify_product_queue_from_webhook(self, product_data, instance):
        """
        This method used to create a product queue and its line from webhook response and
        also process it.
        @author: Dipak Gogiya on Date 10-Jan-2020.
        """
        product_data_queue = self.search([("created_by", "=", "webhook"), ("state", "=", "draft"),
                                          ("shopify_instance_id", "=", instance.id)])
        if product_data_queue:
            message = "Product %s added into Queue %s." % (product_data.get("id"), product_data_queue.name)
        else:
            product_data_queue = self.shopify_create_product_queue(instance, "webhook")
            message = "Product Queue %s created." % product_data_queue.name
        _logger.info(message)

        self.shopify_create_product_data_queue_line(product_data, instance, product_data_queue)

        if len(self.product_data_queue_lines) == 50:
            product_data_queue.product_data_queue_lines.process_product_queue_line_data()
            _logger.info("Processed product {0} of {1} via Webhook Successfully.".format(product_data.get("id"),
                                                                                         instance.name))
        return True
