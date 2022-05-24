# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
from odoo import models, fields, api
import logging
logger = logging.getLogger('__name__')

class QbookLog(models.Model):
    _name = 'qbook.log'
    _rec_name = 'log_name'
    
    @api.model
    def create(self,vals):
        if not vals.get('log_name'):
            logger.info('innnnnnnloggerrrrrrrrr')
            name = self.env['ir.sequence'].next_by_code('log.error')
            vals.update({
                'log_name': name
            })
        return super(QbookLog, self).create(vals)
            
    log_name = fields.Char(string="Name", required=False, )
    log_date = fields.Datetime(string="Date",index=True,default=fields.Datetime.now)
    error_lines = fields.One2many("log.error", "log_id", string="Error lines", required=False, )
    all_operations = fields.Selection(string="Operations",
                                     selection=[
                                                ('authenticate_credentials', 'Vaidate Credentials'),
                                                ('import_accounts', 'Import Accounts'),
                                                ('import_tax', 'Import Tax'),
                                                ('import_payment_method', 'Import Payment Method'),
                                                ('import_payment_term', 'Import Payment Term'),
                                                ('import_department', 'Import Department'),
                                                ('import_customer', 'Import Customer'),
                                                ('import_vendor', 'Import Vendor'),
                                                ('import_employee', 'Import Employee'),
                                                ('import_product_category', 'Import Product Category'),
                                                ('import_products', 'Import Product'),
                                                ('import_product_inventory', 'Import Products Inventory'),
                                                ('import_sale_order', 'Import Sale Order'),
                                                ('import_purchase_order', 'Import Purchase Order'),
                                                ('import_customer_invoice', 'Import Customer Invoice'),
                                                ('import_vendor_bill', 'Import Vendor Bill'),
                                                ('import_customer_payment', 'Import Payment'),
                                                ('import_vendor_bills_payment', 'Import Bills Payment'),

                                                ('export_customer','Export Customer'),
                                                ('export_vendor','Export Vendor'),
                                                ('export_employee','Export Employee'),
                                                ('export_department','Export Department'),
                                                ('export_payment_method','Export Payment Method'),
                                                ('export_category','Export Category'),
                                                ('export_product','Export Product'),
                                                ('export_sale_orders','Export Sale Orders'),
                                                ('export_purchase_orders','Export Purchase Orders'),
                                                ('export_invoice','Export Invoice'),
                                                ('export_account','Export Account'),
                                                ('export_tax','Export Tax'),
                                                ],)



class log_error(models.Model):
    _name = 'log.error'
    _rec_name = 'log_description'

    log_description = fields.Text(string="Log description")
    log_id = fields.Many2one("qbook.log", string="Log description", required=False )

