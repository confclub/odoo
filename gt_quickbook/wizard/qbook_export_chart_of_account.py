from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_chart_account_wizard(models.TransientModel):
    
    _name = 'export.chart.account.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_acccccchhhhh_WIZZZZZZ"
        chh_acc_obj  = self.env['account.account']
        export_chh_acc = self._context.get('active_ids')
        # print "export_chh_accccccc",export_chh_acc
        for export in chh_acc_obj.browse(export_chh_acc):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_chh_acc':export.id}).exportQbooksAccount()
