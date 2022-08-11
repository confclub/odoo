# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _


class account_payment(models.TransientModel):
	_inherit ='account.payment.register'

	manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
	manual_currency_rate = fields.Float('Rate', digits=(12, 6))
	applied_already = fields.Boolean("Applied Already")

	@api.model
	def default_get(self, default_fields):
		rec = super(account_payment, self).default_get(default_fields)
		active_ids = self._context.get('active_ids') or self._context.get('active_id')
		active_model = self._context.get('active_model')

		# Check for selected invoices ids
		if not active_ids or active_model != 'account.move':
			return rec
		invoices = self.env['account.move'].browse(active_ids).filtered(lambda move: move.is_invoice(include_receipts=True))
		for inv in invoices:
			crncy_rate_active = inv.manual_currency_rate_active
			crncy_rate = inv.manual_currency_rate

			rec.update({
				'manual_currency_rate_active':crncy_rate_active,
				'manual_currency_rate':crncy_rate,
				'applied_already' : True if crncy_rate_active else False,
			})
		return rec

	@api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date', 'manual_currency_rate')
	def _compute_amount(self):
		for wizard in self:
			if wizard.source_currency_id == wizard.currency_id:
				# Same currency.
				wizard.amount = wizard.source_amount_currency
			elif wizard.currency_id == wizard.company_id.currency_id:
				# Payment expressed on the company's currency.
				wizard.amount = wizard.source_amount
			else:
				# Foreign currency on payment different than the one set on the journal entries.
				amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
				wizard.amount = amount_payment_currency

	@api.depends('amount')
	def _compute_payment_difference(self):
		for wizard in self:
			if wizard.source_currency_id == wizard.currency_id:
				# Same currency.
				wizard.payment_difference = wizard.source_amount_currency - wizard.amount
			elif wizard.currency_id == wizard.company_id.currency_id:
				# Payment expressed on the company's currency.
				wizard.payment_difference = wizard.source_amount - wizard.amount
			else:
				# Foreign currency on payment different than the one set on the journal entries.
				amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
				wizard.payment_difference = amount_payment_currency - wizard.amount


	def _create_payment_vals_from_wizard(self):
		res = super(account_payment, self)._create_payment_vals_from_wizard()
		if self.manual_currency_rate_active:
			res.update({
				'manual_currency_rate_active': self.manual_currency_rate_active, 
				'manual_currency_rate': self.manual_currency_rate,
				'applied_already' : True if self.applied_already else False,
			})
		return res

	def _create_payment_vals_from_batch(self,batch_result):
		res = super(account_payment, self)._create_payment_vals_from_batch(batch_result)
		if self.manual_currency_rate_active:
			res.update({
				'manual_currency_rate_active': self.manual_currency_rate_active, 
				'manual_currency_rate': self.manual_currency_rate,
				'applied_already' : True if self.applied_already else False,
			})
		return res



class AccountPayment(models.Model):
	_inherit = "account.payment"
	_description = "Payments"


	manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
	manual_currency_rate = fields.Float('Rate', digits=(12, 6))
	applied_already = fields.Boolean("Applied Already")


	def _prepare_move_line_default_vals(self, write_off_line_vals=None):
		''' Prepare the dictionary to create the default account.move.lines for the current payment.
		:param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
			* amount:       The amount to be added to the counterpart amount.
			* name:         The label to set on the line.
			* account_id:   The account on which create the write-off.
		:return: A list of python dictionary to be passed to the account.move.line's 'create' method.
		'''
		self.ensure_one()
		write_off_line_vals = write_off_line_vals or {}

		if not self.journal_id.payment_debit_account_id or not self.journal_id.payment_credit_account_id:
			raise UserError(_(
				"You can't create a new payment without an outstanding payments/receipts accounts set on the %s journal."
			) % self.journal_id.display_name)

		# Compute amounts.
		write_off_amount = write_off_line_vals.get('amount', 0.0)

		if self.payment_type == 'inbound':
			# Receive money.
			counterpart_amount = -self.amount
			write_off_amount *= -1
		elif self.payment_type == 'outbound':
			# Send money.
			counterpart_amount = self.amount
		else:
			counterpart_amount = 0.0
			write_off_amount = 0.0

		if self.manual_currency_rate_active and not self.applied_already and self.manual_currency_rate != 0:

			balance = counterpart_amount / self.manual_currency_rate
			counterpart_amount_currency = counterpart_amount
			write_off_balance = write_off_amount / self.manual_currency_rate
			write_off_amount_currency = write_off_amount
			currency_id = self.currency_id.id
		else:
			balance = self.currency_id._convert(counterpart_amount, self.company_id.currency_id, self.company_id, self.date)
			counterpart_amount_currency = counterpart_amount
			write_off_balance = self.currency_id._convert(write_off_amount, self.company_id.currency_id, self.company_id, self.date)
			write_off_amount_currency = write_off_amount
			currency_id = self.currency_id.id

		if self.is_internal_transfer:
			if self.payment_type == 'inbound':
				liquidity_line_name = _('Transfer to %s', self.journal_id.name)
			else: # payment.payment_type == 'outbound':
				liquidity_line_name = _('Transfer from %s', self.journal_id.name)
		else:
			liquidity_line_name = self.payment_reference

		# Compute a default label to set on the journal items.

		payment_display_name = {
			'outbound-customer': _("Customer Reimbursement"),
			'inbound-customer': _("Customer Payment"),
			'outbound-supplier': _("Vendor Payment"),
			'inbound-supplier': _("Vendor Reimbursement"),
		}

		default_line_name = self.env['account.move.line']._get_default_line_name(
			payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
			self.amount,
			self.currency_id,
			self.date,
			partner=self.partner_id,
		)

		line_vals_list = [
			# Liquidity line.
			{
				'name': liquidity_line_name or default_line_name,
				'date_maturity': self.date,
				'amount_currency': -counterpart_amount_currency,
				'currency_id': currency_id,
				'debit': balance < 0.0 and -balance or 0.0,
				'credit': balance > 0.0 and balance or 0.0,
				'partner_id': self.partner_id.id,
				'account_id': self.journal_id.payment_debit_account_id.id if balance < 0.0 else self.journal_id.payment_credit_account_id.id,
			},
			# Receivable / Payable.
			{
				'name': self.payment_reference or default_line_name,
				'date_maturity': self.date,
				'amount_currency': counterpart_amount_currency + write_off_amount_currency if currency_id else 0.0,
				'currency_id': currency_id,
				'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
				'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
				'partner_id': self.partner_id.id,
				'account_id': self.destination_account_id.id,
			},
		]
		if write_off_balance:
			# Write-off line.
			line_vals_list.append({
				'name': write_off_line_vals.get('name') or default_line_name,
				'amount_currency': -write_off_amount_currency,
				'currency_id': currency_id,
				'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
				'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
				'partner_id': self.partner_id.id,
				'account_id': write_off_line_vals.get('account_id'),
			})

		return line_vals_list


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
