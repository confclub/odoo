# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .. import shopify
from ..shopify.pyactiveresource.connection import ForbiddenAccess

_logger = logging.getLogger("Shopify : ")


class ShopifyInstanceEpt(models.Model):
    _name = "shopify.instance.ept"
    _description = 'Shopify Instance'

    @api.model
    def _get_default_warehouse(self):
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.shopify_company_id.id)], limit=1,
                                                       order='id')
        return warehouse.id if warehouse else False

    @api.model
    def _default_stock_field(self):
        stock_field = self.env['ir.model.fields'].search(
            [('model_id.model', '=', 'product.product'), ('name', '=', 'virtual_available')],
            limit=1)
        return stock_field.id if stock_field else False

    @api.model
    def _default_discount_product(self):
        """
        Gives default discount product to set in imported shopify order.
        @author: Haresh Mori on Date 16-Dec-2019.
        """
        discount_product = self.env.ref('shopify_ept.shopify_discount_product') or False
        return discount_product

    @api.model
    def _default_shipping_product(self):
        """
        Sets default shipping product.
        @author: Maulik Barad on Date 01-Oct-2020.
        """
        shipping_product = self.env.ref('shopify_ept.shopify_shipping_product') or False
        return shipping_product

    def _count_all(self):
        for instance in self:
            instance.product_count = len(instance.product_ids)
            instance.sale_order_count = len(instance.sale_order_ids)
            instance.picking_count = len(instance.picking_ids)
            instance.invoice_count = len(instance.invoice_ids.filtered(lambda x: x.move_type == 'out_invoice'))
            instance.exported_product_count = len(instance.product_ids.filtered(lambda x: x.exported_in_shopify))
            instance.ready_to_export_product_count = len(
                instance.product_ids.filtered(lambda x: not x.exported_in_shopify))
            instance.published_product_count = len(
                instance.product_ids.filtered(lambda x: x.website_published != "unpublished"))
            instance.unpublished_product_count = len(
                instance.product_ids.filtered(lambda x: x.website_published == "unpublished"))
            instance.quotation_count = len(instance.sale_order_ids.filtered(lambda x: x.state in ['draft', 'sent']))
            instance.order_count = len(
                instance.sale_order_ids.filtered(lambda x: x.state not in ['draft', 'sent', 'cancel']))
            instance.risk_order_count = len(
                instance.sale_order_ids.filtered(lambda x: x.state == 'draft' and x.is_risky_order))

            instance.confirmed_picking_count = len(
                instance.picking_ids.filtered(lambda x: x.state == 'confirmed'))
            instance.assigned_picking_count = len(
                instance.picking_ids.filtered(lambda x: x.state == 'assigned'))
            instance.partially_available_picking_count = len(
                instance.picking_ids.filtered(lambda x: x.state == 'partially_available'))
            instance.done_picking_count = len(
                instance.picking_ids.filtered(lambda x: x.state == 'done'))
            instance.open_invoice_count = len(instance.invoice_ids.filtered(
                lambda x: x.state == 'posted' and x.move_type == 'out_invoice' and not x.payment_state == 'paid'))
            instance.paid_invoice_count = len(instance.invoice_ids.filtered(
                lambda x: x.state == 'posted' and x.payment_state in ['paid',
                                                                      'in_payment'] and x.move_type == 'out_invoice'))
            instance.refund_invoice_count = len(
                instance.invoice_ids.filtered(lambda x: x.move_type == 'out_refund'))

    name = fields.Char(size=120, string='Name', required=True)
    shopify_company_id = fields.Many2one('res.company', string='Company', required=True,
                                         default=lambda self: self.env.company)
    shopify_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', default=_get_default_warehouse,
                                           domain="[('company_id', '=',shopify_company_id)]",
                                           help="Selected Warehouse will be set in your Shopify "
                                                "orders.", required=True)
    shopify_pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
                                           help="1.During product sync operation, prices will be Imported/Exported using this Pricelist.\n"
                                                "2.During order sync operation, this pricelist "
                                                "will be set in the order if the order currency from store and the currency from the pricelist set here, matches.")

    shopify_order_prefix = fields.Char(size=10, string='Order Prefix',
                                       help="Enter your order prefix")
    shopify_api_key = fields.Char("API Key", required=True)
    shopify_password = fields.Char("Password", required=True)
    shopify_shared_secret = fields.Char("Secret Key", required=True)
    shopify_host = fields.Char("Host", required=True)
    shopify_last_date_customer_import = fields.Datetime(string="Last Customer Import",
                                                        help="it is used to store last import customer date")
    shopify_last_date_update_stock = fields.Datetime(string="Last Stock Update",
                                                     help="it is used to store last update inventory stock date")
    shopify_last_date_product_import = fields.Datetime(string="Last Product Import",
                                                       help="it is used to store last import product date")
    auto_import_product = fields.Boolean(string="Auto Create Product if not found?")
    shopify_sync_product_with = fields.Selection([('sku', 'Internal Reference(SKU)'),
                                                  ('barcode', 'Barcode'),
                                                  ('sku_or_barcode',
                                                   'Internal Reference or Barcode'),
                                                  ], string="Sync Product With", default='sku')
    update_category_in_odoo_product = fields.Boolean(string="Update Category In Odoo Product ?",
                                                     default=False)
    shopify_stock_field = fields.Many2one('ir.model.fields', string='Stock Field')
    last_date_order_import = fields.Datetime(string="Last Date Of Unshipped Order Import",
                                             help="Last date of sync orders from Shopify to Odoo")
    shopify_section_id = fields.Many2one('crm.team', 'Sales Team')
    is_use_default_sequence = fields.Boolean("Use Odoo Default Sequence?",
                                             help="If checked,Then use default sequence of odoo while create sale order.")
    # Account field
    shopify_store_time_zone = fields.Char("Store Time Zone",
                                          help='This field used to import order process')
    discount_product_id = fields.Many2one("product.product", "Discount",
                                          domain=[('type', '=', 'service')],
                                          default=_default_discount_product,
                                          help="This is used for set discount product in a sale order lines")

    apply_tax_in_order = fields.Selection(
        [("odoo_tax", "Odoo Default Tax Behaviour"), ("create_shopify_tax",
                                                      "Create new tax If Not Found")],
        copy=False, help=""" For Shopify Orders :- \n
                    1) Odoo Default Tax Behaviour - The Taxes will be set based on Odoo's
                                 default functional behaviour i.e. based on Odoo's Tax and Fiscal Position configurations. \n
                    2) Create New Tax If Not Found - System will search the tax data received 
                    from Shopify in Odoo, will create a new one if it fails in finding it.""")
    invoice_tax_account_id = fields.Many2one('account.account', string='Invoice Tax Account')
    credit_tax_account_id = fields.Many2one('account.account', string='Credit Tax Account')
    notify_customer = fields.Boolean("Notify Customer about Update Order Status?",
                                     help="If checked,Notify the customer via email about Update Order Status")
    color = fields.Integer(string='Color Index')

    # fields for kanban view
    product_ids = fields.One2many('shopify.product.template.ept', 'shopify_instance_id',
                                  string="Products")
    product_count = fields.Integer(compute='_count_all', string="Product")
    sale_order_ids = fields.One2many('sale.order', 'shopify_instance_id', string="Orders")
    sale_order_count = fields.Integer(compute='_count_all', string="Sale Order Count")
    picking_ids = fields.One2many('stock.picking', 'shopify_instance_id', string="Pickings")
    picking_count = fields.Integer(compute='_count_all', string="Picking")
    invoice_ids = fields.One2many('account.move', 'shopify_instance_id', string="Invoices")
    invoice_count = fields.Integer(compute='_count_all', string="Invoice")
    exported_product_count = fields.Integer(compute='_count_all', string="Exported Products")
    ready_to_export_product_count = fields.Integer(compute='_count_all', string="Ready For Export")
    published_product_count = fields.Integer(compute='_count_all', string="Published Product")
    unpublished_product_count = fields.Integer(compute='_count_all', string="#UnPublished Product")
    quotation_count = fields.Integer(compute='_count_all', string="Quotation")
    order_count = fields.Integer(compute='_count_all', string="Sales Orders")
    risk_order_count = fields.Integer(compute='_count_all', string="Risky Orders")
    confirmed_picking_count = fields.Integer(compute='_count_all', string="Confirm Picking")
    assigned_picking_count = fields.Integer(compute='_count_all', string="Assigned Pickings")
    partially_available_picking_count = fields.Integer(compute='_count_all',
                                                       string="Partially Available Picking")
    done_picking_count = fields.Integer(compute='_count_all', string="Done Picking")
    open_invoice_count = fields.Integer(compute='_count_all', string="Open Invoice")
    paid_invoice_count = fields.Integer(compute='_count_all', string="Paid Invoice")
    refund_invoice_count = fields.Integer(compute='_count_all', string="Refund Invoices")

    shopify_user_ids = fields.Many2many('res.users', 'shopify_instance_ept_res_users_rel',
                                        'res_config_settings_id', 'res_users_id',
                                        string='Responsible User')
    shopify_activity_type_id = fields.Many2one('mail.activity.type',
                                               string="Activity Type")
    shopify_date_deadline = fields.Integer('Deadline lead days',
                                           help="its add number of  days in schedule activity deadline date ")
    is_shopify_create_schedule = fields.Boolean("Create Schedule Activity ? ", default=False,
                                                help="If checked, Then Schedule Activity create on order data queues"
                                                     " will any queue line failed.")
    active = fields.Boolean("Active", default=True)
    sync_product_with_images = fields.Boolean("Sync Images?",
                                              help="Check if you want to import images along with "
                                                   "products",
                                              default=True)

    webhook_ids = fields.One2many("shopify.webhook.ept", "instance_id", "Webhooks")
    create_shopify_products_webhook = fields.Boolean("Manage Products via Webhooks",
                                                     help="True : It will create all product related webhooks.\nFalse : All product related webhooks will be deactivated.")

    create_shopify_customers_webhook = fields.Boolean("Manage Customers via Webhooks",
                                                      help="True : It will create all customer related webhooks.\nFalse : All customer related webhooks will be deactivated.")
    create_shopify_orders_webhook = fields.Boolean("Manage Orders via Webhooks",
                                                   help="True : It will create all order related webhooks.\nFalse : All "
                                                        "order related webhooks will be deactivated.")
    shopify_default_pos_customer_id = fields.Many2one("res.partner", "Default POS customer",
                                                      help="This customer will be set in POS order, when"
                                                           "customer is not found.")
    # Shopify Payout Report
    shopify_api_url = fields.Char(string="Payout API URL")
    transaction_line_ids = fields.One2many("shopify.payout.account.config.ept", "instance_id",
                                           string="Transaction Line")
    shopify_settlement_report_journal_id = fields.Many2one('account.journal',
                                                           string='Payout Report Journal')
    payout_last_import_date = fields.Date(string="Last Date of Payout Import")
    last_shipped_order_import_date = fields.Datetime(string="Last Date Of Shipped Order Import",
                                                     help="Last date of sync orders from Shopify to Odoo")
    is_instance_create_from_onboarding_panel = fields.Boolean(default=False)
    is_onboarding_configurations_done = fields.Boolean(default=False)
    shipping_product_id = fields.Many2one("product.product", domain=[('type', '=', 'service')],
                                          default=_default_shipping_product,
                                          help="This is used for set shipping product in a Carrier.")

    _sql_constraints = [('unique_host', 'unique(shopify_host)',
                         "Instance already exists for given host. Host must be Unique for the instance!")]

    @api.model
    def create(self, vals):
        """
        Inherited for creating generic POS customer.
        @author: Maulik Barad on date 25-Feb-2020.
        """
        if vals.get("shopify_host").endswith('/'):
            vals["shopify_host"] = vals.get("shopify_host").rstrip('/')

        res_partner_obj = self.env["res.partner"]
        customer_vals = {"name": "POS Customer(%s)" % vals.get("name"), "customer_rank": 1}
        customer = res_partner_obj.create(customer_vals)

        sales_team = self.create_sales_channel(vals.get('name'))

        vals.update({"shopify_default_pos_customer_id": customer.id, "shopify_section_id": sales_team.id})
        return super(ShopifyInstanceEpt, self).create(vals)

    def create_sales_channel(self, name):
        """
        Creates new sales team for Shopify instance.
        @author: Maulik Barad on Date 09-Jan-2019.
        """
        crm_team_obj = self.env['crm.team']
        vals = {
            'name': name,
            'use_quotations': True
        }
        return crm_team_obj.create(vals)

    def shopify_test_connection(self, vals={}):
        """This method used to check the connection between Odoo and Shopify.
            @param : self
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 04/10/2019.
        """
        self.connect_in_shopify(vals)
        try:
            shop_id = shopify.Shop.current()
        except ForbiddenAccess as e:
            if e.response.body:
                errors = json.loads(e.response.body.decode())
                raise UserError("%s\n%s\n%s" % (e.response.code, e.response.msg, errors.get("errors")))
        except Exception as e:
            raise UserError(e)
        shop_detail = shop_id.to_dict()
        self.write({"shopify_store_time_zone": shop_detail.get("iana_timezone")})
        title = _("Shopify")
        message = _("Connection Test Succeeded!")
        self.env['bus.bus'].sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
                                    {'type': 'simple_notification', 'title': title, 'message': message, 'sticky': False,
                                     'warning': True})
        return True

    def connect_in_shopify(self, vals={}):
        """
        This method used to connect with Odoo to Shopify.
        @param vals: Dictionary of api_key and password.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 07/10/2019.
        @change: Maulik Barad on Date 01-Oct-2020.
        """
        if vals:
            api_key = vals.get("shopify_api_key")
            password = vals.get("shopify_password")
        else:
            api_key = self.shopify_api_key
            password = self.shopify_password

        shop = self.shopify_host.split("//")
        if len(shop) == 2:
            shop_url = shop[0] + "//" + api_key + ":" + password + "@" + shop[1] + "/admin/api/2020-07"
        else:
            shop_url = "https://" + api_key + ":" + password + "@" + shop[0] + "/admin/api/2020-07"

        shopify.ShopifyResource.set_site(shop_url)
        return True

    def toggle_active(self):
        """
        Method overrided for archiving the instance from the action menu.
        @author: Maulik Barad on Date 06-Oct-2020.
        """
        for instance in self:
            instance.shopify_action_archive_unarchive()
        return True

    def shopify_action_archive_unarchive(self):
        """This method used to confirm the shopify instance.
            @param : self
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 07/10/2019.
        """
        domain = [("shopify_instance_id", "=", self.id)]
        shopify_template_obj = self.env["shopify.product.template.ept"]
        sale_auto_workflow_configuration_obj = self.env["sale.auto.workflow.configuration.ept"]
        shopify_payment_gateway_obj = self.env["shopify.payment.gateway.ept"]
        shopify_webhook_obj = self.env["shopify.webhook.ept"]
        shopify_location_obj = self.env["shopify.location.ept"]
        if self.active:
            activate = {"active": False}
            domain_for_webhook_location = [("instance_id", "=", self.id)]

            self.write(activate)
            self.change_auto_cron_status(self)
            shopify_webhook_obj.search(domain_for_webhook_location).unlink()
            shopify_location_obj.search(domain_for_webhook_location).write(activate)
        else:
            self.shopify_test_connection()
            activate = {"active": True}
            domain.append(("active", "=", False))
            self.write(activate)
            shopify_location_obj.import_shopify_locations(self)

        shopify_template_obj.search(domain).write(activate)
        sale_auto_workflow_configuration_obj.search(domain).write(activate)
        shopify_payment_gateway_obj.search(domain).write(activate)
        return True

    def change_auto_cron_status(self, instance):
        """
        After connect or disconnect the shopify instance disable all the Scheduled Actions.
        :param instance:
        :return:
        @author: Angel Patel @Emipro Technologies Pvt. Ltd.
        Task Id : 157716
        """
        try:
            stock_cron_exist = self.env.ref(
                'shopify_ept.ir_cron_shopify_auto_export_inventory_instance_%d' % instance.id)
        except:
            stock_cron_exist = False
        try:
            order_cron_exist = self.env.ref(
                'shopify_ept.ir_cron_shopify_auto_import_order_instance_%d' % instance.id)
        except:
            order_cron_exist = False
        try:
            order_status_cron_exist = self.env.ref(
                'shopify_ept.ir_cron_shopify_auto_update_order_status_instance_%d' % (
                    instance.id))
        except:
            order_status_cron_exist = False

        if stock_cron_exist:
            stock_cron_exist.write({'active': False})
        if order_cron_exist:
            order_cron_exist.write({'active': False})
        if order_status_cron_exist:
            order_status_cron_exist.write({'active': False})

    def cron_configuration_action(self):
        """
        Open wizard from "Configure Schedulers" button click.
        @author: Maulik Barad on Date 28-Sep-2020.
        """
        action = self.env.ref('shopify_ept.action_wizard_shopify_cron_configuration_ept').read()[0]
        action['context'] = {'shopify_instance_id': self.id}
        return action

    def action_redirect_to_ir_cron(self):
        """
        Redirect to ir.cron model with cron name like shopify
        @author: Angel Patel @Emipro Technologies Pvt. Ltd.
        Task Id : 157716
        :return:
        """
        action = self.env.ref('base.ir_cron_act').read()[0]
        action['domain'] = [('name', 'ilike', self.name)]
        return action

    def action_archive(self):
        self.shopify_action_archive_unarchive()
        # self.change_webhook_state()
        return super(ShopifyInstanceEpt, self).action_archive()

    def list_of_topic_for_webhook(self, event):
        """
        This method is prepare the list of all the event topic while the webhook create, and return that list
        :param event: having 'product' or 'customer' or 'order'
        :return: topic_list
        @author: Angel Patel on Date 17/01/2020.
        """
        topic_list = []
        if event == 'product':
            topic_list = ["products/update", "products/delete"]
        if event == 'customer':
            topic_list = ["customers/create", "customers/update"]
        if event == 'order':
            topic_list = ["orders/updated"]
        return topic_list

    def configure_shopify_product_webhook(self):
        """
        Creates or activates all product related webhooks, when it is True.
        Inactive all product related webhooks, when it is False.
        @author: Haresh Mori on Date 09-Jan-2020.
        :Modify by Angel Patel on date 17/01/2020, call list_of_topic_for_webhook method for get 'product' list events
        """
        topic_list = self.list_of_topic_for_webhook("product")
        self.configure_webhooks(topic_list)

    def configure_shopify_customer_webhook(self):
        """
        Creates or activates all customer related webhooks, when it is True.
        Inactive all customer related webhooks, when it is False.
        @author: Angel Patel on Date 10/01/2020.
        :Modify by Angel Patel on date 17/01/2020, call list_of_topic_for_webhook method for get 'customer' list events
        """
        topic_list = self.list_of_topic_for_webhook("customer")
        self.configure_webhooks(topic_list)

    def configure_shopify_order_webhook(self):
        """
        Creates or activates all order related webhooks, when it is True.
        Inactive all order related webhooks, when it is False.
        @author: Haresh Mori on Date 10/01/2020.
        :Modify by Angel Patel on date 17/01/2020, call list_of_topic_for_webhook method for get 'order' list events
        """
        topic_list = self.list_of_topic_for_webhook("order")
        self.configure_webhooks(topic_list)

    def configure_webhooks(self, topic_list):
        """
        Creates or activates all webhooks as per topic list, when it is True.
        Pauses all product related webhooks, when it is False.
        @author: Haresh Mori on Date 09/01/2020.
        """
        webhook_obj = self.env["shopify.webhook.ept"]

        resource = topic_list[0].split('/')[0]
        instance_id = self.id
        available_webhooks = webhook_obj.search(
            [("webhook_action", "in", topic_list), ("instance_id", "=", instance_id)])

        # self.refresh_webhooks(available_webhooks)

        if getattr(self, "create_shopify_%s_webhook" % resource):
            if available_webhooks:
                available_webhooks.write({'state': 'active'})
                _logger.info("{0} Webhooks are activated of instance '{1}'.".format(resource, self.name))
                topic_list = list(set(topic_list) - set(available_webhooks.mapped("webhook_action")))

            for topic in topic_list:
                webhook_obj.create({"webhook_name": self.name + "_" + topic.replace("/", "_"),
                                    "webhook_action": topic, "instance_id": instance_id})
                _logger.info("Webhook for '{0}' of instance '{1}' created.".format(topic, self.name))
        else:
            if available_webhooks:
                available_webhooks.write({'state': 'inactive'})
                _logger.info("{0} Webhooks are paused of instance '{1}'.".format(resource, self.name))

    def refresh_webhooks(self):
        """
        This method is used for delete record from the shopify.webhook.ept model record if webhook deleted from the shopify with some of the reasons.
        @author: Angel Patel@Emipro Technologies Pvt. Ltd on Date 15/01/2020.
        """
        self.connect_in_shopify()
        shopify_webhook = shopify.Webhook()
        responses = shopify_webhook.find()
        webhook_ids = []
        for webhook in responses:
            webhook_ids.append(str(webhook.id))
        _logger.info("Emipro-Webhook: Current webhook present in shopify is %s" % webhook_ids)
        webhook_obj = self.env['shopify.webhook.ept'].search(
            [('instance_id', '=', self.id), ('webhook_id', 'not in', webhook_ids)])
        _logger.info("Emipro-Webhook: Webhook not present in odoo is %s" % webhook_obj)
        if webhook_obj:
            for webhooks in webhook_obj:
                _logger.info("Emipro-Webhook: deleting the %s shopify.webhook.ept record" % webhooks.id)
                self._cr.execute("DELETE FROM shopify_webhook_ept WHERE id = %s", [webhooks.id], log_exceptions=False)
        _logger.info("Emipro-Webhook: refresh process done")
        return True

    def search_shopify_instance(self):
        """
            Usage : Search Shopify Instance
            @Task:   166992 - Shopify Onboarding panel
            @author: Dipak Gogiya, 26/09/2020
            :return: shopify.instance.ept()
        """
        company = self.env.company or self.env.user.company_id
        instance = self.search(
            [('is_instance_create_from_onboarding_panel', '=', True),
             ('is_onboarding_configurations_done', '=', False),
             ('shopify_company_id', '=', company.id)], limit=1, order='id desc')
        if not instance:
            instance = self.search([('shopify_company_id', '=', company.id),
                                    ('is_onboarding_configurations_done', '=', False)],
                                   limit=1, order='id desc')
            instance and instance.write({'is_instance_create_from_onboarding_panel': True})
        return instance

    def open_reset_credentials_wizard(self):
        """
        Open wizard for reset credentials.
        @author: Maulik Barad on Date 01-Oct-2020.
        """
        view_id = self.env.ref('shopify_ept.view_reset_credentials_form').id
        action = self.env.ref('shopify_ept.res_config_action_shopify_instance').read()[0]
        action.update({"name": "Reset Credentials",
                       "context": {'shopify_instance_id': self.id,
                                   "default_name": self.name,
                                   "default_shopify_host": self.shopify_host},
                       "view_id": (view_id, "Reset Credentials"),
                       "views": [(view_id, "form")]})
        return action
