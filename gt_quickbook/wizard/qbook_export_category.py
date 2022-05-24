from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_category_wizard(models.TransientModel):
    
    _name = 'export.category.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_category_WIZZZZZZ"

        categ_obj  = self.env['product.category']
        export_cat = self._context.get('active_ids')
        # print "export_catttttt",export_cat
        
        for export in categ_obj.browse(export_cat):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_cat':export.id}).exportQbooksCategory()
