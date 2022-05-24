from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_customer_wizard(models.TransientModel):

    
    _name = 'export.customer.wiz'
    # _rec_name = 'config_name'


    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORTCUSTTTTTTTTTTWIZZZZZZ"
        cust_obj = self.env['res.partner']
        export_cust = self._context.get('active_ids')
        # print "export_custttttttt",export_cust
        for export in cust_obj.browse(export_cust):
            # print "exportttttttttttt",export
            # if export.customer == True:
            self.shop_ids.with_context({'export_cust':export.id}).exportQbooksCustomers()

            # else:
            #     self.shop_ids.with_context({'export_cust':export.id}).exportQbooksVendors()

    # @api.multi
    # def customer_warning_for_vendor(self):
    #     print "ccccccccccccccc"
    #     cust_obj = self.env['res.partner']
    #     export_cust = self._context.get('active_ids')
    #     print "export_custttttttt",export_cust
    #     for export in cust_obj.browse(export_cust):
    #         print "exportttttttttttt",export
    #         if export.supplier == True:
    #             raise UserError(_('Sorry You Can Not Export Vendor From Here!'))



class export_vendor_wizard(models.TransientModel):

    _name = 'export.vendor.wiz'
    # _rec_name = 'config_name'


    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORTVendorrrWIZZZZZZ"
        cust_obj = self.env['res.partner']
        export_vend = self._context.get('active_ids')
        # print "export_vendttttttt",export_vend
        for export in cust_obj.browse(export_vend):
            # print "exportttttttttttt",export
            # if export.customer == True:
            self.shop_ids.with_context({'export_vend':export.id}).exportQbooksVendors()