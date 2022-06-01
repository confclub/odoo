# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import time
import pytz
import re
import logging
from odoo import models, fields, api, _
from .. import shopify
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from ..shopify.pyactiveresource.connection import ClientError

utc = pytz.utc

_logger = logging.getLogger("Shopify")

class ShopifyOrderDataQueueEpt(models.Model):
    _name = "shopify.order.data.queue.ept"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Shopify Order Data Queue"

    name = fields.Char(help="Sequential name of imported order.", copy=False)
    shopify_instance_id = fields.Many2one('shopify.instance.ept', string='Instance',
                                          help="Order imported from this Shopify Instance.")
    state = fields.Selection([('draft', 'Draft'), ('partially_completed', 'Partially Completed'),
                              ('completed', 'Completed'), ('failed', 'Failed')], tracking=True,
                             default='draft', copy=False, compute="_compute_queue_state",
                             store=True)
    shopify_order_common_log_book_id = fields.Many2one("common.log.book.ept", help="""Related Log book which has
                                                                    all logs for current queue.""")
    shopify_order_common_log_lines_ids = fields.One2many(
            related="shopify_order_common_log_book_id.log_lines")
    order_data_queue_line_ids = fields.One2many("shopify.order.data.queue.line.ept",
                                                "shopify_order_data_queue_id")
    order_queue_line_total_record = fields.Integer(string='Total Records',
                                                   compute='_compute_order_queue_line_record')
    order_queue_line_draft_record = fields.Integer(string='Draft Records',
                                                   compute='_compute_order_queue_line_record')
    order_queue_line_fail_record = fields.Integer(string='Fail Records',
                                                  compute='_compute_order_queue_line_record')
    order_queue_line_done_record = fields.Integer(string='Done Records',
                                                  compute='_compute_order_queue_line_record')

    order_queue_line_cancel_record = fields.Integer(string='Cancel Records',
                                                    compute='_compute_order_queue_line_record')
    created_by = fields.Selection([("import", "By Manually Import Process"), ("webhook", "By Webhook"),
                                   ("scheduled_action", "By Scheduled Action")],
                                  help="Identify the process that generated a queue.", default="import")
    is_process_queue = fields.Boolean('Is Processing Queue', default=False)
    running_status = fields.Char(default="Running...")
    # order_log_lines = fields.One2many('common.log.lines.ept', 'order_queue_line_id', "log Lines")
    queue_process_count = fields.Integer(string="Queue Process Times",
                                         help="it is used know queue how many time processed")
    is_action_require = fields.Boolean(default=False, help="it is used  to find the action require queue")

    @api.depends('order_data_queue_line_ids.state')
    def _compute_queue_state(self):
        """
        Computes state from different states of queue lines.
        @author: Haresh Mori on Date 25-Dec-2019.
        """
        for record in self:
            if record.order_queue_line_total_record == record.order_queue_line_done_record + record.order_queue_line_cancel_record:
                record.state = "completed"
            elif record.order_queue_line_draft_record == record.order_queue_line_total_record:
                record.state = "draft"
            elif record.order_queue_line_total_record == record.order_queue_line_fail_record:
                record.state = "failed"
            else:
                record.state = "partially_completed"

    @api.depends('order_data_queue_line_ids.state')
    def _compute_order_queue_line_record(self):
        """This is used for count of total records of order queue lines.
            @param : self
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 2/11/2019.
        """
        for order_queue in self:
            queue_lines = order_queue.order_data_queue_line_ids
            order_queue.order_queue_line_total_record = len(queue_lines)
            order_queue.order_queue_line_draft_record = len(queue_lines.filtered(lambda x:x.state == "draft"))
            order_queue.order_queue_line_done_record = len(queue_lines.filtered(lambda x:x.state == "done"))
            order_queue.order_queue_line_fail_record = len(queue_lines.filtered(lambda x:x.state == "failed"))
            order_queue.order_queue_line_cancel_record = len(queue_lines.filtered(lambda x:x.state == "cancel"))

    @api.model
    def create(self, vals):
        """This method used to create a sequence for Order Queue Data.
            @param : self,vals
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 04/11/2019.
        """
        sequence_id = self.env.ref('shopify_ept.seq_order_queue_data').ids
        if sequence_id:
            record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
        else:
            record_name = '/'
        vals.update({'name':record_name or ''})
        return super(ShopifyOrderDataQueueEpt, self).create(vals)

    def import_order_cron_action(self, ctx={}):
        if not ctx:
            ctx['shopify_instance_id'] = self.env['shopify.instance.ept'].search([], limit=1).id
        instance_id = ctx.get('shopify_instance_id')
        instance = self.env['shopify.instance.ept'].browse(instance_id)
        from_date = instance.last_date_order_import
        to_date = datetime.now()
        if not from_date:
            from_date = to_date - timedelta(3)

        self.shopify_create_order_data_queues(instance, from_date, to_date, created_by="scheduled_action",
                                              order_type="unshipped")
        return

    def convert_dates_by_timezone(self, instance, from_date, to_date):
        """
        This method converts the dates by timezone of the Shopify store to import orders.
        @param instance: Shopify Instance.
        @param from_date: From date for importing orders.
        @param to_date: To date for importing orders.
        @author: Maulik Barad on Date 28-Sep-2020.
        """
        if not instance.shopify_store_time_zone:
            shop_id = shopify.Shop.current()
            shop_detail = shop_id.to_dict()
            instance.write({'shopify_store_time_zone':shop_detail.get('iana_timezone')})
            self._cr.commit()
        from_date = pytz.utc.localize(from_date).astimezone(pytz.timezone(instance.shopify_store_time_zone or
                                                                          'UTC')).strftime('%Y-%m-%dT%H:%M:%S%z')
        to_date = pytz.utc.localize(to_date).astimezone(pytz.timezone(instance.shopify_store_time_zone or
                                                                      'UTC')).strftime('%Y-%m-%dT%H:%M:%S%z')
        return from_date, to_date

    def shopify_create_order_data_queues(self, instance, from_date, to_date, created_by="import",
                                         order_type="unshipped"):
        """
        This method used to create order data queues.
        @param : self, instance,  from_date, to_date, created_by, order_type
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 06/11/2019.
        Task Id : 157350
        @change: Maulik Barad on Date 10-Sep-2020.
        """
        start = time.time()
        order_data_queue_line_obj = self.env["shopify.order.data.queue.line.ept"]
        order_queues = []
        order_type
        instance.connect_in_shopify()

        api_from_date, api_to_date = self.convert_dates_by_timezone(instance, from_date, to_date)

        try:
            order_ship_ids = shopify.Order().find(status="any",
                                             fulfillment_status="shipped",
                                             updated_at_min=api_from_date,
                                             updated_at_max=api_to_date, limit=250)

            order_unship_ids = shopify.Order().find(status="any",
                                                  fulfillment_status="unshipped",
                                                  updated_at_min=api_from_date,
                                                  updated_at_max=api_to_date, limit=250)


            order_partial_ids = shopify.Order().find(status="any",
                                                  fulfillment_status="partial",
                                                  updated_at_min=api_from_date,
                                                  updated_at_max=api_to_date, limit=250)

        except Exception as error:
            raise UserError(error)

        if order_partial_ids:
            order_queues = order_data_queue_line_obj.create_order_data_queue_line(order_partial_ids,
                                                                                  instance,
                                                                                  created_by)

        if order_ship_ids:
            order_queues = order_data_queue_line_obj.create_order_data_queue_line(order_ship_ids,
                                                                                  instance,
                                                                                  created_by)
        #     if len(order_ship_ids) >= 250:
        #         order_ship_ids, order_queue_list = self.list_all_orders(order_ship_ids, instance, created_by,
        #                                                            'shipped')
        #         order_queues += order_queue_list
        #
        if order_unship_ids:
            order_data_queue_line_obj.create_order_data_queue_line(order_unship_ids,
                                                                   instance,
                                                                   created_by)
            # self.process_shopify_orders_directly(order_unship_ids, instance)
            # instance.last_date_order_import = to_date - timedelta(days=2)


        # else:
        #     instance.last_shipped_order_import_date = to_date - timedelta(days=2)

        end = time.time()
        _logger.info("Imported Orders in %s seconds." % (str(end - start)))
        return order_queues

    def process_shopify_orders_directly(self, order_data, instance):
        """
        This method processes the order data directly, without creating queue lines.
        @param order_data:
        @param instance:
        """
        sale_order_obj = self.env["sale.order"]
        common_log_book_obj = self.env["common.log.book.ept"]
        common_log_lines_obj = self.env["common.log.lines.ept"]

        model_id = common_log_lines_obj.get_model_id("sale.order")
        log_book = common_log_book_obj.create({"type":"import",
                                               "module":"shopify_ept",
                                               "shopify_instance_id":instance.id,
                                               "model_id":model_id})
        order_ids = sale_order_obj.import_shopify_orders(order_data, log_book, is_queue_line=False)
        if not log_book.log_lines:
            log_book.unlink()
        return order_ids

    def list_all_orders(self, result, instance, created_by, order_type):
        """
        This method used to get the list of orders from Shopify to Odoo.
        @param : self, result, instance, created_by, order_type
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 06/11/2019.
        Task_id : 157350
        Modify on date 27/12/2019 Taken pagination changes
        @change : Maulik Barad on Date 10-Sep-2020.
        """
        order_data_queue_line_obj = self.env["shopify.order.data.queue.line.ept"]
        sum_order_list = []
        order_queue_list = []
        catch = ""

        while result:
            page_info = ""
            if order_type == "unshipped":
                sum_order_list += result
            link = shopify.ShopifyResource.connection.response.headers.get('Link')
            if not link or not isinstance(link, str):
                return sum_order_list, order_queue_list

            for page_link in link.split(','):
                if page_link.find('next') > 0:
                    page_info = page_link.split(';')[0].strip('<>').split('page_info=')[1]
                    try:
                        result = shopify.Order().find(limit=250, page_info=page_info)
                    except ClientError as e:
                        if hasattr(e, "response"):
                            if e.response.code == 429 and e.response.msg == "Too Many Requests":
                                time.sleep(5)
                                result = shopify.Order().find(limit=250, page_info=page_info)
                    except Exception as e:
                        raise UserError(e)
                    if result and order_type == "shipped":
                        order_queues = order_data_queue_line_obj.create_order_data_queue_line(result, instance,
                                                                                              created_by)
                        order_queue_list += order_queues
            if catch == page_info:
                break
        return sum_order_list, order_queue_list

    def import_order_process_by_remote_ids(self, instance, order_ids):
        """
        This method is used for get a order from shopify based on order ids and create its queue and process it.
        :param instance: browsable object of shopify instance
        :param order_ids: It contain the comma separated ids of shopify orders and its type is String
        :return: It will return either True or False
        """
        sale_order_obj = self.env["sale.order"]
        common_log_book_obj = self.env["common.log.book.ept"]

        if order_ids:
            instance.connect_in_shopify()
            # Below one line is used to find only character values from order ids.
            re.findall("[a-zA-Z]+", order_ids)
            if len(order_ids.split(',')) <= 50:
                # order_ids_list is a list of all order ids which response did not given by shopify.
                order_ids_list = list(set(re.findall(re.compile(r"(\d+)"), order_ids)))
                results = shopify.Order().find(ids=','.join(order_ids_list), status='any')
                if results:
                    _logger.info('%s Shopify order(s) imported from instance : %s' % (
                        len(results), instance.name))
                    order_ids_list = [order_id.strip() for order_id in order_ids_list]
                    # Below process to identify which id response did not give by Shopify.
                    [order_ids_list.remove(str(result.id)) for result in results if str(result.id) in order_ids_list]
            else:
                raise UserError(_('Please enter the Order ids 50 or less'))
            if results:
                if order_ids_list:
                    _logger.warning("Orders are not found for ids :%s" % (str(order_ids_list)))
                model_id = common_log_book_obj.log_lines.get_model_id("sale.order")
                log_book_id = common_log_book_obj.create({"type":"import",
                                                          "module":"shopify_ept",
                                                          "shopify_instance_id":instance.id,
                                                          "model_id":model_id})
                sale_order_obj.import_shopify_orders(results, log_book_id, is_queue_line=False)
        return True
