# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import Warning
from odoo.tools.misc import formatLang, get_lang


class SaleOrder(models.Model):
	_inherit ='sale.order'
	
	sale_manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
	sale_manual_currency_rate = fields.Float('Rate', digits=(12, 6))


class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	@api.onchange('product_id')
	def product_id_change(self):
		if not self.product_id:
			return
		valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
		# remove the is_custom values that don't belong to this template
		for pacv in self.product_custom_attribute_value_ids:
			if pacv.custom_product_template_attribute_value_id not in valid_values:
				self.product_custom_attribute_value_ids -= pacv

		# remove the no_variant attributes that don't belong to this template
		for ptav in self.product_no_variant_attribute_value_ids:
			if ptav._origin not in valid_values:
				self.product_no_variant_attribute_value_ids -= ptav

		vals = {}
		if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
			vals['product_uom'] = self.product_id.uom_id
			vals['product_uom_qty'] = self.product_uom_qty or 1.0

		product = self.product_id.with_context(
			lang=get_lang(self.env, self.order_id.partner_id.lang).code,
			partner=self.order_id.partner_id,
			quantity=vals.get('product_uom_qty') or self.product_uom_qty,
			date=self.order_id.date_order,
			pricelist=self.order_id.pricelist_id.id,
			uom=self.product_uom.id
		)

		vals.update(name=self.get_sale_order_line_multiline_description_sale(product))

		self._compute_tax_id()

		if self.order_id.pricelist_id and self.order_id.partner_id:
			vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
		
			price = vals['price_unit']
			if self.order_id.sale_manual_currency_rate_active and price != 0 and self.order_id.sale_manual_currency_rate != 0:
				sale_manual_currency_rate = price / self.order_id.sale_manual_currency_rate
				vals['price_unit'] = sale_manual_currency_rate
		self.update(vals)

		title = False
		message = False
		result = {}
		warning = {}
		if product.sale_line_warn != 'no-message':
			title = _("Warning for %s", product.name)
			message = product.sale_line_warn_msg
			warning['title'] = title
			warning['message'] = message
			result = {'warning': warning}
			if product.sale_line_warn == 'block':
				self.product_id = False

		return result


	@api.onchange('product_uom', 'product_uom_qty')
	def product_uom_change(self):
		if not self.product_uom or not self.product_id:
			self.price_unit = 0.0
			return
		if self.order_id.pricelist_id and self.order_id.partner_id:
			product = self.product_id.with_context(
				lang=self.order_id.partner_id.lang,
				partner=self.order_id.partner_id,
				quantity=self.product_uom_qty,
				date=self.order_id.date_order,
				pricelist=self.order_id.pricelist_id.id,
				uom=self.product_uom.id,
				fiscal_position=self.env.context.get('fiscal_position')
			)
			self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

		if self.order_id.sale_manual_currency_rate_active and self.price_unit != 0 and self.order_id.sale_manual_currency_rate != 0:
			sale_manual_currency_rate = self.price_unit  / self.order_id.sale_manual_currency_rate
			self.price_unit = sale_manual_currency_rate


class SaleAdvancePaymentInv(models.TransientModel):
	_inherit = "sale.advance.payment.inv"

	def _create_invoice(self, order, so_line, amount):
		res = super(SaleAdvancePaymentInv,self)._create_invoice(order, so_line, amount)
		if order.sale_manual_currency_rate_active:
			res.write({
				'manual_currency_rate_active':order.sale_manual_currency_rate_active,
				'manual_currency_rate':order.sale_manual_currency_rate
			})
		return res


class SaleOrder(models.Model):
	_inherit = "sale.order"

	def _create_invoices(self, grouped=False, final=False):
		res = super(SaleOrder,self)._create_invoices(grouped=grouped, final=final)
		invoice_obj = self.env['account.move'].browse(res.id)
		for ordr in self:
			if ordr.sale_manual_currency_rate_active:
				invoice_obj.write({
					'manual_currency_rate_active':self.sale_manual_currency_rate_active,
					'manual_currency_rate':self.sale_manual_currency_rate,
					'applied_already' : True if self.sale_manual_currency_rate_active else False,
				})
		return invoice_obj
