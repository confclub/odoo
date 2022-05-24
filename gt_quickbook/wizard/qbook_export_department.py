from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_department_wizard(models.TransientModel):
    
    _name = 'export.department.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_DEPT_WIZZZZZZ"
        dept_obj  = self.env['hr.department']
        export_dept = self._context.get('active_ids')
        # print "export_custttttttt",export_dept
        for export in dept_obj.browse(export_dept):
            # print "exportttttttttttt",export
            self.shop_ids.with_context({'export_dept':export.id}).exportQbooksDepartment()
