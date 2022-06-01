# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import json
import logging
import time
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError
from .. import shopify
from ..shopify.pyactiveresource.connection import ClientError

_logger = logging.getLogger("Shopify")


class ShopifyProductProductEpt(models.Model):
    _name = "shopify.product.product.ept"
    _description = "Shopify Product Product"
    _order = "sequence"

    sequence = fields.Integer("Position", default=1)
    name = fields.Char("Title")
    shopify_instance_id = fields.Many2one("shopify.instance.ept", "Instance", required=1)
    default_code = fields.Char()
    product_id = fields.Many2one("product.product", required=1)
    shopify_template_id = fields.Many2one("shopify.product.template.ept", required=1,
                                          ondelete="cascade")
    exported_in_shopify = fields.Boolean(default=False)
    variant_id = fields.Char()
    fix_stock_type = fields.Selection([("fix", "Fix"), ("percentage", "Percentage")])
    fix_stock_value = fields.Float(digits=0)
    created_at = fields.Datetime()
    updated_at = fields.Datetime()
    inventory_item_id = fields.Char()
    check_product_stock = fields.Selection([("continue", "Allow"), ("deny", "Denied")],
                                           string="Sale out of stock products?",
                                           default="deny",
                                           help="If true than customers are allowed to place an order for the product"
                                                "variant when it is out of stock.")
    inventory_management = fields.Selection([("shopify", "Shopify tracks this product Inventory"),
                                             ("Dont track Inventory", "Don't track Inventory")],
                                            default="shopify",
                                            help="If you select 'Shopify tracks this product Inventory' than shopify"
                                                 "tracks this product inventory.if select 'Don't track Inventory' then"
                                                 "after we can not update product stock from odoo")
    active = fields.Boolean(default=True)
    shopify_image_ids = fields.One2many("shopify.product.image.ept", "shopify_variant_id")
    taxable = fields.Boolean(default=True)
    variant_package_ids = fields.One2many("shopify.variant.package", "shopify_product_id")

    def toggle_active(self):
        """
        Archiving related shopify product template if there is only one active shopify product
        :parameter: self
        :return: res
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 09/12/2019.
        :Task id: 158502
        """
        with_one_active = self.filtered(lambda x: len(x.shopify_template_id.shopify_product_ids) == 1)
        for product in with_one_active:
            product.shopify_template_id.toggle_active()
        return super(ShopifyProductProductEpt, self - with_one_active).toggle_active()

    def shopify_create_variant_product(self, result, instance, price):
        """
        This method used to search the attribute and attribute in Odoo and based on attribute it's created a product
        template and variant.
        @param : self,barcode,sku
        @return: Boolean
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 09/10/2019.
        """
        product_template_obj = self.env["product.template"]

        template_title = result.get("title", "")
        brand_name = False
        if result.get('vendor'):
            brand_name = self.env['common.product.brand.ept'].search([('name', '=', result.get('vendor'))]).id
            if not brand_name:
                brand_name = self.env['common.product.brand.ept'].create({
                    'name': result['vendor'],
                }).id

        attrib_line_vals = self.shopify_prepare_attribute_vals(result)
        if attrib_line_vals:
            product_template = product_template_obj.create({"name": template_title,
                                                            "type": "product",
                                                            "attribute_line_ids": attrib_line_vals,
                                                            "description_sale": template_title,
                                                            "description": result.get("body_html"),
                                                            "invoice_policy": "order",
                                                            "product_brand_id": brand_name,
                                                            })

            self.shopify_update_price(instance, product_template, price)
            odoo_product = self.shopify_set_variant_sku(result, product_template, instance)

            if odoo_product:
                return product_template
        return False

    def shopify_prepare_attribute_vals(self, result):
        """This method use to prepare a attribute values list.
            @param : self, result
            @return: vals
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 22/10/2019.
        """
        product_attribute_obj = self.env["product.attribute"]
        product_attribute_value_obj = self.env["product.attribute.value"]
        attrib_line_vals = []
        for attrib in result.get("options"):
            attrib_name = attrib.get("name")
            attrib_values = attrib.get("values")
            attribute = product_attribute_obj.get_attribute(attrib_name, auto_create=True)[0]
            attr_val_ids = []

            for attrib_value in attrib_values:
                attribute_value = product_attribute_value_obj.get_attribute_values(attrib_value, attribute.id,
                                                                                   auto_create=True)
                if attribute_value:
                    attribute_value = attribute_value[0]
                    attr_val_ids.append(attribute_value.id)

            if attr_val_ids:
                attribute_line_ids_data = [0, False,
                                           {"attribute_id": attribute.id, "value_ids": [[6, False, attr_val_ids]]}]
                attrib_line_vals.append(attribute_line_ids_data)
        return attrib_line_vals

    def shopify_update_price(self, instance, product_template, price):
        """This method use set price in product and also set product price in pricelist.
            @param : self, result
            @return: vals
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 22/10/2019.
        """
        if instance.shopify_pricelist_id.currency_id.id == product_template.company_id.currency_id.id:
            product_template.write({"list_price": price.replace(",", ".")})
        else:
            instance_currency = instance.shopify_pricelist_id.currency_id
            product_company_currency = product_template.company_id.currency_id
            date = self._context.get("date") or fields.Date.today()
            company = self.env["res.company"].browse(self._context.get("company_id")) or self.env.company
            amount = instance_currency._convert(float(price), product_company_currency, company, date)
            product_template.write({"list_price": amount})

        return True

    def shopify_set_variant_sku(self, result, product_template, instance):
        """This method set the variant SKU based on the attribute and attribute value.
            @param : self, result, product_template, instance
            @return: True
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 10/10/2019.
        """
        product_attribute_obj = self.env["product.attribute"]
        product_attribute_value_obj = self.env["product.attribute.value"]
        product_template_attribute_value_obj = self.env["product.template.attribute.value"]
        odoo_product_obj = self.env["product.product"]

        for variation in result.get("variants"):
            sku = variation.get("sku")
            price = variation.get("price")
            barcode = variation.get("barcode") or False
            if barcode and barcode.__eq__("false"):
                barcode = False
            template_attribute_value_ids = []
            domain = []
            odoo_product = False
            variation_attributes = []
            option_name = []
            for options in result.get("options"):
                attrib_name = options.get("name")
                attrib_name and option_name.append(attrib_name)

            option1 = variation.get("option1", False)
            option2 = variation.get("option2", False)
            option3 = variation.get("option3", False)
            if option1 and (option_name and option_name[0]):
                variation_attributes.append({"name": option_name[0], "option": option1})
            if option2 and (option_name and option_name[1]):
                variation_attributes.append({"name": option_name[1], "option": option2})
            if option3 and (option_name and option_name[2]):
                variation_attributes.append({"name": option_name[2], "option": option3})

            for variation_attribute in variation_attributes:
                attribute_val = variation_attribute.get("option")
                attribute_name = variation_attribute.get("name")
                product_attribute = product_attribute_obj.search([("name", "=ilike", attribute_name)], limit=1)
                if product_attribute:
                    product_attribute_value = product_attribute_value_obj.get_attribute_values(attribute_val,
                                                                                               product_attribute.id)
                if product_attribute_value:
                    product_attribute_value = product_attribute_value[0]
                    template_attribute_value_id = product_template_attribute_value_obj.search(
                        [("product_attribute_value_id", "=", product_attribute_value.id),
                         ("attribute_id", "=", product_attribute.id), ("product_tmpl_id", "=", product_template.id)],
                        limit=1)
                    template_attribute_value_id and template_attribute_value_ids.append(template_attribute_value_id.id)

            for template_attribute_value in template_attribute_value_ids:
                tpl = ("product_template_attribute_value_ids", "=", template_attribute_value)
                domain.append(tpl)

            domain and domain.append(("product_tmpl_id", "=", product_template.id))
            if domain:
                odoo_product = odoo_product_obj.search(domain)
            if odoo_product and sku:
                odoo_product.write({"default_code": sku})
            # if barcode and odoo_product: # Changing
            #     odoo_product.write({"barcode": barcode})
            #     odoo_product.write({"barcode": barcode})
            if price and odoo_product:
                if instance.shopify_pricelist_id.currency_id.id == product_template.company_id.currency_id.id:
                    odoo_product.write({"list_price": price.replace(",", ".")})
                else:
                    instance_currency = instance.shopify_pricelist_id.currency_id
                    product_company_currency = product_template.company_id.currency_id
                    date = self._context.get("date") or fields.Date.today()
                    company = self.env["res.company"].browse(
                        self._context.get("company_id")) or self.env.company
                    amount = instance_currency._convert(float(price), product_company_currency,
                                                        company, date)
                    odoo_product.write({"list_price": amount})

        return odoo_product

    def prepare_shopify_product_for_update_export(self, new_product, template, instance, is_set_basic_detail,
                                                  is_publish, is_set_price):
        """
        This method will be used for both Export and Updating product in Shopify.
        @author: Maulik Barad on Date 21-Sep-2020.
        """
        if is_set_basic_detail or is_publish:
            self.shopify_set_template_value_in_shopify_obj(new_product, template, is_publish, is_set_basic_detail)
        if is_set_basic_detail or is_set_price:
            variants = []
            for variant in template.shopify_product_ids:
                variant_vals = self.shopify_prepare_variant_vals(instance, variant, is_set_price,
                                                                 is_set_basic_detail)
                variants.append(variant_vals)
            new_product.variants = variants
            self.prepare_export_update_product_attribute_vals(template, new_product)
        return True

    def shopify_export_products(self, instance, is_set_basic_detail, is_set_price, is_set_images, is_publish,
                                templates):
        """
        This method used to Export the shopify product from Odoo to Shopify.
        @author: Nilesh Parmar @Emipro Technologies Pvt. Ltd on date 19/11/2019.
        """
        common_log_obj = self.env["common.log.book.ept"]
        common_log_line_obj = self.env["common.log.lines.ept"]
        model = "shopify.product.product.ept"
        model_id = common_log_line_obj.get_model_id(model)
        instance.connect_in_shopify()
        vals = {"type": "export",
                "module": "shopify_ept",
                "shopify_instance_id": instance.id,
                "model_id": model_id}
        log_book_id = common_log_obj.create(vals)

        for template in templates:
            new_product = shopify.Product()

            self.prepare_shopify_product_for_update_export(new_product, template, instance, is_set_basic_detail,
                                                           is_publish, is_set_price)

            result = new_product.save()

            if not result:
                message = "Product %s not exported in Shopify Store." % template.name
                self.shopify_export_product_log_line(message, model_id, log_book_id)
            if result:
                self.update_products_details_shopify_third_layer(new_product, template, is_publish)
            if new_product and is_set_images:
                self.export_product_images(instance, shopify_template=template)
            self._cr.commit()
        if not log_book_id.log_lines:
            log_book_id.unlink()
        return True

    def shopify_export_product_log_line(self, message, model_id, log_book_id):
        common_log_line_obj = self.env["common.log.lines.ept"]
        vals = {"message": message,
                "model_id": model_id,
                "log_book_id": log_book_id.id if log_book_id else False}
        common_log_line_obj.create(vals)
        return True

    def prepare_export_update_product_attribute_vals(self, template, new_product):
        if len(template.shopify_product_ids) > 1:
            attribute_list = []
            attribute_position = 1
            product_attribute_line_obj = self.env["product.template.attribute.line"]
            product_attribute_lines = product_attribute_line_obj.search(
                [("id", "in", template.product_tmpl_id.attribute_line_ids.ids)], order="attribute_id")
            for attribute_line in product_attribute_lines:
                info = {}
                attribute = attribute_line.attribute_id
                value_names = []
                for value in attribute_line.value_ids:
                    value_names.append(value.name)

                info.update({"name": attribute.name or attribute.name, "values": value_names,
                             "position": attribute_position})
                attribute_list.append(info)
                attribute_position = attribute_position + 1
                # if attribute_position > 3:
                #     break
            attrs = json.loads(template.product_tmpl_id.templ_attribut_compute.replace("'", '"'))
            attribute_list.append(attrs)
            new_product.options = attribute_list
        return True

    def update_products_in_shopify(self, instance, templates, is_set_price, is_set_images, is_publish,
                                   is_set_basic_detail):
        """
        This method is used to Update product in shopify store.
        :param instance: shopify instance id.
        :param is_set_price: if true then update price in shopify store.
        :param is_set_images: if true then update image in shopify store.
        :param is_publish: if true then publish product in shopify web.
        :param is_set_basic_detail: if true then update product basic detail.
        :return:
        @author: Nilesh Parmar @Emipro Technologies Pvt. Ltd on date 15/11/2019.
        """
        common_log_obj = self.env["common.log.book.ept"]
        common_log_line_obj = self.env["common.log.lines.ept"]
        model = "shopify.product.product.ept"
        model_id = common_log_line_obj.get_model_id(model)

        instance.connect_in_shopify()
        vals = {"type": "export",
                "module": "shopify_ept",
                "shopify_instance_id": instance.id,
                "model_id": model_id}
        log_book_id = common_log_obj.create(vals)

        for template in templates:
            if not template.shopify_tmpl_id:
                continue
            try:
                new_product = shopify.Product().find(template.shopify_tmpl_id)
            except ClientError as error:
                if hasattr(error, "response"):
                    if error.response.code == 429 and error.response.msg == "Too Many Requests":
                        time.sleep(5)
                        new_product = shopify.Product().find(template.shopify_tmpl_id)
            except Exception as error:
                message = "Template %s not found in shopify while updating Product.\nError: %s" % (
                    template.shopify_tmpl_id, str(error))
                self.shopify_export_product_log_line(message, model_id, log_book_id)
                continue

            self.prepare_shopify_product_for_update_export(new_product, template, instance, is_set_basic_detail,
                                                           is_publish, is_set_price)

            result = new_product.save()

            if result:
                self.update_products_details_shopify_third_layer(new_product, template, is_publish)
            if is_set_images:
                self.update_product_images(shopify_template=template)

            updated_at = datetime.now()
            template.write({"updated_at": updated_at})
            template.shopify_product_ids.write({"updated_at": updated_at})
        if not log_book_id.log_lines:
            log_book_id.unlink()

        return True

    def shopify_set_template_value_in_shopify_obj(self, new_product, template, is_publish, is_set_basic_detail):
        """
        This method is used to set the shopify product template values.
        :param new_product: shopify product object
        :param template: shopify product template product template
        :param is_publish: if true then publish product in shop[ify store
        :param is_set_basic_detail: if true then set the basic detail in shopify product
        :return:
        @author: Nilesh Parmar @Emipro Technologies Pvt. Ltd on date 15/11/2019.
        """
        if is_publish == "publish_product":
            published_at = datetime.utcnow()
            published_at = published_at.strftime("%Y-%m-%dT%H:%M:%S")
            new_product.published_at = published_at
            new_product.published_scope = "web"
        elif is_publish == "unpublish_product":
            new_product.published_at = None
            new_product.published_scope = "null"

        if is_set_basic_detail:
            if template.description:
                new_product.body_html = template.description
            if template.product_tmpl_id.seller_ids:
                new_product.vendor = template.product_tmpl_id.seller_ids[0].display_name
            new_product.product_type = template.shopify_product_category.name
            new_product.tags = [tag.name for tag in template.tag_ids]
            if template.template_suffix:
                new_product.template_suffix = template.template_suffix
            new_product.title = template.name

        return True

    def shopify_prepare_variant_vals(self, instance, variant, is_set_price, is_set_basic_detail):
        """This method used to prepare variant vals for export product variant from
            shopify third layer to shopify store.
            @param : instance, variant, is_set_price
            @return: variant_vals
            @author: Nilesh Parmar @Emipro Technologies Pvt. Ltd on date 15/11/2019.
        """
        variant_vals = {}
        if variant.variant_id:
            variant_vals.update({"id": variant.variant_id})
        if is_set_price:
            price = instance.shopify_pricelist_id.get_product_price(variant.product_id, 1.0, partner=False,
                                                                    uom_id=variant.product_id.uom_id.id)
            variant_vals.update({"price": float(price)})
        if is_set_basic_detail:
            # Changing is  variant.product_id.barcode or
            variant_vals.update({"barcode": "",
                                 "grams": int(variant.product_id.weight * 1000),
                                 "weight": variant.product_id.weight,
                                 "weight_unit": "kg",
                                 "requires_shipping": "true", "sku": variant.default_code,
                                 "taxable": variant.taxable and "true" or "false",
                                 "title": variant.name,
                                 })
            option_index = 0
            option_index_value = ["option1", "option2", "option3"]
            attribute_value_obj = self.env["product.template.attribute.value"]
            # att_values = attribute_value_obj.search(
            #     [("id", "in", variant.product_id.product_template_attribute_value_ids.ids)],
            #     order="attribute_id")
            att_values = json.loads(variant.product_id.attribut_compute.replace("'", '"'))
            if att_values:
                for att_value in att_values:
                    if option_index > 3:
                        continue
                    if variant.default_code == att_value:
                        attr_list = att_values[att_value].split(',')
                        for app in attr_list:
                            variant_vals.update({option_index_value[option_index]: app})
                            option_index = option_index + 1


            # for att_value in att_values:
            #     if option_index > 3:
            #         continue
            #     variant_vals.update({option_index_value[option_index]: att_value.name})
            #     option_index = option_index + 1
        print("hello")
        if variant.inventory_management == "shopify":
            variant_vals.update({"inventory_management": "shopify"})
        else:
            variant_vals.update({"inventory_management": None})

        if variant.check_product_stock == "continue":
            variant_vals.update({"inventory_policy": "continue"})
        else:
            variant_vals.update({"inventory_policy": "deny"})

        return variant_vals

    def update_products_details_shopify_third_layer(self, new_product, template, is_publish):
        """
        this method is used to update the shopify product id, created date, update date,
        public date in shopify third layer
        :param new_product: shopify store product
        :param template: shopify template
        :param is_publish: if true then update public date of shopify product
        @author: Nilesh Parmar @Emipro Technologies Pvt. Ltd on date 19/11/2019.
        """
        result_dict = new_product.to_dict()
        created_at = datetime.now()
        updated_at = datetime.now()
        tmpl_id = result_dict.get("id")
        total_variant = 1
        if result_dict.get("variants"):
            total_variant = len(result_dict.get("variants" or False))
        template_vals = {"created_at": created_at, "updated_at": updated_at,
                         "shopify_tmpl_id": tmpl_id,
                         "exported_in_shopify": True,
                         "total_variants_in_shopify": total_variant
                         }
        if is_publish == "unpublish_product":
            template.write({"published_at": False, "website_published": False})
        elif is_publish == 'publish_product_global':
            template.write({'published_at': updated_at, 'website_published': 'published_global'})
        else:
            template.write({'published_at': updated_at, 'website_published': 'published_web'})
        if not template.exported_in_shopify:
            template.write(template_vals)
        for variant_dict in result_dict.get("variants"):
            updated_at = datetime.now()
            created_at = datetime.now()
            inventory_item_id = variant_dict.get("inventory_item_id") or False
            variant_id = variant_dict.get("id")
            shopify_variant = template.shopify_search_odoo_product_variant(template.shopify_instance_id, variant_id,
                                                                           variant_dict.get("sku"),
                                                                           variant_dict.get("barcode"))[0]
            if shopify_variant and not shopify_variant.exported_in_shopify:
                shopify_variant.write({
                    "variant_id": variant_id,
                    "updated_at": updated_at,
                    "created_at": created_at,
                    "inventory_item_id": inventory_item_id,
                    "exported_in_shopify": True
                })
        return True

    def export_product_images(self, instance, shopify_template):
        """
        Author: Bhavesh Jadav  @Emipro Technologies Pvt. Ltd on date 18/12/2019.
        This method use for the export images in to shopify store
        :param instance: use for the shopify instance
        :param shopify_template: use for the shopify template
        """
        instance.connect_in_shopify()
        if not shopify_template.shopify_image_ids:
            return False

        for image in shopify_template.shopify_image_ids:
            shopify_image = shopify.Image()
            shopify_image.product_id = shopify_template.shopify_tmpl_id
            shopify_image.attachment = image.odoo_image_id.image.decode("utf-8")
            if image.odoo_image_id.template_id and image.odoo_image_id.product_id:
                shopify_image.variant_ids = [int(image.shopify_variant_id.variant_id)]
            result = shopify_image.save()
            if result:
                image.write({"shopify_image_id": shopify_image.id})

        return True

    def update_product_images(self, shopify_template):
        """
        Author:Bhavesh Jadav 18/12/2019 for the update Shopify image if image is new then export image
        :param shopify_template: use for the shopify template
        """
        if not shopify_template.shopify_image_ids:
            return False
        shopify_images = False
        try:
            shopify_images = shopify.Image().find(product_id=int(shopify_template.shopify_tmpl_id))
        except ClientError as error:
            if hasattr(error, "response"):
                if error.response.code == 429 and error.response.msg == "Too Many Requests":
                    time.sleep(5)
                    shopify_images = shopify.Image().find(product_id=shopify_template.shopify_tmpl_id)

        for image in shopify_template.shopify_image_ids:
            if not image.shopify_image_id:
                shopify_image = shopify.Image()
                shopify_image.product_id = shopify_template.shopify_tmpl_id
                shopify_image.attachment = image.odoo_image_id.image.decode("utf-8")
                if image.shopify_variant_id:
                    shopify_image.variant_ids = [int(image.shopify_variant_id.variant_id)]
                result = shopify_image.save()
                if result:
                    image.write({"shopify_image_id": shopify_image.id})
            else:
                ############################################
                # Need to discuss update binary data or not
                ############################################
                if not shopify_images:
                    continue
                for shop_image in shopify_images:
                    if int(image.shopify_image_id) == shop_image.id:
                        shopify_image = shop_image
                        shopify_image.attachment = image.odoo_image_id.image.decode("utf-8")
                        shopify_image.save()
        return True

    @api.model
    def export_stock_in_shopify(self, instance, product_ids):
        """
        Find products with below condition
            1. shopify_instance_id = instance.id
            2. exported_in_shopify = True
            3. product_id in products
        Find Shopify location for the particular instance
        Check export_stock_warehouse_ids is configured in location or not
        Get the total stock of the product with configured warehouses and update that stock in shopify location
        here we use InventoryLevel shopify API for export stock
        @author: Maulik Barad on Date 15-Sep-2020.
        """
        common_log_line_obj = self.env["common.log.lines.ept"]
        product_obj = self.env["product.product"]

        log_line_array = []
        model = "shopify.product.product.ept"
        model_id = common_log_line_obj.get_model_id(model)

        shopify_products = self.search([("shopify_instance_id", "=", instance.id),
                                        ("exported_in_shopify", "=", True),
                                        ("product_id", "in", product_ids)])
        if not shopify_products:
            return True

        instance.connect_in_shopify()
        location_ids = self.env["shopify.location.ept"].search([("instance_id", "=", instance.id)])
        if not location_ids:
            message = "Location not found for instance %s while update stock" % instance.name
            log_line_array = self.shopify_create_log(message, model_id, False, log_line_array)

        for location_id in location_ids:
            shopify_location_warehouse = location_id.export_stock_warehouse_ids or False
            if not shopify_location_warehouse:
                message = "No Warehouse found for Export Stock in Shopify Location: %s" % location_id.name
                log_line_array = self.shopify_create_log(message, model_id, False, log_line_array)
                continue

            odoo_product_ids = shopify_products.product_id.ids
            product_stock = self.check_stock(instance, odoo_product_ids, product_obj,
                                             location_id.export_stock_warehouse_ids)

            for shopify_product in shopify_products:
                odoo_product = shopify_product.product_id
                if odoo_product.type == "product":
                    if not shopify_product.inventory_item_id:
                        message = "Inventory Item Id did not found for Shopify Product Variant ID " \
                                  "%s with name %s for instance %s while Export stock" % (
                                      shopify_product.id, shopify_product.name, instance.name)
                        log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)
                        continue

                    quantity = product_stock.get(odoo_product.id, 0)
                    if shopify_product.fix_stock_type == 'fix':
                        if shopify_product.fix_stock_value < quantity:
                            quantity = shopify_product.fix_stock_value
                    elif shopify_product.fix_stock_type == 'percentage':
                        percentage_stock = int((quantity * shopify_product.fix_stock_value) / 100.0)
                        if percentage_stock < quantity:
                            quantity = percentage_stock

                    try:
                        shopify.InventoryLevel.set(location_id.shopify_location_id, shopify_product.inventory_item_id,
                                                   int(quantity))
                    except ClientError as error:
                        if hasattr(error, "response"):
                            if error.response.code == 429 and error.response.msg == "Too Many Requests":
                                time.sleep(5)
                                shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                           shopify_product.inventory_item_id,
                                                           int(quantity))
                                continue
                            message = "Error while Export stock for Product ID: %s & Product Name: '%s' for instance:" \
                                      "'%s'\nError: %s\n%s" % (odoo_product.id, odoo_product.name, instance.name,
                                                               str(error.response.code) + " " + error.response.msg,
                                                               json.loads(error.response.body.decode()).get("errors")[0]
                                                               )
                            log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)

                    except Exception as error:
                        message = "Error while Export stock for Product ID: %s & Product Name: '%s' for instance: " \
                                  "'%s'\nError: %s" % (odoo_product.id, odoo_product.name, instance.name, str(error))
                        log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)

        if len(log_line_array) > 0:
            self.create_log(log_line_array, "export", instance)

        return True

    def check_stock(self, instance, product_ids, prod_obj, warehouse):
        """
        This Method relocates check type of stock.
        :param instance: This arguments relocates instance of Shopify.
        :param product_ids: This arguments product listing id of odoo.
        :param prod_obj: This argument relocates product object of common connector.
        :param warehouse:This arguments relocates warehouse of shopify export location.
        :return: This Method return product listing stock.
        """
        product_stock = {}

        if product_ids:
            if instance.shopify_stock_field.name == "free_qty":
                product_stock = prod_obj.get_free_qty_ept(warehouse, product_ids)

            elif instance.shopify_stock_field.name == "virtual_available":
                product_stock = prod_obj.get_forecasted_qty_ept(warehouse, product_ids)

        return product_stock

    def import_shopify_stock(self, instance):
        """
        search shopify product with below condition
            1. shopify_instance_id = instance.id
            2. exported_in_shopify = True
        any is_shopify_product_adjustment is set to True in stock.inventory. Then cancel it first.
        Find the shopify locations
        Using shopify location call InventoryLevel shopify API
        Using API response create stock_inventory_line and stock_inventory with configured warehouse in location for
        import stock
        :param instance:
        :return:
        @author: Angel Patel @Emipro Technologies Pvt. Ltd.
        """
        stock_inventory_obj = self.env["stock.inventory"]
        common_log_line_obj = self.env["common.log.lines.ept"]
        model = "shopify.product.product.ept"
        model_id = common_log_line_obj.get_model_id(model)
        log_line_array = []

        inventory_adjustments = stock_inventory_obj.search(
            [("is_shopify_product_adjustment", "=", True), ("state", "!=", "done")])
        for inventory_adjustment in inventory_adjustments:
            if not inventory_adjustment.state == "cancel":
                inventory_adjustment.action_cancel_draft()
                inventory_adjustment.write({"state": "cancel"})

        templates = self.search([("shopify_instance_id", "=", instance.id), ("exported_in_shopify", "=", True)])
        if templates:
            instance.connect_in_shopify()

            location_ids = self.env["shopify.location.ept"].search(
                [("legacy", "=", False), ("instance_id", "=", instance.id)])
            if not location_ids:
                message = "Location not found for instance %s while Importing stock" % instance.name
                log_line_array = self.shopify_create_log(message, model_id, False, log_line_array)
                self.create_log(log_line_array, "import", instance)
                _logger.info(message)
                return False

            for location_id in location_ids:
                stock_inventory_array = []
                product_ids_list = []
                shopify_location_warehouse = location_id.import_stock_warehouse_id or False
                if not shopify_location_warehouse:
                    message = "No Warehouse found for importing stock in Shopify Location: %s" % location_id.name
                    log_line_array = self.shopify_create_log(message, model_id, False, log_line_array)
                    _logger.info(message)
                    continue

                try:
                    inventory_levels = shopify.InventoryLevel.find(location_ids=location_id.shopify_location_id,
                                                                   limit=250)
                    if len(inventory_levels) == 250:
                        inventory_levels = self.shopify_list_all_inventory_level(inventory_levels)
                except Exception as error:
                    message = "Error while import stock for instance %s\nError: %s" % (
                        instance.name, str(error.response.code) + " " + error.response.msg)
                    log_line_array = self.shopify_create_log(message, model_id, False, log_line_array)
                    _logger.info(message)
                    self.create_log(log_line_array, "import", instance)
                    return False

                _logger.info("Length of the total inventory item id : %s" % len(inventory_levels))
                lot_stock_id = location_id.import_stock_warehouse_id.lot_stock_id.id
                for inventory_level in inventory_levels:
                    inventory_level = inventory_level.to_dict()
                    inventory_item_id = inventory_level.get("inventory_item_id")
                    qty = inventory_level.get("available")

                    shopify_product = self.env["shopify.product.product.ept"].search(
                        [("inventory_item_id", "=", inventory_item_id), ("exported_in_shopify", "=", True),
                         ("shopify_instance_id", "=", instance.id)], limit=1)
                    if shopify_product:
                        product_id = shopify_product.product_id
                        if product_id not in product_ids_list:
                            stock_inventory_line = {
                                "product_id": product_id,
                                "location_id": lot_stock_id,
                                "product_qty": qty
                            }
                            stock_inventory_array.append(stock_inventory_line)
                            product_ids_list.append(product_id)

                if len(stock_inventory_array) > 0:
                    inventories = stock_inventory_obj.create_stock_inventory_ept(
                        stock_inventory_array, location_id.import_stock_warehouse_id.lot_stock_id, False)
                    if inventories:
                        inventory_name = 'Inventory For Instance "%s" And Shopify Location "%s"' % (
                            instance.name + " " + datetime.now().strftime("%d-%m-%Y"), location_id.name)
                        inventories.write({'is_shopify_product_adjustment': True, 'name': inventory_name})
                        _logger.info("Created %s." % inventory_name)

        if len(log_line_array) > 0:
            self.create_log(log_line_array, "import", instance)

        return True

    def shopify_list_all_inventory_level(self, result):
        """
            This method used to call the page wise data import for product stock from Shopify to Odoo.
            @param : self, result, shopify_location_id
            @author: Angel Patel @Emipro Technologies Pvt. Ltd on date 21/12/2019.
            Modify by Haresh Mori on 28/12/2019 API and Pagination changes
        """
        sum_inventory_list = []
        catch = ""
        while result:
            page_info = ""
            sum_inventory_list += result
            link = shopify.ShopifyResource.connection.response.headers.get("Link")
            if not link or not isinstance(link, str):
                return sum_inventory_list
            for page_link in link.split(","):
                if page_link.find("next") > 0:
                    page_info = page_link.split(";")[0].strip("<>").split("page_info=")[1]
                    try:
                        result = shopify.InventoryLevel.find(page_info=page_info, limit=250)
                    except ClientError as error:
                        if hasattr(error, "response"):
                            if error.response.code == 429 and error.response.msg == "Too Many Requests":
                                time.sleep(5)
                                result = shopify.InventoryLevel.find(page_info=page_info, limit=250)
                    except Exception as error:
                        raise UserError(error)
            if catch == page_info:
                break
        return sum_inventory_list

    def shopify_create_log(self, message=False, model_id=False, product=False, log_line_array=False):
        """
        Append all log_line vals and return log_line vals
        :param message:
        :param model_id:
        :param product:
        :param log_line_array:
        :return: log_line_array
        @author: Angel Patel @Emipro Technologies Pvt. Ltd on date 14/11/2019.
        @Task ID: 157623
        """
        log_line_vals = {
            "message": message,
            "model_id": model_id,
            "product_id": product and product.id or False,
            "default_code": product and product.default_code or False
        }
        log_line_array.append(log_line_vals)
        return log_line_array

    def create_log(self, log_line_array, log_type, instance):
        common_log_obj = self.env["common.log.book.ept"]
        common_log_obj.create({"type": log_type,
                               "module": "shopify_ept",
                               "shopify_instance_id": instance.id if instance else False,
                               "active": True,
                               "log_lines": [(0, 0, log_line) for log_line in log_line_array]})
        return True


class ShopifyTag(models.Model):
    _name = "shopify.tags"
    _description = "Shopify Tags"

    name = fields.Char(required=1)
    sequence = fields.Integer(required=1)
