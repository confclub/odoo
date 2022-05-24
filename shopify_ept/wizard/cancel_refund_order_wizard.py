# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import json
from odoo import models, fields, _
from odoo.exceptions import UserError
from .. import shopify


class ShopifyCancelRefundOrderWizard(models.TransientModel):
    _name = "shopify.cancel.refund.order.wizard"
    _description = 'Shopify Cancel Refund Order Wizard'

    message = fields.Selection([('customer', 'Customer changed/cancelled order'),
                                ('inventory', 'Fraudulent order'),
                                ('fraud', 'Items unavailable'),
                                ('other', 'Other'),
                                ], default="other", help="The reason for the order cancellation.")
    notify_by_email = fields.Boolean("Notify By Email ?", default=True,
                                     help="Whether to send an email to the customer notifying the cancellation.")
    auto_create_credit_note = fields.Boolean("Create Credit Note In ERP", default=False,
                                             help="It will create a credit not in Odoo")
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 help='You can select here the journal to use for the credit note that will be created.'
                                      ' If you leave that field empty, it will use the same journal as the current '
                                      'invoice.')
    reason = fields.Char()
    refund_date = fields.Date()
    # Below fields are used for refund process.
    notify_by_email = fields.Boolean("Notify By Email ?", help="Whether to send a refund notification to the customer.")
    note = fields.Char(help="An optional note attached to a refund.")
    restock_type = fields.Selection(
        [('no_restock', 'No Return'), ('cancel', 'Cancel'), ('return', 'Return')],
        default='no_restock',
        help="No Return: Refunding these items won't affect inventory.\nCancel:The items have not yet been fulfilled. "
             "The canceled quantity will be added back to the available count.\n Return:The items were already "
             "delivered,and will be returned to the merchant.The returned quantity will be added back to the available "
             "count")

    def cancel_in_shopify(self):
        """This method used to cancel order in shopify.
            @param : self
            @return: action
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 20/11/2019.
            Task Id : 157911
        """
        active_id = self._context.get('active_id')
        sale_order_id = self.env['sale.order'].browse(active_id)
        instance = sale_order_id.shopify_instance_id
        instance.connect_in_shopify()

        try:
            order_id = shopify.Order()
        except Exception as error:
            raise UserError("Error while cancelling the order in shopify :\n%s" % error)

        order_id.id = sale_order_id.shopify_order_id
        order_id.reason = self.message
        order_id.email = self.notify_by_email

        try:
            order_id.cancel()
        except Exception as error:
            if hasattr(error, "response"):
                if hasattr(error.response, "body") and error.response.code == 422:
                    msg = "Error while cancelling the order in shopify :\n%s" % (
                        json.loads(error.response.body.decode()).get("error"))
                else:
                    msg = "Error while cancelling the order in shopify : %s\n%s" % (
                        error.response.code, json.loads(error.response.body.decode()))
            else:
                msg = "Error while cancelling the order in shopify :\n%s" % str(error)
            raise UserError(msg)

        sale_order_id.write({'canceled_in_shopify': True})
        if self.auto_create_credit_note:
            self.shopify_create_credit_note(sale_order_id)
        return True

    def shopify_create_credit_note(self, order_id):
        """It will create a credit note in Odoo base on the configuration.
            @param : self
            @return: action
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 20/11/2019.
            Task Id : 157911
        """
        moves = order_id.invoice_ids.filtered(lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid')
        if not moves:
            # Here we add commit because we need to write values in sale order before warring
            # raise. if raise warring it will not commit so we need to write commit.
            order_id._cr.commit()
            warning_message = "1.Order cancel in Shopify but unable to create a credit note." \
                              "2.Since order may be uncreated or unpaid invoice."
            raise UserError(warning_message)
        default_values_list = []
        for move in moves:
            date = self.refund_date or move.date
            default_values_list.append({
                'ref': _('Reversal of: %s, %s') % (move.name, self.reason) if self.reason else _(
                    'Reversal of: %s') % move.name,
                'date': date,
                'invoice_date': move.is_invoice(include_receipts=True) and date or False,
                'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
                'invoice_payment_term_id': None,
                'auto_post': True if date > fields.Date.context_today(self) else False,
            })
        moves._reverse_moves(default_values_list)
        return True

    def refund_in_shopify(self):
        """This method used to create a refund in Shopify.
            @param : self
            @return:
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 20/11/2019.
            Task Id : 157911
        """
        active_id = self._context.get('active_id')
        credit_note_ids = self.env['account.move'].browse(active_id)
        mismatch_log_lines = []
        model = "account.move"
        model_id = self.env["common.log.lines.ept"].get_model_id(model)
        restock_type = self.restock_type
        do_not_order_process_ids = []
        for credit_note_id in credit_note_ids:
            if not credit_note_id.shopify_instance_id:
                continue
            credit_note_id.shopify_instance_id.connect_in_shopify()
            orders = credit_note_id.invoice_line_ids.sale_line_ids.order_id
            refund_lines_list = []
            for invoice_line_id in credit_note_id.invoice_line_ids:
                if invoice_line_id.product_id.type == 'service':
                    continue
                shopify_line_id = invoice_line_id.sale_line_ids.shopify_line_id
                refund_line_dict = {'line_item_id': shopify_line_id,
                                    'quantity': int(invoice_line_id.quantity),
                                    'restock_type': restock_type}

                if restock_type in ['cancel', 'return']:
                    order_id = credit_note_id.invoice_line_ids.sale_line_ids.order_id
                    shopify_location_id = order_id.shopify_location_id or False
                    if not shopify_location_id:
                        log_message = "Location is not set in order (%s).Unable to refund in shopify.\n You can see " \
                                      "order location here: Order => Shopify Info => Shopify Location " % order_id.name
                        log_line = self.env["common.log.lines.ept"].shopify_create_order_log_line(log_message, model_id,
                                                                                                  order_id, False,
                                                                                                  order_id.name)
                        mismatch_log_lines.append(log_line.id)
                        do_not_order_process_ids.append(order_id.id)
                        continue
                    refund_line_dict.update(
                        {'location_id': shopify_location_id.shopify_location_id})
                refund_lines_list.append(refund_line_dict)

            log_lines = self.create_refund_in_shopify(orders, credit_note_id, refund_lines_list,
                                                      model_id, do_not_order_process_ids)
        if mismatch_log_lines or log_lines:
            total_log_lines = mismatch_log_lines + log_lines
            self.env["common.log.book.ept"].create({'type': 'export',
                                                    'module': 'shopify_ept',
                                                    'shopify_instance_id': credit_note_id.shopify_instance_id.id if
                                                    credit_note_id.shopify_instance_id else False,
                                                    'active': True,
                                                    "model_id": model_id,
                                                    'log_lines': [(6, 0, total_log_lines)]
                                                    })
        return True

    def create_refund_in_shopify(self, orders, credit_note_id, refund_lines_list, model_id,
                                 do_not_order_process_ids):
        """This method used to create a refund in Shopify.
            @param : self
            @return:
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 20/11/2019.
            Task Id : 157911
        """
        note = self.note
        notify = self.notify_by_email
        in_picking_total_qty = 0
        out_picking_total_qty = 0
        shipping = {}
        mismatch_logline = []
        for order in orders:
            if order.id in do_not_order_process_ids:
                continue
            outgoing_picking_ids = order.mapped('picking_ids').filtered(
                lambda picking: picking.picking_type_id.code == 'outgoing' and picking.state == 'done')
            incoming_picking_ids = order.mapped('picking_ids').filtered(
                lambda picking: picking.picking_type_id.code == 'incoming' and picking.state == 'done')
            if incoming_picking_ids:
                in_picking_total_qty = sum(
                    incoming_picking_ids.mapped('move_lines').mapped('quantity_done'))
            if outgoing_picking_ids:
                out_picking_total_qty = sum(
                    outgoing_picking_ids.mapped('move_lines').mapped('quantity_done'))

            if in_picking_total_qty == out_picking_total_qty:
                shipping.update({"full_refund": True})
            else:
                shipping.update({'amount': 0.0})
            refund_amount = credit_note_id.amount_total
            total_refund_in_shopify = 0.0
            total_order_amount = order.amount_total
            # This used for amount validation.
            transactions = shopify.Transaction().find(order_id=order.shopify_order_id)
            parent_id = False
            for transaction in transactions:
                result = transaction.to_dict()
                if result.get('kind') == 'sale':
                    parent_id = result.get('id')
                    gateway = result.get('gateway')
                if result.get('kind') == 'refund' and result.get('status') == 'success':
                    refunded_amount = result.get('amount')
                    total_refund_in_shopify = total_refund_in_shopify + float(refunded_amount)
            total_refund_amount = total_refund_in_shopify + refund_amount
            maximum_refund_allow = refund_amount - total_refund_in_shopify
            if maximum_refund_allow < 0:
                maximum_refund_allow = 0.0
            if total_refund_amount > total_order_amount:
                raise UserError(_(
                    "You can't refund then actual payment, requested amount for refund %s, maximum refund allow %s") % (
                                    refund_amount, maximum_refund_allow))
            refund_in_shopify = shopify.Refund()
            vals = {'notify': notify,
                    "shipping": shipping,
                    "note": note,
                    "order_id": order.shopify_order_id,
                    "refund_line_items": refund_lines_list,
                    "transactions": [
                        {
                            "parent_id": parent_id,
                            "amount": refund_amount,
                            "kind": "refund",
                            "gateway": gateway,
                        }
                    ]
                    }
            try:
                refund_in_shopify.create(vals)
            except Exception as error:
                log_message = "When creating refund in Shopify for order (%s), issue arrive in " \
                              "request (%s)" % (order.name, error)
                log_line = self.inv["common.log.lines.ept"].shopify_create_order_log_line(
                    log_message, model_id, order, False, order.name)
                mismatch_logline.append(log_line.id)
                continue
            credit_note_id.write({'is_refund_in_shopify': True})

        return mismatch_logline
