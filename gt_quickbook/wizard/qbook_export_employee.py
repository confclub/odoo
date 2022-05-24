from openerp import fields,models,api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class export_employee_wizard(models.TransientModel):

    _name = 'export.employee.wiz'

    shop_ids = fields.Many2one('quickbook.integration', string="Select Integration")
     
     
    # @api.multi
    def export_to_qbook(self):
        # print "EXPORT_EMPPPPPPP_WIZZZZZZ"
        emp_obj = self.env['hr.employee']
        export_emp = self._context.get('active_ids')
        # print "ACTIVE_emppppppppppp",export_emp
        for export in emp_obj.browse(export_emp):
            # print "forrrrexportttttttttttt",export
            self.shop_ids.with_context({'export_emp':export.id}).exportQbooksEmployee()
