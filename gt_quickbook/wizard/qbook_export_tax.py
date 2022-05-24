from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_tax_wizard(models.TransientModel):
    
    _name = 'export.tax.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_tax_WIZZZZZZ"
        chh_acc_obj  = self.env['account.tax']
        export_tax = self._context.get('active_ids')
        # print "export_taxxxxxxxxxxx",export_tax
        for export in chh_acc_obj.browse(export_tax):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_tax':export.id}).exportQbooksTax()
