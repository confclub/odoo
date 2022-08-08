# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

class PurchaseOrder(models.Model):
	_inherit ='purchase.order'
	
	purchase_manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
	purchase_manual_currency_rate = fields.Float('Rate', digits=(12, 6))

	def _prepare_invoice(self):
		res  = super(PurchaseOrder, self)._prepare_invoice()
		self.ensure_one()
	
		res.update({
			'c_purchase_id' : self.id,
			'applied_already' : True if self.purchase_manual_currency_rate_active else False,
			# 'manual_currency_rate_active':self.purchase_manual_currency_rate_active,
			# 'manual_currency_rate':self.purchase_manual_currency_rate,
			})
		return res

	def action_create_invoice(self):
		"""Create the invoice associated to the PO.
		"""
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

		# 1) Prepare invoice vals and clean-up the section lines
		invoice_vals_list = []
		for order in self:
			if order.invoice_status != 'to invoice':
				continue

			order = order.with_company(order.company_id)
			pending_section = None
			# Invoice values.
			invoice_vals = order._prepare_invoice()
			# Invoice line values (keep only necessary sections).
			for line in order.order_line:
				if line.display_type == 'line_section':
					pending_section = line
					continue
				if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
					if pending_section:
						invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
						pending_section = None
					invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
			invoice_vals_list.append(invoice_vals)

		if not invoice_vals_list:
			raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

		# 2) group by (company_id, partner_id, currency_id) for batch creation
		new_invoice_vals_list = []
		for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
			origins = set()
			payment_refs = set()
			refs = set()
			ref_invoice_vals = None
			for invoice_vals in invoices:
				if not ref_invoice_vals:
					ref_invoice_vals = invoice_vals
				else:
					ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
				origins.add(invoice_vals['invoice_origin'])
				payment_refs.add(invoice_vals['payment_reference'])
				refs.add(invoice_vals['ref'])
			ref_invoice_vals.update({
				'ref': ', '.join(refs)[:2000],
				'invoice_origin': ', '.join(origins),
				'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
			})
			new_invoice_vals_list.append(ref_invoice_vals)
		invoice_vals_list = new_invoice_vals_list

		# 3) Create invoices.
		moves = self.env['account.move']
		AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
		for vals in invoice_vals_list:
			moves |= AccountMove.with_company(vals['company_id']).create(vals)

		# 4) Some moves might actually be refunds: convert them if the total amount is negative
		# We do this after the moves have been created since we need taxes, etc. to know if the total
		# is actually negative or not
		moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

		for move in moves :
			prch = move.c_purchase_id
			if prch and prch.purchase_manual_currency_rate_active:
				move.write({
					'manual_currency_rate_active':prch.purchase_manual_currency_rate_active,
					'manual_currency_rate': prch.purchase_manual_currency_rate,
				})

		return self.action_view_invoice(moves)


class PurchaseOrderLine(models.Model):
	_inherit ='purchase.order.line'

	def _prepare_stock_moves(self, picking):
		""" Prepare the stock moves data for one order line. This function returns a list of
		dictionary ready to be used in stock.move's create()
		"""
		rec  = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
		seller = self.product_id._select_seller(
			partner_id=self.partner_id,
			quantity=self.product_qty,
			date=self.order_id.date_order,
			uom_id=self.product_uom)
		
		price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.company_id) if seller else 0.0
		if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
			price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)

		if seller and self.product_uom and seller.product_uom != self.product_uom:
			price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)
		
		if self.order_id.purchase_manual_currency_rate_active and self.price_unit != 0 and self.order_id.purchase_manual_currency_rate != 0 :
			price_unit = self.order_id.currency_id.round((self.price_unit) / self.order_id.purchase_manual_currency_rate)

		for line in rec :
			line.update({'price_unit' : price_unit})

		return rec
	
	@api.onchange('product_qty', 'product_uom')
	def _onchange_quantity(self):
		if not self.product_id:
			return

		seller = self.product_id._select_seller(
			partner_id=self.partner_id,
			quantity=self.product_qty,
			date=self.order_id.date_order,
			uom_id=self.product_uom)

		if seller or not self.date_planned:
			self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

		if not seller:
			return

		price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.company_id) if seller else 0.0
		pu = price_unit
		if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
			price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)

		if seller and self.product_uom and seller.product_uom != self.product_uom:
			price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)
		
		if self.order_id.purchase_manual_currency_rate_active and price_unit != 0 and self.order_id.purchase_manual_currency_rate != 0:
			price_unit = pu / self.order_id.purchase_manual_currency_rate

		self.price_unit = price_unit


# class AccountInvoice(models.Model):
# 	_inherit = 'account.move'

# 	@api.onchange('purchase_vendor_bill_id', 'purchase_id')
# 	def _onchange_purchase_auto_complete(self):
# 		''' Load from either an old purchase order, either an old vendor bill.

# 		When setting a 'purchase.bill.union' in 'purchase_vendor_bill_id':
# 		* If it's a vendor bill, 'invoice_vendor_bill_id' is set and the loading is done by '_onchange_invoice_vendor_bill'.
# 		* If it's a purchase order, 'purchase_id' is set and this method will load lines.

# 		/!\ All this not-stored fields must be empty at the end of this function.
# 		'''
# 		if self.purchase_vendor_bill_id.vendor_bill_id:
# 			self.invoice_vendor_bill_id = self.purchase_vendor_bill_id.vendor_bill_id
# 			self._onchange_invoice_vendor_bill()
# 		elif self.purchase_vendor_bill_id.purchase_order_id:
# 			self.purchase_id = self.purchase_vendor_bill_id.purchase_order_id
# 		self.purchase_vendor_bill_id = False

# 		if not self.purchase_id:
# 			return

# 		# Copy partner.
# 		self.partner_id = self.purchase_id.partner_id
# 		self.fiscal_position_id = self.purchase_id.fiscal_position_id
# 		self.invoice_payment_term_id = self.purchase_id.payment_term_id
# 		self.currency_id = self.purchase_id.currency_id

# 		if self.purchase_id.purchase_manual_currency_rate_active:
# 			self.manual_currency_rate_active = self.purchase_id.purchase_manual_currency_rate_active
# 			self.manual_currency_rate = self.purchase_id.purchase_manual_currency_rate

# 		# Copy purchase lines.
# 		po_lines = self.purchase_id.order_line - self.line_ids.mapped('purchase_line_id')
# 		new_lines = self.env['account.move.line']
# 		for line in po_lines.filtered(lambda l: not l.display_type):
# 			new_line = new_lines.new(line._prepare_account_move_line(self))
# 			new_line.account_id = new_line._get_computed_account()
# 			new_line._onchange_price_subtotal()
# 			new_lines += new_line
# 		new_lines._onchange_mark_recompute_taxes()

# 		# Compute invoice_origin.
# 		origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
# 		self.invoice_origin = ','.join(list(origins))

# 		# Compute ref.
# 		refs = set(self.line_ids.mapped('purchase_line_id.order_id.partner_ref'))
# 		refs = [ref for ref in refs if ref]
# 		self.ref = ','.join(refs)

# 		# Compute _invoice_payment_ref.
# 		if len(refs) == 1:
# 			self._invoice_payment_ref = refs[0]

# 		self.purchase_id = False
# 		self._onchange_currency()
# 		self.partner_bank_id = self.bank_partner_id.bank_ids and self.bank_partner_id.bank_ids[0]
				
