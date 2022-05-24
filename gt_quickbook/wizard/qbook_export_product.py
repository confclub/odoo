from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_product_wizard(models.TransientModel):
    
    _name = 'export.product.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_product_WIZZZZZZ"
        prod_temp_obj = self.env['product.template']
        # product_obj = self.env['product.product']
        # bundle_obj = self.env['bundle.product']
        export_prod = self._context.get('active_ids')
        # print "export_prodttttt",export_prod
        for export in prod_temp_obj.browse(export_prod):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_prod':export.id}).exportQbooksProduct()
