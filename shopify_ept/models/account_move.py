# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, _


class AccountMove(models.Model):
    _inherit = "account.move"

    is_refund_in_shopify = fields.Boolean("Refund In Shopify", default=False)
    shopify_instance_id = fields.Many2one("shopify.instance.ept", "Instances")
    shopify_refund_id = fields.Char()
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Address',
        readonly=True, required=True, compute='_compute_partner_invoice_id')

    def _compute_partner_invoice_id(self):
        for record in self:
            if record.invoice_origin:
                sal_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)])
                if sal_order:
                    record.partner_invoice_id = sal_order.partner_invoice_id.id
            else:
                record.partner_invoice_id = False

    def refund_in_shopify(self):
        """This method used to open a wizard to Refund order in Shopify.
            @param : self
            @return: action
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 20/11/2019.
            Task Id : 157911
        """
        view = self.env.ref('shopify_ept.view_shopify_refund_wizard')
        context = dict(self._context)
        context.update({'active_model': 'account.invoice', 'active_id': self.id, 'active_ids': self.ids})
        return {
            'name': _('Refund order In Shopify'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shopify.cancel.refund.order.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context
        }
