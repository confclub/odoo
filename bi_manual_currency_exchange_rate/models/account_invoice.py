# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
from odoo.exceptions import UserError

		
class account_invoice(models.Model):
	_inherit ='account.move'
	
	manual_currency_rate_active = fields.Boolean('Apply Manual Exchange',copy=False)
	manual_currency_rate = fields.Float('Rate', digits=(12, 6),copy=False)
	c_purchase_id = fields.Many2one('purchase.order',string="Purchased Id")
	applied_already = fields.Boolean("Applied Already")


class account_invoice_line(models.Model):
	_inherit ='account.move.line'
	
	manual_currency_rate = fields.Float('Rate', digits=(12, 6),copy=False)
	is_manual_rate_appllied = fields.Boolean("Is Manual Rate Appllied")

	@api.model
	def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
		''' This method is used to recompute the values of 'amount_currency', 'debit', 'credit' due to a change made
		in some business fields (affecting the 'price_subtotal' field).

		:param price_subtotal:  The untaxed amount.
		:param move_type:       The type of the move.
		:param currency:        The line's currency.
		:param company:         The move's company.
		:param date:            The move's date.
		:return:                A dictionary containing 'debit', 'credit', 'amount_currency'.
		'''
		if move_type in self.move_id.get_outbound_types():
			sign = 1
		elif move_type in self.move_id.get_inbound_types():
			sign = -1
		else:
			sign = 1

		amount_currency = price_subtotal * sign

		if not self.move_id.applied_already and  self.move_id.manual_currency_rate_active and self.move_id.manual_currency_rate != 0 and self.is_manual_rate_appllied == False :
			if amount_currency != 0 and self.move_id.manual_currency_rate != 0 :
				balance = amount_currency / self.move_id.manual_currency_rate
				self.is_manual_rate_appllied = True
			else:
				balance = currency._convert(amount_currency, company.currency_id, company, date or fields.Date.context_today(self))

		else:
			balance = currency._convert(amount_currency, company.currency_id, company, date or fields.Date.context_today(self))

		return {
			'amount_currency': amount_currency,
			'currency_id': currency.id,
			'debit': balance > 0.0 and balance or 0.0,
			'credit': balance < 0.0 and -balance or 0.0,
		}
	

	@api.onchange('product_id')
	def _onchange_product_id(self):
		for line in self:
			if not line.product_id or line.display_type in ('line_section', 'line_note'):
				continue

			line.name = line._get_computed_name()
			line.account_id = line._get_computed_account()
			line.tax_ids = line._get_computed_taxes()
			line.product_uom_id = line._get_computed_uom()
			line.price_unit = line._get_computed_price_unit()

			# price_unit and taxes may need to be adapted following Fiscal Position
			line._set_price_and_tax_after_fpos()

			# Convert the unit price to the invoice's currency.
			company = line.move_id.company_id
			line.price_unit = company.currency_id._convert(line.price_unit, line.move_id.currency_id, company, line.move_id.date, round=False)
			line.is_manual_rate_appllied = False


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
