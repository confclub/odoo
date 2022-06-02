# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    templ_attribut_compute = fields.Char(compute='_compute_template_attributes', string='Template Attribute Compute')


    def _compute_template_attributes(self):
        i = 1
        for pro in self:
            i += 1
            attr_list = {"name": "pack",
                         "values": ["single"],
                         "position": i}
            if pro.product_variant_ids:
                if pro.product_variant_ids[0].variant_package_ids:
                    for pack in pro.product_variant_ids[0].variant_package_ids:
                        attr_list["values"].append(pack.value_name)
            pro.templ_attribut_compute = attr_list

    def write(self, vals):
        """
        This method use to archive/unarchive shopify product templates base on odoo product templates.
        :parameter: self, vals
        :return: res
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 09/12/2019.
        :Task id: 158502
        """
        if 'active' in vals.keys():
            shopify_product_template_obj = self.env['shopify.product.template.ept']
            for template in self:
                shopify_templates = shopify_product_template_obj.search(
                    [('product_tmpl_id', '=', template.id)])
                if vals.get('active'):
                    shopify_templates = shopify_product_template_obj.search(
                        [('product_tmpl_id', '=', template.id), ('active', '=', False)])
                shopify_templates and shopify_templates.write({'active': vals.get('active')})
        res = super(ProductTemplate, self).write(vals)
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'


    price_listed = fields.Float(compute='_compute_varient_price', string='Fixed Price')
    attribut_compute = fields.Char(compute='_compute_attributes', string='Attribute Compute')

    def _compute_varient_price(self):
        for pro in self:
            extra_price = self.env['product.pricelist.item'].search([('product_id', '=', pro.id)], limit=1)
            if extra_price:
                pro.price_listed = extra_price.fixed_price
            else:
                pro.price_listed = 0

    def _compute_attributes(self):
        for pro in self:
            # attr_list = {}
            # if pro.product_template_attribute_value_ids:
            #     for temp_attr in pro.product_template_attribute_value_ids:
            #         attr_list[pro.default_code] = str(temp_attr.name) + str(',') + "Single"
            # if pro.variant_package_ids:
            #     for att in pro.variant_package_ids:
            #         attr_list[att.code] = str(temp_attr.name) + str(',') + att.value_name
            pro.attribut_compute = 'attr_list'

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        # TDE FIXME: delegate to template or not ? fields are reencoded here ...
        # compatibility about context keys used a bit everywhere in the code
        if not uom and self._context.get('uom'):
            uom = self.env['uom.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])

        products = self
        if price_type == 'standard_price':
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost for users not in this group
            # We fetch the standard price as the superuser
            products = self.with_company(company or self.env.company).sudo()

        prices = dict.fromkeys(self.ids, 0.0)
        for product in products:
            prices[product.id] = product[price_type] or 0.0
            if price_type == 'list_price':
                # changing here by me
                prices[product.id] = product.price_listed
                # we need to add the price from the attributes that do not generate variants
                # (see field product.attribute create_variant)
                if self._context.get('no_variant_attributes_price_extra'):
                    # we have a list of price_extra that comes from the attribute values, we need to sum all that
                    prices[product.id] += sum(self._context.get('no_variant_attributes_price_extra'))

            if uom:
                prices[product.id] = product.uom_id._compute_price(prices[product.id], uom)

            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                prices[product.id] = product.currency_id._convert(
                    prices[product.id], currency, product.company_id, fields.Date.today())

        return prices

    def write(self, vals):
        """
        This method use to archive/unarchive shopify product base on odoo product.
        :parameter: self, vals
        :return: res
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 30/03/2019.
        """
        if 'active' in vals.keys():
            shopify_product_product_obj = self.env['shopify.product.product.ept']
            for product in self:
                shopify_product = shopify_product_product_obj.search(
                    [('product_id', '=', product.id)])
                if vals.get('active'):
                    shopify_product = shopify_product_product_obj.search(
                        [('product_id', '=', product.id), ('active', '=', False)])
                shopify_product and shopify_product.write({'active': vals.get('active')})
        res = super(ProductProduct, self).write(vals)
        return res
