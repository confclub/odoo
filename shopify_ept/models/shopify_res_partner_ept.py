# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class ShopifyResPartnerEpt(models.Model):
    _name = "shopify.res.partner.ept"
    _description = "Shopify Res Partner"

    partner_id = fields.Many2one("res.partner", "Partner Id", ondelete="cascade")
    shopify_instance_id = fields.Many2one("shopify.instance.ept", "Instances")
    shopify_customer_id = fields.Char("Shopify Customer Id")

    def shopify_create_contact_partner(self, vals, instance, queue_line, log_book):
        """
        This method used to create a contact type customer.
        @author: Maulik Barad on Date 09-Sep-2020.
        """
        partner_obj = self.env["res.partner"]
        common_log_line_obj = self.env["common.log.lines.ept"]

        shopify_instance_id = instance.id
        shopify_customer_id = vals.get("id", False)
        first_name = vals.get("first_name", "")
        last_name = vals.get("last_name", "")
        email = vals.get("email", "")

        if not first_name and not last_name:
            message = "First name and Last name is not found in customer data."
            model_id = common_log_line_obj.get_model_id("res.partner")
            common_log_line_obj.shopify_create_customer_log_line(message, model_id, queue_line, log_book)
            return False

        name = "%s %s" % (first_name, last_name)
        shopify_partner = self.search([("shopify_customer_id", "=", shopify_customer_id),
                                       ("shopify_instance_id", "=", shopify_instance_id)], limit=1)
        if shopify_partner:
            partner = shopify_partner.partner_id
            return partner

        shopify_partner_values = {"shopify_customer_id": shopify_customer_id,
                                  "shopify_instance_id": shopify_instance_id}
        if email:
            partner = partner_obj.search_partner_by_email(email)

            if partner:
                partner.write({"is_shopify_customer": True})
                shopify_partner_values.update({"partner_id": partner.id})
                self.create(shopify_partner_values)
                return partner

        partner_vals = self.shopify_prepare_partner_vals(vals.get("default_address", {}), instance)
        partner_vals.update({
            "name": name,
            "email": email,
            "customer_rank": 1,
            "is_shopify_customer": True,
            "type": "contact",
        })
        partner = partner_obj.create(partner_vals)

        shopify_partner_values.update({"partner_id": partner.id})
        self.create(shopify_partner_values)

        return partner

    @api.model
    def shopify_create_or_update_address(self, shopify_customer_data, instance, parent_partner, partner_type="contact"):
        """
        Creates or updates existing partner from Shopify customer's data.
        @author: Maulik Barad on Date 09-Sep-2020.
        """
        partner_obj = self.env["res.partner"]

        first_name = shopify_customer_data.get("first_name")
        last_name = shopify_customer_data.get("last_name")

        if not first_name and not last_name:
            return False

        company_name = shopify_customer_data.get("company")
        partner_vals = self.shopify_prepare_partner_vals(shopify_customer_data, instance)
        address_key_list = ["street", "street2", "city", "zip", "phone", "state_id", "country_id"]

        if company_name:
            address_key_list.append("company_name")
            partner_vals.update({"company_name": company_name})

        partner = partner_obj._find_partner_ept(partner_vals, address_key_list,
                                                [("parent_id", "=", parent_partner.id), ("type", "=", partner_type)])

        if not partner:
            partner = partner_obj._find_partner_ept(partner_vals, address_key_list,
                                                    [("parent_id", "=", parent_partner.id)])
        if partner:
            return partner

        partner_vals.update({"type": partner_type, "parent_id": parent_partner.id})
        partner = partner_obj.create(partner_vals)

        company_name and partner.write({"company_name": company_name})
        return partner

    def shopify_prepare_partner_vals(self, vals, instance):
        """
        This method used to prepare a partner vals.
        @param : self,vals
        @return: partner_vals
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 29 August 2020 .
        Task_id: 165956
        """
        partner_obj = self.env["res.partner"]

        first_name = vals.get("first_name")
        last_name = vals.get("last_name")
        name = "%s %s" % (first_name, last_name)

        zipcode = vals.get("zip")
        state_name = vals.get("province")

        country_name = vals.get("country")
        country = partner_obj.get_country(country_name)
        if not country:
            country_code = vals.get("country_code")
            country = partner_obj.get_country(country_code)

        state = partner_obj.create_or_update_state_ept(country_name, state_name, zipcode, country)

        partner_vals = {
            "email": vals.get("email") or False,
            "name": name,
            "phone": vals.get("phone"),
            "street": vals.get("address1"),
            "street2": vals.get("address2"),
            "city": vals.get("city"),
            "zip": zipcode,
            "state_id": state and state.id or False,
            "country_id": country and country.id or False,
            "is_company": False
        }
        return partner_vals
