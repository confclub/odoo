# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _


class AccountReconciliationInherit(models.AbstractModel):
	_inherit = 'account.reconciliation.widget'

	####################################################
	# Public
	####################################################

	@api.model
	def process_bank_statement_line(self, st_line_ids, data):
		""" Handles data sent from the bank statement reconciliation widget
			(and can otherwise serve as an old-API bridge)

			:param st_line_ids
			:param list of dicts data: must contains the keys
				'counterpart_aml_dicts', 'payment_aml_ids' and 'new_aml_dicts',
				whose value is the same as described in process_reconciliation
				except that ids are used instead of recordsets.
			:returns dict: used as a hook to add additional keys.
		"""
		st_lines = self.env['account.bank.statement.line'].browse(st_line_ids)
		ctx = dict(self._context, force_price_include=False)

		for st_line, datum in zip(st_lines, data):
			if datum.get('partner_id') is not None:
				st_line.write({'partner_id': datum['partner_id'],'manual_currency_rate':datum.get('manual_currency_rate')})
			st_line.with_context(ctx).reconcile(datum.get('lines_vals_list', []), to_check=datum.get('to_check', False))
		return {'statement_line_ids': st_lines}


class AccountBankStatementLineInherit(models.Model):
	_inherit = "account.bank.statement.line"

	@api.model
	def _prepare_liquidity_move_line_vals(self):
		''' Prepare values to create a new account.move.line record corresponding to the
		liquidity line (having the bank/cash account).
		:return:        The values to create a new account.move.line record.
		'''
		self.ensure_one()

		statement = self.statement_id
		journal = statement.journal_id
		company_currency = journal.company_id.currency_id
		journal_currency = journal.currency_id if journal.currency_id != company_currency else False

		if self.foreign_currency_id and journal_currency:
			currency_id = journal_currency.id
			if self.foreign_currency_id == company_currency:
				amount_currency = self.amount
				if self.manual_currency_rate != 0 and self.amount != 0 :
					balance = self.amount / self.manual_currency_rate
				else:
					balance = self.amount_currency
			else:
				amount_currency = self.amount
				if self.manual_currency_rate != 0 and self.amount != 0 :
					balance = self.amount / self.manual_currency_rate
				else:
					balance = journal_currency._convert(amount_currency, company_currency, journal.company_id, self.date)
		elif self.foreign_currency_id and not journal_currency:
			amount_currency = self.amount_currency
			if self.manual_currency_rate != 0 and self.amount != 0 :
				balance = self.amount / self.manual_currency_rate
			else:
				balance = self.amount
			currency_id = self.foreign_currency_id.id
		elif not self.foreign_currency_id and journal_currency:
			currency_id = journal_currency.id
			amount_currency = self.amount
			if self.manual_currency_rate != 0 and self.amount != 0 :
				balance = self.amount / self.manual_currency_rate
			else:
				balance = journal_currency._convert(amount_currency, journal.company_id.currency_id, journal.company_id, self.date)
		else:
			currency_id = company_currency.id
			amount_currency = self.amount
			if self.manual_currency_rate != 0 and self.amount != 0 :
				balance = self.amount / self.manual_currency_rate
			else:
				balance = self.amount
		return {
			'name': self.payment_ref,
			'move_id': self.move_id.id,
			'partner_id': self.partner_id.id,
			'currency_id': currency_id,
			'account_id': journal.default_account_id.id,
			'debit': balance > 0 and balance or 0.0,
			'credit': balance < 0 and -balance or 0.0,
			'amount_currency': amount_currency,
		}

	@api.model
	def _prepare_counterpart_move_line_vals(self, counterpart_vals, move_line=None):
		''' Prepare values to create a new account.move.line move_line.
		By default, without specified 'counterpart_vals' or 'move_line', the counterpart line is
		created using the suspense account. Otherwise, this method is also called during the
		reconciliation to prepare the statement line's journal entry. In that case,
		'counterpart_vals' will be used to create a custom account.move.line (from the reconciliation widget)
		and 'move_line' will be used to create the counterpart of an existing account.move.line to which
		the newly created journal item will be reconciled.
		:param counterpart_vals:    A python dictionary containing:
			'balance':                  Optional amount to consider during the reconciliation. If a foreign currency is set on the
										counterpart line in the same foreign currency as the statement line, then this amount is
										considered as the amount in foreign currency. If not specified, the full balance is took.
										This value must be provided if move_line is not.
			'amount_residual':          The residual amount to reconcile expressed in the company's currency.
										/!\ This value should be equivalent to move_line.amount_residual except we want
										to avoid browsing the record when the only thing we need in an overview of the
										reconciliation, for example in the reconciliation widget.
			'amount_residual_currency': The residual amount to reconcile expressed in the foreign's currency.
										Using this key doesn't make sense without passing 'currency_id' in vals.
										/!\ This value should be equivalent to move_line.amount_residual_currency except
										we want to avoid browsing the record when the only thing we need in an overview
										of the reconciliation, for example in the reconciliation widget.
			**kwargs:                   Additional values that need to land on the account.move.line to create.
		:param move_line:           An optional account.move.line move_line representing the counterpart line to reconcile.
		:return:                    The values to create a new account.move.line move_line.
		'''
		self.ensure_one()

		statement = self.statement_id
		journal = statement.journal_id
		company_currency = journal.company_id.currency_id
		journal_currency = journal.currency_id or company_currency
		foreign_currency = self.foreign_currency_id or journal_currency or company_currency
		statement_line_rate = (self.amount_currency / self.amount) if self.amount else 0.0
		balance_to_reconcile = counterpart_vals.pop('balance', None)
		amount_residual = -counterpart_vals.pop('amount_residual', move_line.amount_residual if move_line else 0.0) \
			if balance_to_reconcile is None else balance_to_reconcile
		amount_residual_currency = -counterpart_vals.pop('amount_residual_currency', move_line.amount_residual_currency if move_line else 0.0)\
			if balance_to_reconcile is None else balance_to_reconcile

		if 'currency_id' in counterpart_vals:
			currency_id = counterpart_vals['currency_id'] or company_currency.id
		elif move_line:
			currency_id = move_line.currency_id.id or company_currency.id
		else:
			currency_id = foreign_currency.id

		if currency_id not in (foreign_currency.id, journal_currency.id):
			currency_id = company_currency.id
			amount_residual_currency = 0.0

		amounts = {
			company_currency.id: 0.0,
			journal_currency.id: 0.0,
			foreign_currency.id: 0.0,
		}

		amounts[currency_id] = amount_residual_currency
		amounts[company_currency.id] = amount_residual

		if currency_id == journal_currency.id and journal_currency != company_currency:
			if foreign_currency != company_currency:
				amounts[company_currency.id] = journal_currency._convert(amounts[currency_id], company_currency, journal.company_id, self.date)
			if statement_line_rate:
				amounts[foreign_currency.id] = amounts[currency_id] * statement_line_rate
		elif currency_id == foreign_currency.id and self.foreign_currency_id:
			if statement_line_rate:
				amounts[journal_currency.id] = amounts[foreign_currency.id] / statement_line_rate
				if foreign_currency != company_currency:
					amounts[company_currency.id] = journal_currency._convert(amounts[journal_currency.id], company_currency, journal.company_id, self.date)
		else:
			amounts[journal_currency.id] = company_currency._convert(amounts[company_currency.id], journal_currency, journal.company_id, self.date)
			if statement_line_rate:
				amounts[foreign_currency.id] = amounts[journal_currency.id] * statement_line_rate

		if foreign_currency == company_currency and journal_currency != company_currency and self.foreign_currency_id:
			if self.manual_currency_rate != 0 and self.amount != 0 :
				balance = -( self.amount / self.manual_currency_rate )
			else:
				balance = amounts[foreign_currency.id]
		else:
			if self.manual_currency_rate != 0 and self.amount != 0 :
				balance = -( self.amount / self.manual_currency_rate )
			else:
				balance = amounts[company_currency.id]

		if foreign_currency != company_currency and self.foreign_currency_id:
			amount_currency = amounts[foreign_currency.id]
			currency_id = foreign_currency.id
		elif journal_currency != company_currency and not self.foreign_currency_id:
			amount_currency = amounts[journal_currency.id]
			currency_id = journal_currency.id
		else:
			amount_currency = amounts[company_currency.id]
			currency_id = company_currency.id
		return {
			**counterpart_vals,
			'name': counterpart_vals.get('name', move_line.name if move_line else ''),
			'move_id': self.move_id.id,
			'partner_id': self.partner_id.id or (move_line.partner_id.id if move_line else False),
			'currency_id': currency_id,
			'account_id': counterpart_vals.get('account_id', move_line.account_id.id if move_line else False),
			'debit': balance if balance > 0.0 else 0.0,
			'credit': -balance if balance < 0.0 else 0.0,
			'amount_currency': amount_currency,
		}
	
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
