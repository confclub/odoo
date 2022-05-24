# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
import time
import logging
logger = logging.getLogger('sale')
from odoo.exceptions import UserError


class quickbook_integration(models.Model):
    _inherit = "quickbook.integration"


    @api.model
    def refresh_access_token(self, cron=True):
        print ("refresh_access_token_schedularrrrrrrrrrrrrrrr111111")
        shop_ids = self.env['quickbook.integration'].search([])
        # print "shop_idsssssssssssssssssss",shop_ids
        # shop = shop_ids[0]
        # shop.refresh_token()
        # return True

        for shop in shop_ids:
            shop.refresh_token()
        return True


    @api.model
    def import_account_schedular(self, cron=True):
        print ("import_account_schedularrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_account()
        return True


    @api.model
    def import_taxes_schedular(self, cron=True):
        print ("import_taxxxxx_schedularrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_tax()
        return True


    @api.model
    def import_payment_method_schedular(self, cron=True):
        print ("import_payment_method_schedularrrrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_payment_method()
        return True


    @api.model
    def import_payment_term_schedular(self, cron=True):
        print ("import_payment_term_schedularrrrrrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_payment_term()
        return True


    @api.model
    def import_departments_schedular(self, cron=True):
        print ("import_departments_schedularrrrrrrrrrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_departments()
        return True


    @api.model
    def import_customers_schedular(self, cron=True):
        print ("import_customers_schedularrrrrrrrrrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_customer()
        return True


    @api.model
    def import_vendors_schedular(self, cron=True):
        print ("import_vendors_schedularrrrrrrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_vendor()
        return True


    @api.model
    def import_employees_schedular(self, cron=True):
        print ("import_emppppppppp_schedularrrrrrrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_employee()
        return True


    @api.model
    def import_prod_category_schedular(self, cron=True):
        print ("import_prod_category_schedularrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_category()
        return True


    @api.model
    def import_product_schedular(self, cron=True):
        print ("import_product_schedularrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_product()
        return True


    @api.model
    def import_product_inventory_schedular(self, cron=True):
        print ("import_product_inventory_schedulartrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_product_inventory()
        return True


    @api.model
    def import_orders_schedular(self, cron=True):
        print ("import_orders_schedularsssssssss")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_order()
        return True


    @api.model
    def import_purchase_orders_schedular(self, cron=True):
        print ("import_purchasesssss_orders_schedularsssssssss")
        shop_ids = self.env['quickbook.integration'].search([])
        print( "shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_purchase_order()
        return True


    @api.model
    def import_cust_invoices_schedular(self, cron=True):
        print ("import_cust_invoices_schedularsssssssssssssssssssss")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_invoice()
        return True


    @api.model
    def import_vend_bills_schedular(self, cron=True):
        print ("import_vend_bills_schedularssrrrrrrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_vendor_bill()
        return True


    @api.model
    def import_cust_payments_schedular(self, cron=True):
        print ("import_cust_payments_schedularrrrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_customer_payment()
        return True
        

    @api.model
    def import_vend_bills_payments_schedular(self, cron=True):
        print ("import_vend_bills_payments_schedularrrrrrrrrrrrrrr")
        shop_ids = self.env['quickbook.integration'].search([])
        print ("shop_idsssssssssssssssssss",shop_ids)
        for shop in shop_ids:
            shop.import_vendor_payment()
        return True





        