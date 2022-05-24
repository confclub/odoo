from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_purchase_order_wizard(models.TransientModel):
    
    _name = 'export.purchase.order.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_Purchaseee_WIZZZZZZ"
        purchase_order_obj  = self.env['purchase.order']
        export_purchase_order = self._context.get('active_ids')
        # print "export_pppppppppp",export_purchase_order
        for export in purchase_order_obj.browse(export_purchase_order):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_purchase_order':export.id}).exportQbooksPurchaseOrder()


