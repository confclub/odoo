from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_invoice_wizard(models.TransientModel):
    
    _name = 'export.invoice.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_Invccccccccccc_WIZZZZZZ"
        inv_obj  = self.env['account.move']
        export_invoice = self._context.get('active_ids')
        # print "export_pppppppppp",export_invoice
        
        for export in inv_obj.browse(export_invoice):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_invoice':export.id}).exportQbooksInvoice()


