# -*- encoding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2012 (http://www.globalteckz.com)
#
##############################################################################
import time
from odoo import api, fields, models, _

class QbooksConnectorWizard(models.TransientModel):
    _name = "quickbooks.connector.wizard"

    @api.model
    def default_get(self, fields):
        result= super(QbooksConnectorWizard, self).default_get(fields)
        if self._context.get('active_model') == 'quickbook.integration':
            obj = self.env['quickbook.integration'].browse(self._context.get('active_id'))
            result.update({'shop_ids': self._context.get('active_ids'),
                           })
        return result
    
    shop_ids = fields.Many2many('quickbook.integration', string="Select Integration")
    
    #import fields
    import_customer = fields.Boolean('Import Customers')
    import_vendor = fields.Boolean('Import Vendor')
    import_employee = fields.Boolean('Import Employee')
    import_payment_metod = fields.Boolean('Import Payment Method')
    import_payment_term = fields.Boolean('Import Payment Term')
    import_department = fields.Boolean('Import Department')
    import_product_category = fields.Boolean('Import Product Category')
    import_product = fields.Boolean('Import Product')
    import_product_inventory = fields.Boolean('Import Product Inventory')
    import_order  = fields.Boolean('Import Order')
    import_invoice  = fields.Boolean('Import Customer Invoice')
    import_vendor_bill  = fields.Boolean('Import Vendor Bill')
    import_purchase_order  = fields.Boolean('Import Purchase Order')
    import_customer_payment  = fields.Boolean('Import Customer Payment')
    import_vendor_payment  = fields.Boolean('Import Vendor Bills Payment')
    import_account  = fields.Boolean('Import Account')
    import_tax  = fields.Boolean('Import Tax')

    export_account = fields.Boolean('Export Accounts')
    export_tax = fields.Boolean('Export Taxes')
    export_payment_method = fields.Boolean('Export Payment Methods')
    export_department = fields.Boolean('Export Departments')
    export_customers = fields.Boolean('Export Customers')
    export_vendor = fields.Boolean('Export Vendors')
    export_employee = fields.Boolean('Export Employees')
    export_category = fields.Boolean('Export Category')
    export_products = fields.Boolean('Export Products And Inventory')
    export_order = fields.Boolean('Export Sales Orders')
    export_purchase_order = fields.Boolean('Export Purchase Orders')
    export_customer_invoice= fields.Boolean('Export Customer Invoices')



    # @api.one
    def import_qbooks(self):
        # print "wwwwwwwwwwwww_iimport_qbooks"

        # IMPORT

        if self.import_customer:
            self.shop_ids.import_customer()

        if self.import_vendor:
            self.shop_ids.import_vendor()

        if self.import_employee:
            self.shop_ids.import_employee()

        if self.import_payment_metod:
            self.shop_ids.import_payment_method()

        if self.import_payment_term:
            self.shop_ids.import_payment_term()

        if self.import_department:
            self.shop_ids.import_departments()

        if self.import_product_category:
            self.shop_ids.import_category()

        if self.import_product:
            self.shop_ids.import_product()

        if self.import_product_inventory:
            self.shop_ids.import_product_inventory()

        if self.import_order:
            self.shop_ids.import_order()

        if self.import_invoice:
            self.shop_ids.import_invoice()

        if self.import_vendor_bill:
            self.shop_ids.import_vendor_bill()

        if self.import_purchase_order:
            self.shop_ids.import_purchase_order()

        if self.import_customer_payment:
            self.shop_ids.import_customer_payment()

        if self.import_vendor_payment:
            self.shop_ids.import_vendor_payment()             

        if self.import_account:
            self.shop_ids.import_account()

        if self.import_tax:
            self.shop_ids.import_tax()

        # EXPORT

        if self.export_account:
            self.shop_ids.exportQbooksAccount()    

        if self.export_tax:
            self.shop_ids.exportQbooksTax()
        
        if self.export_payment_method:
            self.shop_ids.exportQbooksPaymentMethod()

        if self.export_department:
            self.shop_ids.exportQbooksDepartment()

        if self.export_customers:
            self.shop_ids.exportQbooksCustomers()

        if self.export_vendor:
            self.shop_ids.exportQbooksVendors()

        if self.export_employee:
            self.shop_ids.exportQbooksEmployee()

        if self.export_category:
            self.shop_ids.exportQbooksCategory()

        if self.export_products:
            self.shop_ids.exportQbooksProduct()

        if self.export_order:
            self.shop_ids.exportQbooksOrder()

        if self.export_purchase_order:
            self.shop_ids.exportQbooksPurchaseOrder()

        if self.export_customer_invoice:
            self.shop_ids.exportQbooksInvoice()

        return True
    
    
