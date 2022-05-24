from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_order_wizard(models.TransientModel):
    
    _name = 'export.order.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_orderrrr_WIZZZZZZ"
        sale_order_obj  = self.env['sale.order']
        export_order = self._context.get('active_ids')
        # print "export_orderr",export_order
        
        for export in sale_order_obj.browse(export_order):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_order':export.id}).exportQbooksOrder()
