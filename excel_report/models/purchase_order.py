# -*- coding: utf-8 -*-
import datetime

from odoo import api, fields, models, _
from odoo.tests import Form, tagged


class PurchaseOrderInherit(models.Model):

    _inherit = "purchase.order"

    def create_invoice(self):
        for order in self:
            if order.state == 'purchase' and order.order_line:
                if not order.invoice_ids:
                    order.action_create_invoice()
                invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                for invoice in invoices:
                    invoice.invoice_date = datetime.datetime.now()
                    invoice.action_post()
                    action_data = invoice.action_register_payment()
                    wizard = self.env['account.payment.register'].with_context(action_data['context']).create({})
                    wizard.action_create_payments()

    def create_deliveries(self):
        for order in self:
            if order.state == 'draft':
                order.button_confirm()
                for pick in order.picking_ids:
                    wizerd = pick.button_validate()
                    self.env['stock.immediate.transfer'].with_context(wizerd['context']).create({}).process()

    def delete_orders(self):
        for order in self:
            if order.state == 'draft':
                order.button_cancel()

    def create_credit_note(self):
        for order in self:
            if order.state == 'purchase' and order.order_line:
                if order.invoice_ids:
                    invoices = order.invoice_ids.filtered(lambda r: r.move_type == 'in_invoice' and r.state == 'posted')
                    for invoice in invoices:
                        invoice.action_reverse()
                        move_reversal = self.env['account.move.reversal'].with_context(
                            active_model="account.move",
                            active_ids=invoice.ids).create({
                            'reason': 'purchase reason',
                        })
                        reversal = move_reversal.reverse_moves()
                        reverse_move = self.env['account.move'].browse(reversal['res_id'])
                        reverse_move.action_post()
                        action_data = reverse_move.action_register_payment()
                        wizard = self.env['account.payment.register'].with_context(action_data['context']).create({})
                        wizard.action_create_payments()
