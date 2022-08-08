# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
from odoo.exceptions import UserError


class stock_move(models.Model):
	_inherit = 'stock.move'

	def _create_in_svl(self, forced_quantity=None):
		"""Create a `stock.valuation.layer` from `self`.

		:param forced_quantity: under some circunstances, the quantity to value is different than
			the initial demand of the move (Default value = None)
		"""
		rec  = super(stock_move, self)._create_in_svl(forced_quantity=None)
		for rc in rec:
			for line in self:
				if line.purchase_line_id :
					if line.purchase_line_id.order_id.purchase_manual_currency_rate_active:
						price_unit = line.purchase_line_id.order_id.currency_id.round((line.purchase_line_id.price_unit)/line.purchase_line_id.order_id.purchase_manual_currency_rate)

						rc.write({'unit_cost' : price_unit,'value' :price_unit * rc.quantity,'remaining_value' : price_unit * rc.quantity})
		return rec

	def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
		"""
		Generate the account.move.line values to post to track the stock valuation difference due to the
		processing of the given quant.
		"""
		self.ensure_one()

		# the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
		# the company currency... so we need to use round() before creating the accounting entries.
		debit_value = self.company_id.currency_id.round(cost)
		credit_value = debit_value

		valuation_partner_id = self._get_partner_id_for_valuation_lines()

		if self.purchase_line_id.order_id.purchase_manual_currency_rate_active:
			debit_value = self.purchase_line_id.order_id.currency_id.round((self.purchase_line_id.price_unit*qty)/self.purchase_line_id.order_id.purchase_manual_currency_rate)
			credit_value = debit_value
			
			res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

		else:      
			res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

		if self.sale_line_id.order_id.sale_manual_currency_rate !=0 :
			debit_value = self.sale_line_id.order_id.currency_id.round((self.sale_line_id.price_unit*qty)/self.sale_line_id.order_id.sale_manual_currency_rate)
			credit_value = debit_value
			res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

		else:      
			res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

		return res


	def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
		# This method returns a dictionary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
		
		company_currency = self.company_id.currency_id
		
		diff_currency_po = self.purchase_line_id.order_id.currency_id != company_currency
		diff_currency_so = self.sale_line_id.order_id.currency_id != company_currency
		
		ctx = dict(self._context, lang=self.purchase_line_id.order_id.partner_id.lang)
		self.ensure_one()
		if self._context.get('forced_ref'):
			ref = self._context['forced_ref']
		else:
			ref = self.picking_id.name
		if self.purchase_line_id:
			debit_line_vals = {
				'name': self.name,
				'product_id': self.product_id.id,
				'quantity': qty,
				'product_uom_id': self.product_id.uom_id.id,
				'ref': ref,
				'partner_id': partner_id,
				'debit': debit_value if debit_value > 0 else 0,
				'credit': -debit_value if debit_value < 0 else 0,
				'account_id': debit_account_id,
				'amount_currency': diff_currency_po and (self.purchase_line_id.price_unit)*qty,
				'currency_id': diff_currency_po and self.purchase_line_id.order_id.currency_id.id,
			}

			credit_line_vals = {
				'name': self.name,
				'product_id': self.product_id.id,
				'quantity': qty,
				'product_uom_id': self.product_id.uom_id.id,
				'ref': ref,
				'partner_id': partner_id,
				'credit': credit_value if credit_value > 0 else 0,
				'debit': -credit_value if credit_value < 0 else 0,
				'account_id': credit_account_id,
				'amount_currency': diff_currency_po and (-self.purchase_line_id.price_unit)*qty,
				'currency_id': diff_currency_po and self.purchase_line_id.order_id.currency_id.id,
			}
		elif self.sale_line_id and self.sale_line_id.order_id.sale_manual_currency_rate_active:
			debit_line_vals = {
				'name': self.name,
				'product_id': self.product_id.id,
				'quantity': qty,
				'product_uom_id': self.product_id.uom_id.id,
				'ref': ref,
				'partner_id': partner_id,
				'debit': debit_value if debit_value > 0 else 0,
				'credit': -debit_value if debit_value < 0 else 0,
				'account_id': debit_account_id,
				'amount_currency': diff_currency_so and (self.sale_line_id.price_unit)*qty,
				'currency_id': diff_currency_so and self.sale_line_id.order_id.currency_id.id,
			}

			credit_line_vals = {
				'name': self.name,
				'product_id': self.product_id.id,
				'quantity': qty,
				'product_uom_id': self.product_id.uom_id.id,
				'ref': ref,
				'partner_id': partner_id,
				'credit': credit_value if credit_value > 0 else 0,
				'debit': -credit_value if credit_value < 0 else 0,
				'account_id': credit_account_id,
				'amount_currency': diff_currency_so and (-self.sale_line_id.price_unit)*qty,
				'currency_id': diff_currency_so and self.sale_line_id.order_id.currency_id.id,
			}
		else:
			debit_line_vals = {
					'name': self.name,
					'product_id': self.product_id.id,
					'quantity': qty,
					'product_uom_id': self.product_id.uom_id.id,
					'ref': ref,
					'partner_id': partner_id,
					'debit': debit_value if debit_value > 0 else 0,
					'credit': -debit_value if debit_value < 0 else 0,
					'account_id': debit_account_id,
				}

			credit_line_vals = {
				'name': self.name,
				'product_id': self.product_id.id,
				'quantity': qty,
				'product_uom_id': self.product_id.uom_id.id,
				'ref': ref,
				'partner_id': partner_id,
				'credit': credit_value if credit_value > 0 else 0,
				'debit': -credit_value if credit_value < 0 else 0,
				'account_id': credit_account_id,
			}

		rslt = {'credit_line_vals': credit_line_vals, 'debit_line_vals': debit_line_vals}
		if credit_value != debit_value:
			# for supplier returns of product in average costing method, in anglo saxon mode
			diff_amount = debit_value - credit_value
			price_diff_account = self.product_id.property_account_creditor_price_difference

			if not price_diff_account:
				price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
			if not price_diff_account:
				raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))

			rslt['price_diff_line_vals'] = {
				'name': self.name,
				'product_id': self.product_id.id,
				'quantity': qty,
				'product_uom_id': self.product_id.uom_id.id,
				'ref': ref,
				'partner_id': partner_id,
				'credit': diff_amount > 0 and diff_amount or 0,
				'debit': diff_amount < 0 and -diff_amount or 0,
				'account_id': price_diff_account.id,
			}
		return rslt

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
