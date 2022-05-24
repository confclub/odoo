# -*- coding: utf-8 -*-
"""
Onboarding Controller.
"""
from odoo import http
from odoo.http import request


class ShopifyOnboarding(http.Controller):
    """
        Controller for Onboarding (Banner).
        @author: Dipak Gogiya on Date 26-Sep-2020.
    """

    @http.route('/shopify_instances/shopify_instances_onboarding_panel', auth='user', type='json')
    def shopify_instances_onboarding_panel(self):
        """ Returns the `banner` for the shopify onboarding panel.
            It can be empty if the user has closed it or if he doesn't have
            the permission to see it. """

        current_company_id = request.httprequest.cookies.get('cids', []) and request.httprequest.cookies.get(
            'cids').split(',')
        company = False
        if len(current_company_id) > 0 and current_company_id[0] and current_company_id[0].isdigit():
            company = request.env['res.company'].sudo().search([('id', '=', int(current_company_id[0]))])
        if not company:
            company = request.env.company
        if not request.env.is_admin() or \
                company.shopify_onboarding_state == 'closed':
            return {}
        hide_panel = True if company.shopify_onboarding_toggle_state != 'open' else False
        btn_value = 'Create More Shopify Instance' if hide_panel else 'Hide On boarding Panel'
        return {
            'html': request.env.ref('shopify_ept.shopify_instances_onboarding_panel_ept')._render({
                'company': company,
                'toggle_company_id': company.id,
                'hide_panel': hide_panel,
                'btn_value': btn_value,
                'state': company.get_and_update_shopify_instances_onboarding_state(),
                'is_button_active': company.is_create_shopify_more_instance
            })
        }
