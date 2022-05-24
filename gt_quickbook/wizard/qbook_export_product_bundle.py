from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_product_bundle_wizard(models.TransientModel):
    
    _name = 'export.product.bundle.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_product_bbbbb_WIZZZZZZ"
        prod_prod_obj = self.env['product.product']
        export_prod_bndl = self._context.get('active_ids')
        # print "export_prod_bndltttttbbbbbbb",export_prod_bndl
        for export in prod_prod_obj.browse(export_prod_bndl):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_prod_bndl':export.id}).exportQbooksProductBundle()
