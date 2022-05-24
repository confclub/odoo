from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_payment_method_wizard(models.TransientModel):
    
    _name = 'export.payment.method.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_Payment_methodd_WIZZZZZZ"
        payment_method_obj  = self.env['payment.method']
        export_payment_method = self._context.get('active_ids')
        # print "export_custttttttt",export_payment_method
        for export in payment_method_obj.browse(export_payment_method):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_payment_method':export.id}).exportQbooksPaymentMethod()
