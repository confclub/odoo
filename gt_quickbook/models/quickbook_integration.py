import logging
import pytz
from datetime import datetime
from odoo import api, fields, models, _, tools
from xml.dom.minidom import parse, parseString
import xml.etree.ElementTree as ET
import base64
import requests
import json
from requests import request

import os
import unittest
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError

from odoo.addons.gt_quickbook.api.auth import Oauth2SessionManager
from odoo.addons.gt_quickbook.api.client import QuickBooks
from odoo.addons.gt_quickbook.api.client_intuitlib import AuthClient

from odoo.addons.gt_quickbook.api.enums import Scopes
# from flask import Flask, render_template, redirect, redirect, url_for, make_response
from odoo.addons.gt_quickbook.api.base import Address, PhoneNumber, EmailAddress

from odoo.addons.gt_quickbook.api.customer import Customer
from odoo.addons.gt_quickbook.api.vendor import Vendor
from odoo.addons.gt_quickbook.api.employee import Employee

from odoo.addons.gt_quickbook.api.paymentmethod import PaymentMethod
from odoo.addons.gt_quickbook.api.term import Term

from odoo.addons.gt_quickbook.api.department import Department
from odoo.addons.gt_quickbook.api.item import Item
from odoo.addons.gt_quickbook.api.account import Account
from odoo.addons.gt_quickbook.api.salesreceipt import SalesReceipt
from odoo.addons.gt_quickbook.api.invoice import Invoice
from odoo.addons.gt_quickbook.api.bill import Bill
from odoo.addons.gt_quickbook.api.detailline import SalesItemLine, SalesItemLineDetail

from odoo.addons.gt_quickbook.api.purchaseorder import PurchaseOrder
from odoo.addons.gt_quickbook.api.payment import Payment
from odoo.addons.gt_quickbook.api.billpayment import BillPayment

from odoo.addons.gt_quickbook.api.taxrate import TaxRate
from odoo.addons.gt_quickbook.api.taxservice import TaxService
from odoo.addons.gt_quickbook.api.taxcode import TaxCode
from odoo.addons.gt_quickbook.api.taxservice import TaxRateDetails
from odoo.addons.gt_quickbook.api.taxagency import TaxAgency

from odoo.addons.gt_quickbook.api import client
from datetime import datetime, timedelta, date
# import time
import pytz
from pytz import timezone
from datetime import datetime
from dateutil import tz
import datetime, pytz
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class quickbook_integration(models.Model):
    _name = 'quickbook.integration'
    _rec_name = 'config_name'

    config_name = fields.Char('Name', required=True)

    client_id = fields.Char('Client ID', required=True)
    client_secret = fields.Char('Client Secret Key', required=True)

    # token_access_expire_in = fields.Datetime(string='Access Token Expires On',readonly=True)
    accerss_hours = fields.Char('Hours', readonly=True)
    accerss_minute = fields.Char('Minutes', readonly=True)
    accerss_second = fields.Char('Seconds', readonly=True)
    token_access_expiry_date = fields.Date(string='Access Token Expires On Date', readonly=True)

    # token_ref_expire_in = fields.Datetime(string='Refresh Token Expires On')
    ref_token_hours = fields.Char('Hours', readonly=True)
    ref_token_minute = fields.Char('Minutes', readonly=True)
    ref_token_second = fields.Char('Seconds', readonly=True)
    ref_token_expiry_date = fields.Date(string='Refresh Token Expires On Date', readonly=True)

    # versions = fields.Selection([('1','1.0'),('2','2.0')], string='Version', default='2')

    # authorize_url = fields.Char('Authorization URL')
    # access_token_url = fields.Char('Authorization Token URL')
    auth_code = fields.Char('Authorization Code')

    access_token = fields.Char('Access Token', required=True)
    ref_token = fields.Char('Refresh Token', required=True)

    # state = fields.Selection([('draft', 'Draft'), ('connected', 'Connected')],string='State', default='draft')
    base_url = fields.Char('Base URL')
    redirect_url = fields.Char('Redirect URL')

    company_id = fields.Char('Sandbox Company ID / Realm ID', required=True)

    # @api.model
    # def default_warehouse(self):
    #     warehouse_obj = self.env['stock.warehouse']
    #     def_warehouse_ids = warehouse_obj.search([])
    #     print "def_warehouse_idssssssssss",def_warehouse_ids
    #     # self.warehouse_id = def_warehouse_ids[0].id,
    #     self.update({'warehouse_id': def_warehouse_ids})
    #     # 'warehouse_id' : def_warehouse_ids and def_warehouse_ids[0].id,

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    customer_journal_id = fields.Many2one('account.journal', string='Payment Journal For Customer Bills', required=True)

    shipping_product = fields.Many2one('product.product', string='Shipping Product', required=True)
    discount_product = fields.Many2one('product.product', string='Discount Product', required=True)

    # @api.multi
    def check_connection(self):
        # Quickbooks will send the response to this url
        # callback_url = 'http://localhost:9988/'
        # callback_url = 'http://127.0.0.15:9988/'

        for rec in self:
            session_manager = Oauth2SessionManager(
                client_id=rec.client_id,
                client_secret=rec.client_secret,
                # base_url=rec.base_url,
                access_token=rec.access_token,
                # refresh_token=rec.ref_token,
            )
            # try:
            # print "session_manager>>>>>>>>>>>",session_manager
            authorize_url = session_manager.get_authorize_url(rec.base_url)
            # print "authorize_urlllllllllll>>>>>>>>>>>",authorize_url

            # payload = {
            #             'code': rec.auth_code,
            #             'redirect_uri': self.redirect_url,
            #             'grant_type': 'authorization_code'
            #         }

            # token_req = session_manager.token_request(payload)
            # print "PAYLODDDDDDDDDDDDDDDDDDD",token_req

            # result = session_manager.get_access_tokens('code')
            # print "codeeeeeeeeeeeeeeeeResulttttttttt>>>>>>>>>>>",result
            # # session_manager.get_access_tokens(request.GET['code'])
            # code = session_manager.get_access_tokens(rec.auth_code)
            # print "codeeeeeeeeeeeeeeee>>>>>>>>>>>",code

            # result_ref = session_manager.refresh_access_tokens()
            # print "REFFFFFFFFFFFFFFFFFFFFFFFF",result_ref

            # ===========================================

            auth_client = AuthClient(
                client_id=rec.client_id,
                client_secret=rec.client_secret,
                redirect_uri=rec.redirect_url,
                environment='sandbox',
            )

            # // Prepare scopes
            scopes = [
                Scopes.OPENID,
                Scopes.EMAIL,
            ]

            # // Get authorization URL
            auth_url = auth_client.get_authorization_url(scopes)
            # print "auth_urlllllllllllllll2222222222======>>>>>>>>>",auth_url
            # print "redirect_urlllllllllllllll======>>>>>>>>>",redirect(auth_url)

            access_token=auth_client.get_bearer_token(rec.auth_code, realm_id=rec.company_id)

            user_info = auth_client.get_user_info(rec.access_token)
            print("access_token----", access_token)
            # a = user_info.json()
            # print "aaaaaaaaaaaaaaaa",a,a.statusCode
        return redirect(auth_url)
        #     except Exception as e:
        #         if self.env.context.get('log_id'):
        #             log_id = self.env.context.get('log_id')
        #             self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
        #         else:
        #             log_id = self.env['qbook.log'].create({'all_operations':'authenticate_credentials', 'error_lines': [(0, 0, {'log_description': str(e)})]})
        #             self = self.with_context(log_id=log_id.id)
        # return redirect(auth_url)

    def refresh_token(self):
        # print "refresh_tokennnnnnnnnnnnnnnnn",self.env.user.tz
        for rec in self:
            new_token_session_manager = Oauth2SessionManager(
                client_id=rec.client_id,
                client_secret=rec.client_secret,
                # base_url=rec.base_url,
                access_token=rec.access_token,
                refresh_token=rec.ref_token,
            )
            headers = {
                'Accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded',
                'Authorization': new_token_session_manager.get_auth_header()
            }
            # print "headersssssssssssssss",headers

            payload = {
                'refresh_token': new_token_session_manager.refresh_token,
                'grant_type': 'refresh_token'
            }
            # print "payyyyyyyyyyy",payload

            r = requests.post(new_token_session_manager.access_token_url, data=payload, headers=headers)
            # print "rrrrrrrrrrrrrrrrrrr",r.status_code,r.text
            if r.status_code != 200:
                return r.text

            bearer_raw = json.loads(r.text)
            # print "bbbbbbrrrrrrrrrrrrrrr",bearer_raw

            new_token_session_manager.x_refresh_token_expires_in = bearer_raw['x_refresh_token_expires_in']
            new_token_session_manager.access_token = bearer_raw['access_token']
            new_token_session_manager.token_type = bearer_raw['token_type']
            new_token_session_manager.refresh_token = bearer_raw['refresh_token']
            new_token_session_manager.expires_in = bearer_raw['expires_in']

            # print "new_access_token::::::",new_token_session_manager.access_token
            # print "new_token_type:::::::",new_token_session_manager.token_type
            # print "new_refresh_token::::::",new_token_session_manager.refresh_token
            # print "x_refresh_token_expires_in::::::",new_token_session_manager.x_refresh_token_expires_in
            # print "expires_in::::::",new_token_session_manager.expires_in

            added_minutes = new_token_session_manager.expires_in / 60
            # print "added_added_minuteseeeeeeeeee",added_minutes
            if not self.env.user.tz:
                raise UserError(_("Please select user's Timezone !"))
            dtobj1 = datetime.datetime.utcnow()
            dtobj3 = dtobj1.replace(tzinfo=pytz.UTC)
            dtobj = dtobj3.astimezone(pytz.timezone(self.env.user.tz))
            # print "dtobjjjjjjjjjjjjjjj",dtobj
            # token_access_expire_in = dtobj
            # print "ttttttttttttttttt",token_access_expire_in,type(token_access_expire_in)
            access_t1_exp = dtobj + timedelta(minutes=added_minutes)
            # print "access_t1_exppppppp",access_t1_exp,type(access_t1_exp), access_t1_exp.hour, access_t1_exp.minute, access_t1_exp.second, access_t1_exp.date(),type(access_t1_exp.date)

            added_days = (((new_token_session_manager.x_refresh_token_expires_in / 60) / 60) / 24)
            # print "added_daysssssssssssssssssssssss",added_days
            ref_t2_exp = dtobj + timedelta(days=added_days)
            # print "ref_t2_exppppppppppppppppppppp",ref_t2_exp

            rec.update({
                'access_token': new_token_session_manager.access_token,
                'ref_token': new_token_session_manager.refresh_token,
                # 'token_access_expire_in':access_t1_exp,
                'accerss_hours': access_t1_exp.hour,
                'accerss_minute': access_t1_exp.minute,
                'accerss_second': access_t1_exp.second,
                'token_access_expiry_date': access_t1_exp.date(),

                'ref_token_hours': ref_t2_exp.hour,
                'ref_token_minute': ref_t2_exp.minute,
                'ref_token_second': ref_t2_exp.second,
                'ref_token_expiry_date': ref_t2_exp.date(),
            })

    # @api.multi
    def import_customer(self):
        print ("import_customer=========>>>>")
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']

        # callback_url = 'http://127.0.0.15:9988/'
        for rec in self:
            cust_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,

                                    )
            # print "custtttt_session_manager",cust_session_manager

            qb_client = QuickBooks(
                                        session_manager= cust_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )

            # print "rec.qb_clientttttttttttttt",qb_client
            try:
                customer = Customer()
                # print "cccccccc1111111111111111",customer
                customers = Customer.all(qb=qb_client)
                print ("cccccccc22222222222222",customers)

                for cust in customers:
                    query_customer = Customer.get(cust.Id, qb=qb_client)
                    # print "QQQQQQQQQQQQQQQQQQQQQQQQ1111111",query_customer
                    # print "BillWithParent",query_customer.BillWithParent
                    # print "PreferredDeliveryMethod",query_customer.PreferredDeliveryMethod
                    # print "Taxable",query_customer.Taxable
                    # print "PrintOnCheckName",query_customer.PrintOnCheckName
                    # print "Balance",query_customer.Balance
                    # print "BalanceWithJobs",query_customer.BalanceWithJobs

                    company_id = False
                    company_id = query_customer.CompanyName
                    # print "company_idddddddddd",company_id

                    if company_id:
                        company_ids = res_partner_obj.search([('name', '=', company_id)])
                        # print "cccccccccc",company_ids
                        if not company_ids:
                            company_id = res_partner_obj.create({'name':company_id}).id
                            # print "cccccccccc1111111111111",company_id
                        else:
                            # print "cccccccccc222222222"
                            company_id = company_ids[0].id
                            # print "cccccccccc222222222..22222222222"
                    else :
                        company_id = False
                        # print "ELSEEEEEEEE",company_id

                    # print "COMPANYYYYYYYYYIDDDDDDDDDDD",company_id

                    country_ids  = False
                    if query_customer.BillAddr:
                        c_country = query_customer.BillAddr.Country
                        c_country = c_country.upper()
                        c_state = query_customer.BillAddr.CountrySubDivisionCode
                        c_state = c_state.upper()
                        c_city = query_customer.BillAddr.City
                        c_postalcode = query_customer.BillAddr.PostalCode
                        c_line1 = query_customer.BillAddr.Line1
                        c_line2 = query_customer.BillAddr.Line2
                    else:
                        c_country  = False
                        c_state = False
                        c_city = False
                        c_postalcode = False
                        c_line1 = False
                        c_line2 = False

                    if c_country != False:
                        country_ids = country_obj.search([('code', '=', c_country)])
                        # print "country_idssssssssssssssssss",country_ids
                        if not country_ids:
                            country_id = country_obj.create({'name':c_country, 'code':c_country}).id
                            # print "country_id11111111111111111",country_id
                        else:
                            country_id = country_ids[0].id
                            # print "country_id2222222222222222",country_id
                    else:
                        country_id = False

                    if c_state != False:
                        state_ids = state_obj.search([('code', '=', c_state),('country_id', '=', country_id)])
                        if not state_ids:
                            state_id = state_obj.create({'name':c_state, 'code':c_state, 'country_id': country_id}).id
                        else:
                            state_id = state_ids[0].id
                    else:
                        state_id = False

                    vals = {
                                'qbook_id': query_customer.Id,
                                'name': query_customer.DisplayName,
                                'customer' : True,
                                'supplier' : False,
                                'street':c_line1,
                                'street2' : c_line2,
                                'city': c_city,
                                'zip': c_postalcode,
                                'phone': query_customer.PrimaryPhone.FreeFormNumber if query_customer.PrimaryPhone != None else '',
                                'state_id' :state_id,
                                'country_id': country_id,

                                'email': query_customer.PrimaryEmailAddr.Address if query_customer.PrimaryEmailAddr != None else '',
                                'parent_id': company_id,
                                'website': query_customer.WebAddr.URI if query_customer.WebAddr != None else '',

                                'is_taxable':query_customer.Taxable,
                                'print_on_check_name':query_customer.PrintOnCheckName,
                                'preferred_delivery_method':query_customer.PreferredDeliveryMethod,
                                'balance':query_customer.Balance if query_customer.Balance != None else '',
                                'balance_job':query_customer.BalanceWithJobs if query_customer.BalanceWithJobs != None else '',
                            }

                    # print "valsssssssssssssssssss",vals
                    customer_ids = res_partner_obj.search([('qbook_id', '=', query_customer.Id)])
                    # print"==========>customer_ids>>>>>>>>>>",customer_ids
                    if not customer_ids:
                        cust_id = res_partner_obj.create(vals)
                        # print "IFNOTCCCCCCCCCC",cust_id
                    else:
                        cust_id = customer_ids[0]
                        # print "ELSE111111CCCCCCCCCC",cust_id
                        # logger.info('customer id ===> %s', cust_id.name)
                        cust_id.write(vals)
                        # print "ELSE222222CCCCCCCCCC",cust_id
                # return cust_id
            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_customer', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def import_vendor(self):
        # print "vvvvvvvvvvvvvvvvvvvv"
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']

        # callback_url = 'http://127.0.0.15:9988/'
        for rec in self:
            cust_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,

                                    )
            # print "Vendorrrrrrrr_session_manager",cust_session_manager

            qb_client_vendor = QuickBooks(
                                        session_manager= cust_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )
            try:
                vendor = Vendor()
                vendors = Vendor.all(qb=qb_client_vendor)
                for vend in vendors:
                    query_vendor = Vendor.get(vend.Id, qb=qb_client_vendor)

                    company_id = False
                    company_id = query_vendor.CompanyName

                    if company_id:
                        company_ids = res_partner_obj.search([('name', '=', company_id)])
                        # print "cccccccccc",company_ids
                        if not company_ids:
                            company_id = res_partner_obj.create({'name':company_id}).id
                            # print "cccccccccc1111111111111",company_id
                        else:
                            # print "cccccccccc222222222"
                            company_id = company_ids[0].id
                            # print "cccccccccc222222222..22222222222"

                    country_ids  = False

                    if query_vendor.BillAddr:
                        v_country = query_vendor.BillAddr.Country
                        v_country = v_country.upper()
                        v_state = query_vendor.BillAddr.CountrySubDivisionCode
                        v_state = v_state.upper()
                        v_city = query_vendor.BillAddr.City
                        v_postalcode = query_vendor.BillAddr.PostalCode
                        v_line1 = query_vendor.BillAddr.Line1
                        v_line2 = query_vendor.BillAddr.Line2
                    else:
                        v_country  = False
                        v_state = False
                        v_city = False
                        v_postalcode = False
                        v_line1 = False
                        v_line2 = False

                    if v_country != False:
                        country_ids = country_obj.search([('code', '=', v_country)])
                        # print "ccccccccccccccccc",country_ids
                        if not country_ids:
                            country_id = country_obj.create({'name':v_country, 'code':v_country}).id
                            # print "ccccccccccccccccc1111111111",country_ids
                        else:
                            # print "ccccccccccccccccc22222222222",country_ids
                            country_id = country_ids[0].id
                            # logger.info('country id ===> %s', country_id)
                    else:
                        # print "ccccccccccccccccc33333333333",country_ids
                        country_id = False

                    # bstate = query_vendor.BillAddr.CountrySubDivisionCode
                    # bstate = bstate.upper()

                    if v_state != False:
                        state_ids = state_obj.search([('code', '=', v_state),('country_id', '=', country_id)])
                        if not state_ids:
                            state_id = state_obj.create({'name':v_state, 'code':v_state, 'country_id': country_id}).id
                        else:
                            state_id = state_ids[0].id
                            # logger.info('state id ===> %s', state_id)
                    else:
                        state_id = False

                    # print "=======================",query_vendor,query_vendor.PrimaryEmailAddr
                    # print"Vendor1099", query_vendor.Vendor1099

                    vals = {
                                'qbook_id': query_vendor.Id,
                                'name': query_vendor.DisplayName,
                                'customer' : False,
                                'supplier' : True,
                                'street':v_line1,
                                'street2' : v_line2,
                                'city': v_city,
                                'zip': v_postalcode,
                                'phone': query_vendor.PrimaryPhone.FreeFormNumber if query_vendor.PrimaryPhone != None else '',
                                'state_id' :state_id,
                                'country_id': country_id,
                                'email': query_vendor.PrimaryEmailAddr.Address if query_vendor.PrimaryEmailAddr != None else '',
                                'parent_id': company_id,
                                'website': query_vendor.WebAddr.URI if query_vendor.WebAddr != None else '',

                                'vendor1099':query_vendor.Vendor1099 if query_vendor.Vendor1099 != None else '',
                                'print_on_check_name':query_vendor.PrintOnCheckName,
                                'balance':query_vendor.Balance if query_vendor.Balance != None else '',
                                'acc_num':query_vendor.AcctNum if query_vendor.AcctNum != None else '',
                            }

                    # print "valsssssssssssssssssss",vals
                    vendor_ids = res_partner_obj.search([('qbook_id', '=', query_vendor.Id)])
                    # print"==========>vendor_ids>>>>>>>>>>",vendor_ids
                    if not vendor_ids:
                        vend_id = res_partner_obj.create(vals)
                        # print "IFFFFFFFNNOTTTTVVVVVVVVVVVVV",vend_id
                    else:
                        vend_id = vendor_ids[0]
                        # print "ELSE2222VVVVVVVV",vend_id
                        vend_id.write(vals)
                        # print "ELSE2222VVVVVVVV",vend_id
                # return vend_id
            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_vendor', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)

    # @api.multi
    def import_employee(self):
        # print "eeeeeeeeeeeeeeeee"
        hr_employee_obj = self.env['hr.employee']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']

        # callback_url = 'http://127.0.0.15:9988/'
        for rec in self:
            emp_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        access_token=rec.access_token,
                                    )

            qb_client_employee = QuickBooks(
                                        session_manager= emp_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                    )
            try:
                employee = Employee()
                employees = Employee.all(qb=qb_client_employee)

                for emp in employees:
                    query_emp = Employee.get(emp.Id, qb=qb_client_employee)
                    # print "query_emppppppppppppp",query_emp


                    # if query_emp and query_emp.PrimaryAddr:
                    #     e_email = query_emp.PrimaryAddr or query_emp.PrimaryEmailAddr.get('Address')
                    # else:
                    #     e_email = False
                    # print "emailllllllllllll",e_email



                    country_ids = False
                    if query_emp.PrimaryAddr:
                        e_country = query_emp.PrimaryAddr.Country
                        e_country = e_country.upper()
                        e_state = query_emp.PrimaryAddr.CountrySubDivisionCode
                        e_city = query_emp.PrimaryAddr.City
                        e_postalcode = query_emp.PrimaryAddr.PostalCode
                        e_line1 = query_emp.PrimaryAddr.Line1
                    else:
                        e_country  = False
                        e_state = False
                        e_city = False
                        e_postalcode = False
                        e_line1 = False

                    # print "CCCCCCCCCCCCCCCCCC=====>",e_country,e_email
                    if e_country != False:
                        country_ids = country_obj.search([('code', '=', e_country)])
                        # print "country_idsssssssssss",country_ids
                        if not country_ids:
                            country_id = country_obj.create({'name':e_country, 'code':e_country}).id
                            # print "ccccccccccccccccc1111111111",country_ids
                        else:
                            country_id = country_ids[0].id
                            # print "ccccccccccccccccc22222222222",country_ids
                    else:
                        # print "ccccccccccccccccc33333333333",country_ids
                        country_id = False


                    # print "SSSSSSSSSSSSSSSSSSSS=====>",e_state
                    if e_state != False:
                        state_ids = state_obj.search([('code', '=', e_state),('country_id', '=', country_id)])
                        # print "state_idsssssssssssssssss",state_ids
                        if not state_ids:
                            state_id = state_obj.create({'name':e_state, 'code':e_state, 'country_id': country_id}).id
                            # print "state_id111111111111111111",state_id
                        else:
                            state_id = state_ids[0].id
                            # print "state_id22222222222222222",state_id
                    else:
                        state_id = False
                        # print "state_id33333333333",country_ids

                    # print"empppppppppppppp",  query_emp
                    # print"stateeeeeeeeee",  state_id

                    # print "=======================",query_emp,query_emp.PrimaryEmailAddr
                    # print"SyncToken", query_emp.SyncToken
                    # print"domain", query_emp.domain
                    # print"DisplayName", query_emp.DisplayName

                    # print"PrintOnCheckName", query_emp.PrintOnCheckName
                    # print"FamilyName", query_emp.FamilyName
                    # print"Active", query_emp.Active
                    # print"SSN", query_emp.SSN

                    # print"sparse", query_emp.sparse
                    # print"BillableTime", query_emp.BillableTime
                    # print"GivenName", query_emp.GivenName
                    # print"Id", query_emp.Id

                    # print "CountrySubDivisionCode",e_country,country_id
                    # print "Stateeeeeeee", state_id
                    # print "Cityyyyyyyyyyy",e_city
                    # print "PostalCodeeeee",e_postalcode
                    # print "Line111111111",e_line1

                    vals = {
                                'qbook_id': query_emp.Id,
                                'name': query_emp.DisplayName,
                                # 'street':query_emp.PrimaryAddr.Line1 or '',
                                # 'street2' : query_emp.PrimaryAddr.Line2 or '',
                                'work_location': e_city ,
                                # 'work_email': e_email ,
                                # 'zip': query_emp.PrimaryAddr.PostalCode or '',
                                # 'mobile_phone': query_emp.PrimaryPhone.FreeFormNumber if query_emp.PrimaryPhone != None else '' or False,
                                # 'state_id' :state_id,
                                'country_id': country_id,
                                'identification_id': query_emp.SSN,
                            }
                    # print "valsssssssssssssssssss",vals

                    if  hasattr(query_emp , 'PrimaryPhone'):
                    # if query_emp and query_emp.PrimaryPhone:
                        vals.update({'mobile_phone':query_emp.PrimaryPhone.FreeFormNumber})
                    else :
                        vals.update({'mobile_phone':''})
                        # print "nooooooooo",query_emp.PrimaryPhone.FreeFormNumber

                    # if  hasattr(query_emp , 'PrimaryAddr'):
                    # # if query_emp and query_emp.PrimaryPhone:
                    #     vals.update({'mobile_phone':query_emp.PrimaryEmailAddr.get('Address')})
                    # else :
                    #     vals.update({'mobile_phone':''})

                    employee_ids = hr_employee_obj.search([('qbook_id', '=', query_emp.Id)])
                    # print"==========>employee_ids>>>>>>>>>>",employee_ids
                    if not employee_ids:
                        emp_id = hr_employee_obj.create(vals)
                    else:
                        emp_id = employee_ids[0]
                        # logger.info('customer id ===> %s', emp_id.name)
                        emp_id.write(vals)
                # return emp_id

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_employee', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def import_payment_method(self):
        # print "payyyymethodddddddddddddddd"
        payment_obj = self.env['payment.method']
        for rec in self:
            payment_method_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )

            qb_client_payment_method = QuickBooks(
                                        session_manager= payment_method_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )
            try:
                paymentmethod = PaymentMethod()
                # print "pppppppppppppppppp1111111111111111",paymentmethod
                paymentmethods = PaymentMethod.all(qb=qb_client_payment_method)
                # print "pppppppppp22222222222222",paymentmethods

                for payment_method in paymentmethods:
                    query_payment_method = PaymentMethod.get(payment_method.Id, qb=qb_client_payment_method)
                    # print "pppppppppp33333333333",query_payment_method,query_payment_method.Name

                    pay_ids = payment_obj.search([('qbooks_id', '=',query_payment_method.Id)])

                    pay_vals = {
                        'title': query_payment_method.Name,
                        'qbooks_id': query_payment_method.Id,
                        'payment_type':query_payment_method.Type,
                        }
                    # print"==============pay_methodsssssvals==>>>>>>>>>>",pay_vals
                    pay_ids.write(pay_vals)

                    if not pay_ids:
                        payment_id = payment_obj.create(pay_vals)
                        payment_id.write(pay_vals)

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_payment_method', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def import_payment_term(self):
        # print "TTTTTTTTTTTTTTTTTTTt"
        # payment_term_obj  = self.env['payment.term']
        payment_term_obj  = self.env['account.payment.term']
        payment_line_obj = self.env['account.payment.term.line']
        for rec in self:
            payment_term_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )

            qb_client_payment_term = QuickBooks(
                                        session_manager= payment_term_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )
            try:
                term = Term()
                payment_terms = Term.all(qb=qb_client_payment_term)
                # print "pppppppppp22222222222222",payment_terms

                for payment_term in payment_terms:
                    query_payment_term = Term.get(payment_term.Id, qb=qb_client_payment_term)
                    # print "dueeeeeeeeeeeeeeeeee",query_payment_term,query_payment_term.DueDays,query_payment_term.Type

                    payment_term_id = payment_term_obj.search([('qbooks_id', '=',query_payment_term.Id)])
                    # print "00000000000000000sssssss",payment_term_id

                    payment_terms_vals = {
                        # 'term_name': query_payment_term.Name,
                        'name': query_payment_term.Name,
                        'qbooks_id': query_payment_term.Id,
                        'payment_term_type':query_payment_term.Type,
                        }
                    # print"==============payment_terms_vals==>>>>>>>>>>",payment_terms_vals


                    payment_term_id.write(payment_terms_vals)
                    # print "1111111111111111",payment_term_id

                    if not payment_term_id:
                        payment_term_id = payment_term_obj.create(payment_terms_vals)

                        payment_term_id.write(payment_terms_vals)
                        # print "22222222222222",payment_term_id

                    payment_line={
                                  "value":"balance",
                                  # "value_amount": query_payment_term.DueDays,
                                  "days":query_payment_term.DueDays,
                                  "option":"day_after_invoice_date",
                                  "payment_id":payment_term_id.id,
                                }

                    payment_term_line_ids = payment_line_obj.search([('value','=',"balance"),('days','=',query_payment_term.DueDays)])

                    if payment_term_line_ids:
                        payment_term_line_ids.write(payment_line)
                    else:
                        payment_line_obj.create(payment_line)
            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_payment_term', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def import_departments(self):
        # print "ddddddd"
        dept_obj  = self.env['hr.department']
        for rec in self:
            dept_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_client_dept = QuickBooks(
                                        session_manager= dept_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )
            try:
                department = Department()
                deptments = Department.all(qb=qb_client_dept)
                print("pppppppppp22222222222222",deptments)

                for deptment in deptments:
                    query_deptment = Department.get(deptment.Id, qb=qb_client_dept)

                    dept_ids = dept_obj.search([('qbook_id', '=',query_deptment.Id)])
                    # print "dept_idsssssssssssssss",dept_ids

                    dept_vals = {
                        'name': query_deptment.Name,
                        'qbook_id': query_deptment.Id,
                        'sub_department':query_deptment.SubDepartment,
                        }
                    # print"==============dept_vals==>>>>>>>>>>",dept_vals
                    dept_ids.write(dept_vals)

                    if not dept_ids:
                        dept_id = dept_obj.create(dept_vals)
                        dept_id.write(dept_vals)

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_department', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def import_category(self):
        # print "catttttttttttttttttttt"
        prod_category_obj  = self.env['product.category']
        for rec in self:
            cat_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_client_cat = QuickBooks(
                                        session_manager= cat_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )

            try:
                item = Item()
                items = Item.all(qb=qb_client_cat)

                # print "ITEMMMMMMMMMMMMMMMMssssssssssss",items.items()
                for item in items:
                    # print "ITEMMMMMMMMMMMMMMMM",item
                    cat_id = False
                    query_cat_item = Item.get(item.Id, qb=qb_client_cat)
                    # print "Nameeeee",query_cat_item.FullyQualifiedName
                    # print "Tyypeeee",query_cat_item.Type
                    if query_cat_item.Type == 'Category':
                        # print "categoryyyyyyyyy",query_cat_item.Name
                        category_check = prod_category_obj.search([('qbook_id', '=',query_cat_item.Id)])
                        # print "cat_idsssssssssssssssChild",category_check
                        if not category_check:
                            vals = {
                                'name': query_cat_item.Name,
                                'qbook_id': query_cat_item.Id,
                                }
                            # print"==============child_cat_vals==>>>>>>>>>>",vals

                            if query_cat_item.ParentRef:
                                parent_category_check_id = query_cat_item.ParentRef.value
                                # parent_category_check_name = query_cat_item.ParentRef.name
                                # print "parentttttttt",parent_category_check_id,parent_category_check_name
                                parent_category_check = prod_category_obj.search([('qbook_id', '=',parent_category_check_id)])

                                # print "parent_category_check1111",parent_category_check
                                if parent_category_check:
                                    parent_id = parent_category_check[0].id
                                else:
                                    parent_id = False
                                vals.update({'parent_id': parent_id})
                            else:
                                # print "esleeeeee11111112222222......"
                                if query_cat_item.ParentRef:
                                    parent_category_check = query_cat_item.ParentRef.value
                                    # print "parent_category_check=======",parent_category_check
                                    vals.update({'parent_id': parent_category_check[0].id})
                            cat_id = prod_category_obj.create(vals)
                            # print "=====catiddddddddddddd",cat_id

                        else:
                            # print "ELSEEEEEEEEEEEEEEEEEEEE"
                            vals = {
                                'name': query_cat_item.Name,
                                'qbook_id': query_cat_item.Id,
                                }
                            # print"==============child_cat_vals2222222==>>>>>>>>>>",vals
                            if query_cat_item.ParentRef:
                                parent_category_check_id = query_cat_item.ParentRef.value
                                parent_category_check = prod_category_obj.search([('qbook_id', '=',parent_category_check_id)])
                                # print "parent_category_check22222",parent_category_check
                                if parent_category_check:
                                    parent_id = parent_category_check[0].id
                                else:
                                    parent_id = False
                                vals.update({'parent_id': parent_id})
                            else:
                                # print "esleeeeee11111112222222.2.2.2.2.2.2......"
                                if query_cat_item.ParentRef:
                                    parent_category_check = query_cat_item.ParentRef.value
                                    vals.update({'parent_id': parent_category_check[0].id})
                            category_check[0].write(vals)

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_product_category', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def import_product(self):
        # print "PPPPPPPPPPPPPpp"
        prod_temp_obj = self.env['product.template']
        product_obj = self.env['product.product']
        bundle_obj = self.env['bundle.product']

        for rec in self:
            item_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_client_item = QuickBooks(
                                        session_manager= item_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                item = Item()
                items = Item.all(qb=qb_client_item)

                for item in items:
                    query_item = item.get(item.Id, qb=qb_client_item)
                    # print "nameeeeeeeeeeeee", query_item
                    # print "nameeeeeeeeeeeee", query_item.FullyQualifiedName
                    # print "skuuuuuuuuuuuuuu", query_item.Sku

                    if query_item.IncomeAccountRef:
                        in_acc_name =query_item.IncomeAccountRef.name
                        acc_id =query_item.IncomeAccountRef.value
                        # print "IncomeAccountRef",in_acc_name,acc_id
                        in_acc_id2 = self.env['account.account'].search([('qbooks_id', '=',acc_id)])
                        # print "in_acc_id2222222",in_acc_id2


                    if query_item.AssetAccountRef:
                        asst_acc_name =query_item.AssetAccountRef.name
                        acc_id =query_item.AssetAccountRef.value
                        # print "AssetAccountRef",asst_acc_name,acc_id
                        asst_acc_id2 = self.env['account.account'].search([('qbooks_id', '=',acc_id)])
                        # print "asst_acc_id22222",asst_acc_id2

                    if query_item.ExpenseAccountRef:
                        exp_acc_name =query_item.ExpenseAccountRef.name
                        acc_id =query_item.ExpenseAccountRef.value
                        # print "ExpenseAccountRef",exp_acc_name,acc_id
                        exp_acc_id2 = self.env['account.account'].search([('qbooks_id', '=',acc_id)])
                        # print "exp_acc_id222222",exp_acc_id2

                    # print "Typeeeeeeeeeeeeeeeee", query_item.Type
                    # print "prceeeeeeeeeeeeeee", query_item.UnitPrice
                    # print "purchaseeeeeeeeee", query_item.PurchaseDesc
                    # print "Descriptionnnnnnnn", query_item.Description
                    # print "QtyOnHand", query_item.QtyOnHaIdnd

                    if not query_item.Type == 'Category':
                        prd_tmp_vals = {
                                        'qbooks_id': query_item.Id,
                                        'name': query_item.Name,
                                        # 'type': ,
                                        'lst_price': query_item.UnitPrice  or 0.00,
                                        'standard_price': query_item.PurchaseCost  or 0.00,
                                        # 'default_code': product.get('sku'),
                                        'description_sale': query_item.Description,
                                        'description_purchase':query_item.PurchaseDesc,
                                        # 'property_account_expense_id':exp_acc_id2.id,
                                        # 'property_account_income_id':in_acc_id2.id,
                                        'default_code':query_item.Sku,
                                        }
                        # print "valsssssssssssssssssss",prd_tmp_vals
                        if query_item.Type =='Group':
                            prd_tmp_vals.update({'type': 'product',
                                                })

                        elif query_item.Type =='Inventory':
                            prd_tmp_vals.update({'type': 'product',
                                                'property_account_expense_id':exp_acc_id2.id,
                                                'property_account_income_id':in_acc_id2.id,
                                                })
                        elif query_item.Type =='NonInventory':
                            prd_tmp_vals.update({'type': 'consu',
                                                    'property_account_expense_id':exp_acc_id2.id,
                                                    })
                        else:
                            prd_tmp_vals.update({'type': 'service',
                                                    'property_account_income_id':in_acc_id2.id,
                                                })

                        # print "tempvalssssssssssssssssssssss",prd_tmp_vals

                        temp_ids = prod_temp_obj.search([('qbooks_id', '=', query_item.Id)])
                        # print "temp_idsssssssssss00000000000",temp_ids


                        if temp_ids:
                            temp_ids.write(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            # print "temp_idsssssssssss1111111111",temp_ids,temp_id

                        else:
                            temp_ids = prod_temp_obj.create(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            # print "temp_idsssssssssss222222222",temp_ids,temp_id
                            self._cr.commit()


                        # print "temp_id1111111111111111",temp_id

                        if query_item.Type == 'Group':
                            # print "Groupppppppppppp", query_item.Type

                            for bundle in query_item.ItemGroupDetail.get('ItemGroupLine'):
                                bundle_item_qty = bundle.get('Qty')
                                # print "Qtyyyyyyyyyyyyyyyyyyyyyyy",bundle_item_qty
                                # bundle_item_name = bundle.get('ItemRef').get('name')
                                # print "bbbbbbbbbbbbbbbNAMEEEEEEEE",bundle_item_name
                                bundle_item_id = bundle.get('ItemRef').get('value')
                                # print "Valueeeeeeeeee====", bundle_item_id

                                prod_bundle_ids = product_obj.search([('qbooks_id', '=', bundle_item_id)])
                                # print "prod_temp_bundle_idsssssss====",prod_bundle_ids

                                if prod_bundle_ids:
                                    prod_bundle_id = prod_bundle_ids[0]
                                    # print "prod_temp_id111111111",prod_bundle_id,prod_bundle_id.name,prod_bundle_id.lst_price

                                else:
                                    item = Item()
                                    query_item = Item.get(bundle_item_id, qb=qb_client_item)

                                    prd_vals = {
                                            'qbooks_id': query_item.Id,
                                            'name': query_item.Name,
                                            'lst_price': query_item.UnitPrice  or 0.00,
                                            'standard_price': query_item.PurchaseCost  or 0.00,
                                            'description_sale': query_item.Description,
                                            }
                                    # print "======valssssss=====",prd_vals


                                    if query_item.Type =='Inventory' or query_item.Type =='Group':
                                        prd_vals.update({'type': 'product'})
                                    elif query_item.Type =='NonInventory':
                                        prd_vals.update({'type': 'consu'})
                                    else:
                                        prd_vals.update({'type': 'service'})

                                    prod_bundle_ids = product_obj.search([('qbooks_id', '=', query_item.Id)])
                                    if prod_bundle_ids:
                                        prod_bundle_id = prod_bundle_ids[0]
                                        prod_bundle_id.write(prd_vals)

                                    else:
                                        prod_bundle_id = product_obj.create(prd_vals)
                                        self._cr.commit()
                                # print "***********prod_temp_bundle_id************",prod_bundle_id


                                # print "prod_bundle_iddddddddddddddddd",prod_bundle_id,prod_bundle_id.name,prod_bundle_id.lst_price,bundle_item_qty
                                # b_list =[]

                                # bundle_item_price = prod_bundle_id.lst_price * bundle_item_qty
                                # print "pppppppppppppppppppp",bundle_item_price
                                # b_list.append(bundle_item_price)
                                # print "bbbbbbbbbblistttttt",b_list
                                # for data in str(bundle_item_price):
                                #     b_list.append(data)
                                #     print "bbbbbbbbbb",b_list
                                #     a = sum(b_list)
                                #     print "bbbb_priceeeeeeeeeeeeee",a
                                # print "bbbb_priceeeeeeeeeeeeeebbbbbb",a

                                product_ids = product_obj.search([('product_tmpl_id','=', temp_id.id)])
                                # print "***********product_idsssssssssss************",product_ids

                                if product_ids:
                                    product_id = product_ids[0]

                                    # product_id.write({'state': 'subscribed', 'action_id': act_window.id})
                                    bndl_id = bundle_obj.search([('name','=', prod_bundle_id.id),('prod_id','=', product_id.id)])
                                    # print "***********bndl_id************",bndl_id
                                    if not bndl_id:
                                        bundle_id = bundle_obj.create({
                                            'name':  prod_bundle_id.id,
                                            # 'prod_id':pp and pp.id or False,
                                            'prod_id': product_id.id,
                                            'quantity': bundle_item_qty,
                                        })
                                        product_id.bundle_product = True
                                        # print "***********bundle_idssssss************",bundle_id

                                        # bundle_item_price = prod_bundle_id.lst_price * bundle_item_qty
                                        # print "pppppppppppppppppppp",bundle_item_price
                                        # b_list.append(bundle_item_price)
                                        # print "bbbbbbbbbblistttttt",b_list
                                    b_list= []
                                    for sub_item_id in product_id.bundle_product_ids:
                                        sub_qty = sub_item_id.quantity
                                        # print "sub_qtyyyyyyyyyy",sub_qty
                                        sub_price = sub_item_id.name.lst_price
                                        # print "sub_priceeeeeeee",sub_price
                                        total = sub_qty * sub_price
                                        # print "totalttttttttt",total
                                        b_list.append(total)
                                        # print "b_listtttttttt====",b_list
                                    bundle_price = sum(b_list)
                                    # print "bundle_priceeeeeeeeee",bundle_price
                                    product_id.lst_price = bundle_price

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_products', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)



    # @api.multi
    def import_product_inventory(self):
        # print "iiiiiiiiii"

        prod_temp_obj = self.env['product.template']
        product_obj = self.env['product.product']
        # product_image_obj = self.env['product.images']

        for rec in self:
            item_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_client_item = QuickBooks(
                                        session_manager= item_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                item = Item()
                items = Item.all(qb=qb_client_item)

                for item in items:
                    query_item = item.get(item.Id, qb=qb_client_item)
                    # print "QtyOnHand", query_item.QtyOnHand
                    if not query_item.Type == 'Category':
                        pro_ids = prod_temp_obj.search([('qbooks_id', '=', query_item.Id)])

                        if pro_ids:
                            # print "p_id11111111111111111111",pro_ids[0]
                            p_id = pro_ids[0]
                            # temp_ids = temp_ids.write(prd_tmp_vals)
                        else:
                            prd_tmp_vals = {
                                        'qbooks_id': query_item.Id,
                                        'name': query_item.Name,
                                        # 'type': 'product',
                                        'list_price': query_item.UnitPrice  or 0.00,
                                        'standard_price': query_item.PurchaseCost  or 0.00,
                                        # 'default_code': product.get('sku'),
                                        'description_sale': query_item.Description,
                                        }

                            if query_item.Type =='Inventory' or query_item.Type =='Group':
                                prd_tmp_vals.update({'type': 'product'})
                            elif query_item.Type =='NonInventory':
                                prd_tmp_vals.update({'type': 'consu'})
                            else:
                                prd_tmp_vals.update({'type': 'service'})

                            p_id = prod_temp_obj.create(prd_tmp_vals)
                            # print "p_id222222222222222222222",p_id
                            self._cr.commit()

                            pro_ids = prod_temp_obj.search([('qbooks_id', '=', query_item.Id)])

                            if pro_ids:
                                # print "p_id333333333333333",pro_ids[0]
                                p_id = pro_ids[0]

                        if p_id:
                            # print "p_id4444444444444",p_id
                            pro_id = self.env['product.product'].search([('product_tmpl_id', '=',p_id.id )])
                            # print "p_id5555555555555",pro_id

                            inv_wiz = self.env['stock.change.product.qty']
                            # inv_wiz = self.env['stock.quant']
                            if query_item.QtyOnHand > 0:
                                # print "-----------------------",query_item.QtyOnHand
                                # print "---------self.warehouse_id.lot_stock_id.id",self.warehouse_id.lot_stock_id.id
                                # print "---------p_id.id",p_id.id


                                inv_wizard = inv_wiz.create({
                                    'location_id' : self.warehouse_id.lot_stock_id.id,
                                    # 'location_id' : self.warehouse_id.partner_id.property_stock_customer.id,
                                    'new_quantity' : query_item.QtyOnHand,
                                    # 'qty' : query_item.QtyOnHand,
                                    'product_id' : pro_id.id,
                                    })
                                # print ("inv_wizardddddd",inv_wizard)
                                inv_wizard.change_product_qty()

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_product_inventory', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)
        return True



    # @api.one
    def QbookManageOrderLines(self, orderid, order_detail, qb_order_item):
        # print "QQQbookManageOrderLinesssssssss",orderid,order_detail,qb_order_item
        sale_order_line_obj = self.env['sale.order.line']
        prod_temp_obj = self.env['product.template']
        product_obj = self.env['product.product']
        bundle_obj = self.env['bundle.product']
        accounttax_obj = self.env['account.tax']
        # accounttax_id = False
        # lines = []

        for line_item in order_detail.Line:
            # print"DetailType", line_item.DetailType
            # print "lineeeeeeId",line_item
            # bundle_price = str(line_item)
            # print "bundle_priceeeeeee",bundle_price,type(bundle_price)
            # bundle_new_price = bundle_price[9:]
            # print "bundle_new_priceeeeeee",bundle_new_price
            # print "Bundle pricerrrrrrrrrrrrrrr",order_detail.TotalAmt

            tax_idss = []
            accounttax_id = False

            if line_item.DetailType == 'SalesItemLineDetail' and line_item.SalesItemLineDetail.get('ItemRef').get('value') == 'SHIPPING_ITEM_ID':
                    ship_value = line_item.SalesItemLineDetail.get('ItemRef').get('value')
                    # print "1111111111111111111111",ship_value
                    ship_amount= line_item.Amount
                    # print "2222222222222222222222",ship_amount

                    # p_id = False
                    # p_ids = product_obj.search([('name','=','Shipping and Handling'),('type','=','service')])
                    # # print ("P_IDSSSSSSSSSSSS",p_id)

                    # if p_ids:
                    #     p_id = p_ids[0]
                    #     # print ("iiiffffffffP_IDSSSSSSSSSSS",p_id)
                    # else:
                    #     p_id = product_obj.create({
                    #         'name': 'Shipping and Handling',
                    #         'type': 'service'
                    #         })
                    #     # print ("elseeeeeeeeP_IDSSSSSSSSSS",p_id)
                    #     self._cr.commit()

                    line = {
                        # 'product_id' : p_id and p_id.id,
                        'product_id' : self.shipping_product.id,
                        'price_unit': float(ship_amount),
                        # 'name': p_id.name,
                        'name': self.shipping_product.name,
                        'product_uom_qty': 1,
                        'order_id': orderid.id,
                        'tax_id': False,
                        'qbook_id': ship_value,
                        # 'product_uom': p_id and p_id.uom_id.id
                        'product_uom': self.shipping_product.uom_id.id,
                    }
                    # print ("LINEEEEEEEEEssssssssssssss",line)

                    line_ids = sale_order_line_obj.search([('order_id', '=', orderid.id), ('qbook_id', '=', ship_value)])
                    if line_ids:
                        line_id = line_ids[0]
                        # print ("line_idsssssssssss",line_ids)
                        line_id.write(line)
                    else:
                        # print "====elseeeeeeline===>",line
                        line_id = sale_order_line_obj.create(line)
                    self.env.cr.commit()
                    continue


            if line_item.DetailType == 'SalesItemLineDetail' or line_item.DetailType == 'GroupLineDetail':
                if line_item.DetailType == 'SalesItemLineDetail':
                    # print "lineidddddddddddddd",line_item.SalesItemLineDetail
                    tax = line_item.SalesItemLineDetail.get('TaxCodeRef').get('value')
                    # print("tax_nameeeeeeeeeee",tax)
                    if tax == 'TAX':
                        # print "ttttttttttttttttttttttt",tax
                        for tax_line in order_detail.TxnTaxDetail.TaxLine:
                            # print "tax_lineeeeeeeeeeeeee===",tax_line
                            tex_DetailType = tax_line.DetailType
                            # print "tex_line_iddddddddddd",tex_DetailType

                            if tex_DetailType == 'TaxLineDetail':
                                tax_qb_id  = tax_line.TaxLineDetail.TaxRateRef.value
                                # print "dataaaaaaaaaaaaaaaaaaaaa",tax_qb_id

                                tax_id = accounttax_obj.search([('qbook_id','=',tax_qb_id)])
                                # print "tax_iddddddddddddddd11111",tax_id
                                # if tax_id:
                                #     accounttax_id = tax_id[0]
                                #     tax_ids.append(accounttax_id)
                                #     print "ttttttttttttttttt",tax_ids
                                if not tax_id:
                                    query_tax_rate = TaxRate.get(tax_qb_id, qb=qb_order_item)
                                    if query_tax_rate.AgencyRef:
                                        # print "AgencyReffffffffffVVVVv",query_tax_rate.AgencyRef.value
                                        query_tax_a = TaxAgency.get(query_tax_rate.AgencyRef.value, qb=qb_order_item)
                                        # print "aaaaaaaaaaiddddddddddddd",query_tax_a.Id
                                        # print "aaaaaaaaaanameeeeeeeeeee",query_tax_a.DisplayName
                                        agency_ids =self.env['account.agency'].search([('qbook_id', '=',query_tax_a)])
                                        agency_vals = {
                                                        'name':query_tax_a.DisplayName,
                                                        'qbook_id':query_tax_a.Id,
                                                      }
                                        # print "agency_valsssssssssssss",agency_vals
                                        if agency_ids:
                                            agency_id = agency_ids[0]
                                            agency_id.write(agency_vals)
                                        else:
                                            agency_id = self.env['account.agency'].create(agency_vals)

                                    tax_ids = accounttax_obj.search([('name', '=',query_tax_rate.Name)])
                                    # print "tax_idssssssssssssssss",tax_ids
                                    tax_vals = {
                                        'name': query_tax_rate.Name,
                                        'qbook_id': query_tax_rate.Id,
                                        'type_tax_use':'sale',
                                        'amount_type':'percent',
                                        'amount':query_tax_rate.RateValue,
                                        'account_agency': agency_id.id,
                                        }
                                    # print "tax_valsssssssssssssss",tax_vals
                                    tax_ids.write(tax_vals)

                                    if not tax_ids:
                                        # print "notttttttttttttt"
                                        tax_id = accounttax_obj.create(tax_vals)
                                        tax_id.write(tax_vals)

                                accounttax_id = tax_id[0]
                                tax_idss.append(accounttax_id)
                                # print "ttttttttttttttttt",tax_idss


                elif line_item.DetailType == 'GroupLineDetail':
                        bundle_tax_line = line_item.GroupLineDetail
                        # print "tax_lineeeeeeeeee",bundle_tax_line,len(bundle_tax_line)
                        for bundle_item_tax in bundle_tax_line.get('Line'):
                            # print "bundle_item_taxxxxxxxxxxx",bundle_item_tax
                            if bundle_item_tax.get('DetailType') == 'SalesItemLineDetail':
                                # print "//////////"
                                tax = bundle_item_tax.get('SalesItemLineDetail').get('TaxCodeRef').get('value')
                                # print("tax_nameeeeeeeeeee",tax)
                                if tax == 'TAX':
                                    for tax_line in order_detail.TxnTaxDetail.TaxLine:
                                        # print "tax_lineeeeeeeeeeeeee2222222===",tax_line
                                        tex_DetailType = tax_line.DetailType
                                        # print "tex_line_iddddddddddd",tex_DetailType

                                        if tex_DetailType == 'TaxLineDetail':
                                            tax_qb_id  = tax_line.TaxLineDetail.TaxRateRef.value
                                            # print "dataaaaaaaaaaaaaaaaaaaaa",tax_qb_id
                                            tax_id = accounttax_obj.search([('qbook_id','=',tax_qb_id)])
                                            # print "tax_iddddddddddddddd11111",tax_id
                                            # if tax_id:
                                            #     accounttax_id = tax_id[0]
                                            #     tax_idss.append(accounttax_id)
                                            #     print "ttttttttttttttttt222222",tax_idss

                                            if not tax_id:
                                                query_tax_rate = TaxRate.get(tax_qb_id, qb=qb_order_item)
                                                if query_tax_rate.AgencyRef:
                                                    # print "AgencyReffffffffffVVVVv",query_tax_rate.AgencyRef.value
                                                    query_tax_a = TaxAgency.get(query_tax_rate.AgencyRef.value, qb=qb_order_item)
                                                    # print "aaaaaaaaaaiddddddddddddd",query_tax_a.Id
                                                    # print "aaaaaaaaaanameeeeeeeeeee",query_tax_a.DisplayName
                                                    agency_ids =self.env['account.agency'].search([('qbook_id', '=',query_tax_a)])
                                                    agency_vals = {
                                                                    'name':query_tax_a.DisplayName,
                                                                    'qbook_id':query_tax_a.Id,
                                                                  }
                                                    # print "agency_valsssssssssssss",agency_vals
                                                    if agency_ids:
                                                        agency_id = agency_ids[0]
                                                        agency_id.write(agency_vals)
                                                    else:
                                                        agency_id = self.env['account.agency'].create(agency_vals)

                                                tax_ids = accounttax_obj.search([('name', '=',query_tax_rate.Name)])
                                                # print "tax_idssssssssssssssss",tax_ids
                                                tax_vals = {
                                                    'name': query_tax_rate.Name,
                                                    'qbook_id': query_tax_rate.Id,
                                                    'type_tax_use':'sale',
                                                    'amount_type':'percent',
                                                    'amount':query_tax_rate.RateValue,
                                                    'account_agency': agency_id.id,
                                                    }
                                                # print "tax_valsssssssssssssss",tax_vals
                                                tax_ids.write(tax_vals)

                                                if not tax_ids:
                                                    # print "notttttttttttttt"
                                                    tax_id = accounttax_obj.create(tax_vals)
                                                    tax_id.write(tax_vals)

                                            accounttax_id = tax_id[0]
                                            tax_idss.append(accounttax_id)
                                            # print "ttttttttttttttttt222222",tax_idss

                else:
                    accounttax_id = False
            # print("tax_nameeeeeeeeeee============",tax,accounttax_id)
            # print "accounttax_iddddddddddd",accounttax_id


            if line_item.DetailType == 'SalesItemLineDetail' or line_item.DetailType == 'GroupLineDetail':
                if line_item.DetailType == 'SalesItemLineDetail':
                    # print "lineeeeeeTaxCodeRef",line_item.SalesItemLineDetail.get('TaxCodeRef').get('value')
                    prod_qbook_id = line_item.SalesItemLineDetail.get('ItemRef').get('value')
                    # print "prodddddIIIIIDDDDDDDDD111111111",prod_qbook_id
                else:
                    prod_qbook_id = line_item.GroupLineDetail.get('GroupItemRef').get('value')
                    # print "prodddddIIIIIDDDDDDDDD222222222",prod_qbook_id

                if line_item.DetailType == 'SalesItemLineDetail':
                    prod_qbook_name = line_item.SalesItemLineDetail.get('ItemRef').get('name')
                    # print "prodddddIIIIIDDDDDDDDDdNAMEEEEEEE22222222222",prod_qbook_name
                else:
                    prod_qbook_name = line_item.GroupLineDetail.get('GroupItemRef').get('name')

                if line_item.DetailType == 'SalesItemLineDetail':
                    prod_qbook_qty = line_item.SalesItemLineDetail.get('Qty')
                    # print "prodddddQQQQtyyyyyyyyyyy2222222222222",prod_qbook_qty
                else:
                    prod_qbook_qty = line_item.GroupLineDetail.get('Quantity')

                if line_item.DetailType == 'SalesItemLineDetail':
                    prod_qbook_price = line_item.SalesItemLineDetail.get('UnitPrice')
                    # print "prodddddqtPriceeeeee1111111111111",prod_qbook_price
                else:
                    # prod_qbook_price = line_item.GroupLineDetail.get('UnitPrice')
                    # print "prodddddqtPriceeeeee2222222222222",prod_qbook_price

                    total = sum(total_bundle.get('Amount') for total_bundle in line_item.GroupLineDetail.get('Line'))
                    # print "Totallllllbbbbbbbbbbbb",total
                    bundle_total_qty = line_item.GroupLineDetail.get('Quantity')
                    # print "llllllllllllll",bundle_total_qty

                    total = total / bundle_total_qty
                    # print "Totallllllccccccccccccccccccc",total

                if prod_qbook_id:
                    temp_ids = prod_temp_obj.search([('qbooks_id', '=', prod_qbook_id)])

                    if temp_ids:
                        temp_id = temp_ids[0]
                        # print "iffffffffp_iddddddddddd",temp_id
                        # temp_ids.write(prd_tmp_vals)
                        # print "TEMP00000000000000",temp_id
                    else:
                        # print "ELSEEEEEEEEEEEEEEEEE"
                        item = Item()
                        query_item = Item.get(prod_qbook_id, qb=qb_order_item)
                        # print "query_itemquerrrrrrrr$$$$$$",query_item
                        # print "TYPE#############",query_item.Type

                        prd_tmp_vals = {
                                'qbooks_id': query_item.Id,
                                'name': query_item.Name,
                                'list_price': query_item.UnitPrice  or 0.00,
                                'standard_price': query_item.PurchaseCost  or 0.00,
                                'description_sale': query_item.Description,
                                }
                        # print "prodddddvalsssssssssssssss",prd_tmp_vals

                        if query_item.Type =='Inventory' or query_item.Type =='Group':
                            prd_tmp_vals.update({'type': 'product'})
                        elif query_item.Type =='NonInventory':
                            prd_tmp_vals.update({'type': 'consu'})
                        else:
                            prd_tmp_vals.update({'type': 'service'})

                        temp_ids = prod_temp_obj.search([('qbooks_id', '=', query_item.Id)])
                        if temp_ids:
                            temp_ids.write(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            # print "ifffffffffTEMP",temp_id
                        else:
                            temp_ids = prod_temp_obj.create(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            self._cr.commit()
                            # print "ElseeeeeeeeTEMP",temp_id



                        # print "Groupppppppppppp*********", query_item.Type
                        if query_item.Type == 'Group':
                            # print "Groupppppppppppp1233333333", query_item.Type
                            for bundle in query_item.ItemGroupDetail.get('ItemGroupLine'):
                                bundle_item_qty = bundle.get('Qty')
                                bundle_item_id = bundle.get('ItemRef').get('value')
                                prod_bundle_ids = product_obj.search([('qbooks_id', '=', bundle_item_id)])
                                if prod_bundle_ids:
                                    prod_bundle_id = prod_bundle_ids[0]
                                    # print "prod_bundle_idddddddddddd",prod_bundle_id
                                else:
                                    item = Item()
                                    query_item = Item.get(bundle_item_id, qb=qb_order_item)
                                    # print "query_itemSSSSSSSSSSS",query_item

                                    prd_vals = {
                                            'qbooks_id': query_item.Id,
                                            'name': query_item.Name,
                                            'list_price': query_item.UnitPrice  or 0.00,
                                            'standard_price': query_item.PurchaseCost  or 0.00,
                                            'description_sale': query_item.Description,
                                            }

                                    if query_item.Type =='Inventory' or query_item.Type =='Group':
                                        prd_vals.update({'type': 'product'})
                                    elif query_item.Type =='NonInventory':
                                        prd_vals.update({'type': 'consu'})
                                    else:
                                        prd_vals.update({'type': 'service'})

                                    prod_bundle_ids = product_obj.search([('qbooks_id', '=', query_item.Id)])
                                    if prod_bundle_ids:
                                        prod_bundle_id = prod_bundle_ids[0]
                                        prod_bundle_id.write(prd_vals)
                                    else:
                                        prod_bundle_id = product_obj.create(prd_vals)
                                        self._cr.commit()

                                product_ids = product_obj.search([('product_tmpl_id','=', temp_id.id)])
                                # print "TEMPPPMAINNNNNNNProdProd",product_ids

                                if product_ids:
                                    product_id = product_ids[0]

                                    bndl_id = bundle_obj.search([('name','=', prod_bundle_id.id),('prod_id','=', product_id.id)])
                                    # print "bndl_iddddddddddddddd",bndl_id

                                    if not bndl_id:
                                        bundle_id = bundle_obj.create({
                                            'name':  prod_bundle_id.id,
                                            # 'prod_id':pp and pp.id or False,
                                            'prod_id': product_id.id,
                                            'quantity': bundle_item_qty,
                                        })

                                        product_id.bundle_product = True


                    # print "TEMP**************",temp_id
                    product_ids = product_obj.search([('product_tmpl_id','=', temp_id.id)])

                    if product_ids:
                        product_id = product_ids[0]
                        # print ("product_iddddddddddds",product_id)

                    # print "prod_priceeeeeeeeee",prod_qbook_price
                    # print "bundle_prceeeeeeeee",order_detail.TotalAmt
                    line = {
                        'product_id' : product_id and product_id.id,
                        'name': prod_qbook_name or temp_id.name,
                        'product_uom_qty': float(prod_qbook_qty),
                        'order_id': orderid.id,
                        # 'tax_id': False,
                        'qbook_id': line_item.Id,
                        'product_uom': temp_id and temp_id.uom_id.id
                    }
                    # print "LINE_VALSSSSSSSSSSSSSS",line

                    # print "accounttax_iddddddddddd",accounttax_id,tax_idss
                    if not accounttax_id == False:
                        # print "aaaaaaaaaaaaaaaaaa",accounttax_id
                        # line['tax_id'] = [(6, 0, [accounttax_id.id])]
                        line['tax_id'] = [(6, 0, [tax.id for tax in tax_idss])]
                        # print ("iiiiifffffffline['tax_id']ddddddddddd",line['tax_id'])
                    else:
                        # print "eeeeeeeeeeeeeee"
                        line['tax_id'] =[]


                    if line_item.DetailType == 'SalesItemLineDetail':
                        line.update({'price_unit': line_item.SalesItemLineDetail.get('UnitPrice')})
                        # print "LLLLprodddddqtPriceeeeee1111111111111",prod_qbook_price
                    elif line_item.DetailType == 'GroupLineDetail':
                        # print "ELSEELLLLLprodddddqtPriceeeeee2222222222222",prod_qbook_price
                        # print "ELSEELLLLLprodddddqtPriceeeeee2222222222222",line_item.GroupLineDetail.get('UnitPrice')
                        # line.update({'price_unit': order_detail.TotalAmt})
                        line.update({'price_unit': total})


                    # if line_item.DetailType == 'SalesItemLineDetail':
                        # if not line_item.SalesItemLineDetail.get('ItemRef').get('name'):
                            # p_id = False
                            # p_ids = product_obj.search([('qbooks_id','=','DLTPRD')])

                            # if p_ids:
                            #     p_id = p_ids[0]
                            # else:
                            #     p_id = product_obj.create({
                            #         'name': 'Deleted Product',
                            #         'type': 'product',
                            #         'default_code': 'DLTPRD',
                            #         })
                            # line.update({'name': str(prod_qbook_id), 'product_id': p_id.id})
                            # print "LINEVALS_DEletedddddddddd",line


                    line_ids = sale_order_line_obj.search([('order_id', '=', orderid.id),('qbook_id', '=',line_item.Id)])
                    # print ("Lineidddddddsssssss",line_ids,line_item.Id)

                    if line_ids:
                        line_id = line_ids[0]
                        line_id.write(line)
                        # print ("LINEEEEEEE",line_id)
                    else:
                        line_id = sale_order_line_obj.create(line)
                        # print ("elseeeeeLINEEEEEEE",line_id)
        self.env.cr.commit()
        return True





    # @api.multi
    def import_order(self):
        # print "oooooooooooooo"
        sale_order_obj = self.env['sale.order']
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']
        payment_method_obj = self.env['payment.method']
        # account_payment_term_obj = self.env['account.payment.term']

        for rec in self:
            order_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_order_item = QuickBooks(
                                        session_manager= order_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )
            try:
                sale = SalesReceipt()
                sales = SalesReceipt.all(qb=qb_order_item)

                for sales_data in sales:
                    sales_order_query = SalesReceipt.get(sales_data.Id, qb=qb_order_item)
                    # print "==============="
                    # print "SSSSSSSSSSSS",sales_order_query
                    # print "Amtttttttttt",sales_order_query.TotalAmt
                    # print "DocNumberrrrrr",sales_order_query.DocNumber
                    # print "lineeeeeeTAXXXXXXCODEREF",sales_order_query.TxnTaxDetail.TxnTaxCodeRef

                    custm_id = sales_order_query.CustomerRef.value
                    # print("===custm_idcustm_idcustm_id======>",custm_id)
                    if not custm_id:
                        # print("===custm_idcustm_idcustm_id======>",custm_id)
                        partner_id = self[0].partner_id
                    else:
                        # print ("==ELSEEEEORDERRRRRRRRRR==")
                        part_ids = res_partner_obj.search([('qbook_id', '=', custm_id)])
                        # print ("part_idssssssssss111111111111111",part_ids)

                        if part_ids:
                            partner_id = part_ids[0]
                            # print ("iffffff_part_ids111111111111111",part_ids)
                        else:
                            # print ("==esleeeeeeee2222222==***********")
                            customer = Customer()

                            # for cust in customers:
                            query_customer = Customer.get(custm_id, qb=qb_order_item)
                            # query_customer = Customer.get(1, qb=qb_order_item)
                            # print "QQQQQQQQQQQQQQQQQQQQQQQQ1111111",query_customer
                            company_id = False
                            company_id = query_customer.CompanyName

                            if company_id :
                                company_ids = res_partner_obj.search([('name', '=', company_id)])
                                # print "cccccccccc",company_ids
                                if not company_ids:
                                    company_id = res_partner_obj.create({'name':company_id}).id
                                    # print "cccccccccc1111111111111",company_id
                                else:
                                    # print "cccccccccc222222222"
                                    company_id = company_ids[0].id
                                    # print "cccccccccc222222222..22222222222"

                            country_ids  = False

                            if query_customer.BillAddr:
                                c_country = query_customer.BillAddr.Country
                                c_country = c_country.upper()
                                c_state = query_customer.BillAddr.CountrySubDivisionCode
                                c_state = c_state.upper()
                                c_city = query_customer.BillAddr.City
                                c_postalcode = query_customer.BillAddr.PostalCode
                                c_line1 = query_customer.BillAddr.Line1
                                c_line2 = query_customer.BillAddr.Line2
                            else:
                                c_country  = False
                                c_state = False
                                c_city = False
                                c_postalcode = False
                                c_line1 = False
                                c_line2 = False

                            if c_country != False:
                                country_ids = country_obj.search([('code', '=', c_country)])
                                if not country_ids:
                                    country_id = country_obj.create({'name':c_country, 'code':c_country}).id
                                else:
                                    country_id = country_ids[0].id
                                    # logger.info('country id ===> %s', country_id)
                            else:
                                country_id = False

                            # c_state = query_customer.BillAddr.CountrySubDivisionCode
                            # c_state = c_state.upper()

                            if c_state != False:
                                state_ids = state_obj.search([('code', '=', c_state),('country_id', '=', country_id)])
                                if not state_ids:
                                    state_id = state_obj.create({'name':c_state, 'code':c_state, 'country_id': country_id}).id
                                else:
                                    state_id = state_ids[0].id
                                    # logger.info('state id ===> %s', state_id)
                            else:
                                state_id = False

                            cust_vals = {
                                        'qbook_id': query_customer.Id,
                                        'name': query_customer.DisplayName,
                                        'customer' : True,
                                        'supplier' : False,
                                        'street':c_line1,
                                        'street2' : c_line2,
                                        'city': c_city,
                                        'zip': c_postalcode,
                                        'phone': query_customer.PrimaryPhone.FreeFormNumber if query_customer.PrimaryPhone != None else '',
                                        'state_id' :state_id,
                                        'country_id': country_id,
                                        'email': query_customer.PrimaryEmailAddr.Address if query_customer.PrimaryEmailAddr != None else '',
                                        'parent_id': company_id,
                                        'website': query_customer.WebAddr.URI if query_customer.WebAddr != None else '',
                                    }

                            # print "cust_valsssssssssssssssssss",cust_vals
                            customer_ids = res_partner_obj.search([('qbook_id', '=', query_customer.Id)])
                            # print"==========>customer_ids>>>>>>>>>>",customer_ids
                            if not customer_ids:
                                partner_id = res_partner_obj.create(cust_vals)
                            else:
                                partner_id = customer_ids[0]
                                # logger.info('customer id ===> %s', cust_id.name)
                                partner_id.write(cust_vals)

                            # print "cust_iddddddddddddddd",partner_id

                    payment_id = False
                    if sales_order_query.PaymentMethodRef:
                        payment_method_id = sales_order_query.PaymentMethodRef.value
                        # print "payment_method_iddddddddd",payment_method_id

                        paym_ids = payment_method_obj.search([('qbooks_id','=',payment_method_id)])
                        # print "paym_idssssssssssssssssss",paym_ids

                        if paym_ids:
                            payment_id = paym_ids[0]
                            # print "paym_iddddddddddiffffffff",payment_id
                        else:
                            paymentmethod = PaymentMethod()
                            query_payment_method = PaymentMethod.get(payment_method_id, qb=qb_order_item)
                            # print "query_payment_methodddddddddd",query_payment_method.Name

                            payment_ids = payment_method_obj.search([('qbooks_id', '=',query_payment_method.Id)])
                            # print "payment_idsssssssssssssssssss",payment_ids
                            pay_vals = {
                                'title': query_payment_method.Name,
                                'qbooks_id': query_payment_method.Id,
                                'payment_type':query_payment_method.Type,
                                }
                            # print"==============pay_methodsssssvals==>>>>>>>>>>",pay_vals

                            # if not payment_ids:
                            #     payment_id = payment_method_obj.create(pay_vals)
                            #     print "NOOOOOTTTTpayment_idddddddddddd",payment_id
                            # else:
                            #     payment_id.write(pay_vals)
                            #     print "payment_idddddddddddd*********",payment_id


                            if payment_ids:
                                payment_id = payment_ids[0].id
                                payment_id.write(pay_vals)

                                # logger.info('payment id ===> %s', pay_id)
                            else:
                                payment_ids = payment_method_obj.create(pay_vals)
                                payment_id = payment_ids[0].id

                    # print "payment_idddddddddddd",payment_id
                    order_vals = {
                                  'partner_id': partner_id.id,
                                  'qbook_id' : sales_order_query.Id,
                                  'name': sales_order_query.DocNumber,
                                  'payment_method':payment_id.id if payment_id != False else '',
                                  'amount_tax':sales_order_query.TxnTaxDetail.TotalTax,
                                    }

                    # print "order_valssssssssssssssssssss",order_vals

                    sale_order_ids = sale_order_obj.search([('qbook_id', '=', sales_data.Id)])
                    # print ("SALEORDERIDDDDDDDD",sale_order_ids,sales_order_query.TxnTaxDetail.TotalTax)

                    if not sale_order_ids:
                        s_id = sale_order_obj.create(order_vals)
                        self._cr.commit()
                        # print ("SID11111111111111",s_id,s_id.name)
                        # print "sales_order_queryyyyyyyyyyyyyy",sales_order_query
                        self.QbookManageOrderLines(s_id, sales_order_query, qb_order_item)
                        self.qbookManageDiscount(s_id, sales_order_query, qb_order_item)
                    else:
                        if sale_order_ids.state != 'done':
                            s_id = sale_order_ids[0]
                            # print ("SID22222222222",s_id,s_id.name)
                            # print "sales_order_queryyyyyyyyyyyyyy",sales_order_query
                            # logger.info('create order ===> %s', s_id.name)
                            s_id.write(order_vals)
                            self.QbookManageOrderLines(s_id, sales_order_query,qb_order_item)
                            self.qbookManageDiscount(s_id, sales_order_query, qb_order_item)
                    self.env.cr.commit()

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_sale_order', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.one
    def qbookManageDiscount(self, orderid, sales_order_query, qb_order_item):
        # print ("qbookManageDiscountttttttttttttt",orderid,sales_order_query,qb_order_item)

        sale_order_line_obj = self.env['sale.order.line']
        product_obj = self.env['product.product']

        for line_item in sales_order_query.Line:
            if line_item.DetailType == 'DiscountLineDetail':
                discount_line = line_item.DiscountLineDetail
                # print "discount_lineeeeeeeeeeeeeee",discount_line
                # dis_name = discount_line.get('DiscountAccountRef').get('name')
                # print "discount_nmameeeeeeeeeeeeee",dis_name
                dis_id = discount_line.get('DiscountAccountRef').get('value')
                # print "discount_idddddddddddddddddddddd",dis_id

                discount_line_amount = line_item.Amount
                # print "discount_line_amounttttttttt",discount_line_amount

                # p_id = False
                # # p_ids = product_obj.search([('name','=',dis_name),('type','=','service')])
                # p_ids = product_obj.search([('name','=','Discount Given'),('type','=','service')])
                # print ("P_IDSSSSSSSSSSSS",p_id)

                # if p_ids:
                #     p_id = p_ids[0]
                #     print ("iiiffffffffP_IDSSSSSSSSSSS",p_id)
                # else:
                #     p_id = product_obj.create({
                #         'name': 'Discount Given',
                #         'type': 'service'
                #         })
                #     print ("elseeeeeeeeP_IDSSSSSSSSSS",p_id)
                #     self._cr.commit()

                line = {
                    # 'product_id' : p_id and p_id.id,
                    'product_id' : self.discount_product.id,
                    'price_unit': -float(discount_line_amount),
                    # 'name': p_id.name,
                    'name': self.discount_product.name,
                    'product_uom_qty': 1,
                    'order_id': orderid.id,
                    'tax_id': False,
                    # 'product_uom': p_id and p_id.uom_id.id,
                    'product_uom': self.discount_product.uom_id.id,
                    'qbook_id':dis_id,
                }
                # print ("LINEEEEEEEEE",line)

                line_ids = sale_order_line_obj.search([('order_id', '=', orderid.id), ('qbook_id', '=', dis_id)])
                if line_ids:
                    line_id = line_ids[0]
                    # print ("line_idsssssssssss",line_ids)
                    # logger.info('order line id ===> %s', line_id.name)
                    line_id.write(line)
                else:
                    # print "====elseeeeeeline===>",line
                    line_id = sale_order_line_obj.create(line)
                self.env.cr.commit()
        return True




    # @api.multi
    def import_purchase_order(self):
        # print "PPPPPPPPPPPPPPP"
        purchase_order_obj = self.env['purchase.order']
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']

        for rec in self:
            purchase_order_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_purchase_order = QuickBooks(
                                        session_manager= purchase_order_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )
            try:
                purchaseorder = PurchaseOrder()
                purchaseorders = PurchaseOrder.all(qb=qb_purchase_order)

                for purchaseorder_data in purchaseorders:
                    query_purchaseorder = purchaseorder_data.get(purchaseorder_data.Id, qb=qb_purchase_order)
                    # print "Purchseidddddd",query_purchaseorder.Id
                    # print "PurchseNOOOOOO",query_purchaseorder.DocNumber

                    vend_id = query_purchaseorder.VendorRef.value
                    # print "VVVVVIIIDDDDDDDDDD",vend_id

                    if not vend_id:
                        partner_id = self[0].partner_id
                        # print "ifffffNOTVIDDDDDDDD",partner_id
                    else:
                        part_ids = res_partner_obj.search([('qbook_id', '=', vend_id)])
                        # print "ELSEEEEEEEpart_idssssssss",part_ids
                        if part_ids:
                            vend_id = part_ids[0]
                            # print "iffffffpart_iddddd",vend_id
                        else:
                            # print "esleeeeeeeeeeeeeeee"
                            vendor = Vendor()
                            query_vendor = Vendor.get(vend_id, qb=qb_purchase_order)

                            company_id = False
                            company_id = query_vendor.CompanyName

                            if company_id:
                                company_ids = res_partner_obj.search([('name', '=', company_id)])
                                # print "ccccccccccoooooommpppp",company_ids
                                if not company_ids:
                                    company_id = res_partner_obj.create({'name':company_id}).id
                                    # print "ccccccccccoooommmmppp1111111111111",company_id
                                else:
                                    # print "cccccccccc222222222"
                                    company_id = company_ids[0].id
                                    # print "ccccccccccooooommmppp222222222..22222222222"

                            country_ids  = False

                            if query_vendor.BillAddr:
                                v_country = query_vendor.BillAddr.Country
                                v_country = v_country.upper()
                                v_state = query_vendor.BillAddr.CountrySubDivisionCode
                                v_state = v_state.upper()
                                v_city = query_vendor.BillAddr.City
                                v_postalcode = query_vendor.BillAddr.PostalCode
                                v_line1 = query_vendor.BillAddr.Line1
                                v_line2 = query_vendor.BillAddr.Line2
                            else:
                                v_country  = False
                                v_state = False
                                v_city = False
                                v_postalcode = False
                                v_line1 = False
                                v_line2 = False

                            if v_country != False:
                                country_ids = country_obj.search([('code', '=', v_country)])
                                # print "ccccccccccccccccc",country_ids
                                if not country_ids:
                                    country_id = country_obj.create({'name':v_country, 'code':v_country}).id
                                    # print "ccccccccccccccccc1111111111",country_ids
                                else:
                                    country_id = country_ids[0].id
                                    # print "ccccccccccccccccc22222222222",country_id
                            else:
                                # print "ccccccccccccccccc33333333333",country_ids
                                country_id = False

                            # bstate = query_vendor.BillAddr.CountrySubDivisionCode
                            # bstate = bstate.upper()

                            if v_state != False:
                                state_ids = state_obj.search([('code', '=', v_state),('country_id', '=', country_id)])
                                if not state_ids:
                                    state_id = state_obj.create({'name':v_state, 'code':v_state, 'country_id': country_id}).id
                                else:
                                    state_id = state_ids[0].id
                                    # logger.info('state id ===> %s', state_id)
                            else:
                                state_id = False

                            # print "=======================",query_vendor,query_vendor.PrimaryEmailAddr
                            # print"Vendor1099", query_vendor.Vendor1099

                            vals = {
                                    'qbook_id': query_vendor.Id,
                                    'name': query_vendor.DisplayName,
                                    'customer' : False,
                                    'supplier' : True,
                                    'street':v_line1,
                                    'street2' : v_line2,
                                    'city': v_city,
                                    'zip': v_postalcode,
                                    'phone': query_vendor.PrimaryPhone.FreeFormNumber if query_vendor.PrimaryPhone != None else '',
                                    'state_id' :state_id,
                                    'country_id': country_id,
                                    'email': query_vendor.PrimaryEmailAddr.Address if query_vendor.PrimaryEmailAddr != None else '',
                                    'parent_id': company_id,
                                    'website': query_vendor.WebAddr.URI if query_vendor.WebAddr != None else '',

                                    'vendor1099':query_vendor.Vendor1099 if query_vendor.Vendor1099 != None else '',
                                    'print_on_check_name':query_vendor.PrintOnCheckName,
                                    'balance':query_vendor.Balance if query_vendor.Balance != None else '',
                                    'acc_num':query_vendor.AcctNum if query_vendor.AcctNum != None else '',
                                    }

                            # print "valsssssssssssssssssss",vals
                            vendor_ids = res_partner_obj.search([('qbook_id', '=', query_vendor.Id)])
                            # print"==========>vendor_ids>>>>>>>>>>",vendor_ids
                            if not vendor_ids:
                                vend_id = res_partner_obj.create(vals)
                                # print "IFFFFFFFNNOTTTTVVVVVVVVVVVVV",vend_id
                            else:
                                vend_id = vendor_ids[0]
                                # print "ELSE2222VVVVVVVV",vend_id
                                vend_id.write(vals)
                                # print "ELSE2222VVVVVVVV",vend_id

                    purchase_order_vals = {
                                  'partner_id': vend_id.id,
                                  'qbook_id' : query_purchaseorder.Id,
                                  'name': query_purchaseorder.DocNumber,
                                  'date_planned': datetime.datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                    }
                    purchase_order_ids = purchase_order_obj.search([('qbook_id', '=', purchaseorder_data.Id)])
                    # print "purchase_order_idsssssssssssssssss",purchase_order_ids,purchase_order_ids.state

                    if query_purchaseorder.ShipAddr:
                        # print "shippppppppLIneeeIDDD",query_purchaseorder.ShipAddr.Id,
                        # print "shippppppppLine1",query_purchaseorder.ShipAddr.Line1,
                        purchase_order_vals.update({
                                                    'addr_l1':query_purchaseorder.ShipAddr.Line1,
                                                    'addr_l2':query_purchaseorder.ShipAddr.Line2,
                                                    'addr_l3':query_purchaseorder.ShipAddr.Line3,
                                                    'addr_l4':query_purchaseorder.ShipAddr.Line4,
                                                    })

                    if not purchase_order_ids:
                        p_id = purchase_order_obj.create(purchase_order_vals)
                        self._cr.commit()
                        self.QbookManagePurchaseOrderLines(p_id, query_purchaseorder, qb_purchase_order)
                    else:
                        # print "purchase_order_idsssssssssssssssss",purchase_order_ids
                        for p_id in purchase_order_ids:
                            # print "p_idddddddddddddd",purchase_order_ids
                            if p_id.state != 'done':
                                # p_id = purchase_order_ids[0]
                                p_id.write(purchase_order_vals)
                                self.QbookManagePurchaseOrderLines(p_id, query_purchaseorder,qb_purchase_order)
                    self.env.cr.commit()

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_purchase_order', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.one
    def QbookManagePurchaseOrderLines(self, purchase_orderid, purchase_order_detail, qb_purchase_order):
        # print "QQQbookManagePurchaseOrderLinessssssssss",purchase_orderid,purchase_order_detail,qb_purchase_order

        purchase_order_line_obj = self.env['purchase.order.line']
        prod_temp_obj = self.env['product.template']
        product_obj = self.env['product.product']
        bundle_obj = self.env['bundle.product']
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']
        purchase_lines = []

        for purchase_line_item in purchase_order_detail.Line:
            # print "purchase_line_itemmmmmmmm",purchase_line_item
            if purchase_line_item.DetailType == 'ItemBasedExpenseLineDetail' :
                prod_qbook_id = purchase_line_item.ItemBasedExpenseLineDetail.ItemRef.value
                # print "prodddddIIIIIDDDDDDDDD111111111",prod_qbook_id
                prod_qbook_name = purchase_line_item.ItemBasedExpenseLineDetail.ItemRef.name
                # print "prodddddIIIIIDDDDDDDDDdNAMEEEEEEE22222222222",prod_qbook_name
                prod_qbook_qty = purchase_line_item.ItemBasedExpenseLineDetail.Qty
                # print "prodddddQQQQtyyyyyyyyyyy2222222222222",prod_qbook_qty
                prod_qbook_price = purchase_line_item.ItemBasedExpenseLineDetail.UnitPrice
                # print "prodddddqtPriceeeeee1111111111111",prod_qbook_price



                if prod_qbook_id:
                    temp_ids = prod_temp_obj.search([('qbooks_id', '=', prod_qbook_id)])
                    # print "temp_idssssssss=====>>>>",temp_ids

                    if temp_ids:
                        temp_id = temp_ids[0]
                        # print "iffffffffp_iddddddddddd",temp_id
                        # temp_ids.write(prd_tmp_vals)
                        # print "TEMP00000000000000",temp_id
                    else:
                        # print "ELSEEEEEEEEEEEEEEEEE"
                        item = Item()
                        query_item = Item.get(prod_qbook_id, qb=qb_purchase_order)
                        # print "query_itemquerrrrrrrr$$$$$$",query_item
                        # print "TYPE#############",query_item.Type

                        prd_tmp_vals = {
                                'qbooks_id': query_item.Id,
                                'name': query_item.Name,
                                'list_price': query_item.UnitPrice  or 0.00,
                                'standard_price': query_item.PurchaseCost  or 0.00,
                                'description_sale': query_item.Description,
                                }
                        # print "prodddddvalsssssssssssssss",prd_tmp_vals

                        if query_item.Type =='Inventory' or query_item.Type =='Group':
                            prd_tmp_vals.update({'type': 'product'})
                        elif query_item.Type =='NonInventory':
                            prd_tmp_vals.update({'type': 'consu'})
                        else:
                            prd_tmp_vals.update({'type': 'service'})

                        temp_ids = prod_temp_obj.search([('qbooks_id', '=', query_item.Id)])
                        if temp_ids:
                            temp_ids.write(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            # print "ifffffffffTEMP",temp_id
                        else:
                            temp_ids = prod_temp_obj.create(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            self._cr.commit()
                            # print "ElseeeeeeeeTEMP",temp_id

                product_ids = product_obj.search([('product_tmpl_id','=', temp_id.id)])

                if product_ids:
                    product_id = product_ids[0]

                line = {
                    'product_id' : product_id and product_id.id,
                    'name': prod_qbook_name or temp_id.name,
                    'product_qty': float(prod_qbook_qty),
                    'order_id': purchase_orderid.id,
                    'taxes_id': False,
                    'qbook_id': purchase_line_item.Id,
                    'product_uom': temp_id and temp_id.uom_id.id,
                    'price_unit': prod_qbook_price,
                    'date_planned': datetime.datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }
                # print "PPPPPPPLINE_VALSSSSSSSSSSSSSS",line

                # if purchase_line_item.ItemBasedExpenseLineDetail:
                if purchase_line_item.ItemBasedExpenseLineDetail.CustomerRef:
                    qbook_line_cust_id = purchase_line_item.ItemBasedExpenseLineDetail.CustomerRef.value
                    # print "LIneeeeeeCUSTTTTTTTTTTTIIIIIDDDDDDD",qbook_line_cust_id

                    qbook_line_cust_name = purchase_line_item.ItemBasedExpenseLineDetail.CustomerRef.name
                    # print "LIneeeeeeCUSTTTTTTTTTTTNAMEEEEEEEE",qbook_line_cust_name

                    # line_cust_id = False
                    if not qbook_line_cust_id:
                        line_cust_id = self[0].line_cust_id
                    else:
                        line_cust_ids = res_partner_obj.search([('qbook_id', '=', qbook_line_cust_id)])
                        if line_cust_ids:
                            line_cust_id = line_cust_ids[0]
                        else:
                            customer = Customer()
                            query_customer = Customer.get(qbook_line_cust_id, qb=qb_purchase_order)

                            company_id = False
                            company_id = query_customer.CompanyName

                            if company_id:
                                company_ids = res_partner_obj.search([('name', '=', company_id)])
                                if not company_ids:
                                    company_id = res_partner_obj.create({'name':company_id}).id
                                else:
                                    company_id = company_ids[0].id

                            country_ids  = False
                            if query_customer.BillAddr:
                                c_country = query_customer.BillAddr.Country
                                c_country = c_country.upper()
                                c_state = query_customer.BillAddr.CountrySubDivisionCode
                                c_state = c_state.upper()
                                c_city = query_customer.BillAddr.City
                                c_postalcode = query_customer.BillAddr.PostalCode
                                c_line1 = query_customer.BillAddr.Line1
                                c_line2 = query_customer.BillAddr.Line2
                            else:
                                c_country  = False
                                c_state = False
                                c_city = False
                                c_postalcode = False
                                c_line1 = False
                                c_line2 = False
                            if c_country != False:
                                country_ids = country_obj.search([('code', '=', c_country)])
                                if not country_ids:
                                    country_id = country_obj.create({'name':c_country, 'code':c_country}).id
                                else:
                                    country_id = country_ids[0].id
                            else:
                                country_id = False
                            if c_state != False:
                                state_ids = state_obj.search([('code', '=', c_state),('country_id', '=', country_id)])
                                if not state_ids:
                                    state_id = state_obj.create({'name':c_state, 'code':c_state, 'country_id': country_id}).id
                                else:
                                    state_id = state_ids[0].id
                            else:
                                state_id = False

                            line_cust_vals = {
                                        'qbook_id': query_customer.Id,
                                        'name': query_customer.DisplayName,
                                        'customer' : True,
                                        'supplier' : False,
                                        'street':c_line1,
                                        'street2' : c_line2,
                                        'city': c_city,
                                        'zip': c_postalcode,
                                        'phone': query_customer.PrimaryPhone.FreeFormNumber if query_customer.PrimaryPhone != None else '',
                                        'state_id' :state_id,
                                        'country_id': country_id,
                                        'email': query_customer.PrimaryEmailAddr.Address if query_customer.PrimaryEmailAddr != None else '',
                                        'parent_id': company_id,
                                        'website': query_customer.WebAddr.URI if query_customer.WebAddr != None else '',
                                    }
                            # print "LINEEEEEEECUSTVALSSSSSSSSSS++++>>>",line_cust_vals

                            line_customer_ids = res_partner_obj.search([('qbook_id', '=', query_customer.Id)])
                            # print "LINE_customer_idssssssssssss====>>",line_customer_ids

                            if not line_customer_ids:
                                line_cust_id = res_partner_obj.create(line_cust_vals)
                            else:
                                line_cust_id = line_customer_ids[0]
                                line_cust_id.write(line_cust_vals)

                # if line_cust_id:
                    # print "line_cust_idddddddddd*******",line_cust_id
                    line.update({'line_customer':line_cust_id and line_cust_id.id,})


                line_ids = purchase_order_line_obj.search([('order_id', '=', purchase_orderid.id),('qbook_id', '=',purchase_line_item.Id)])
                # print ("Lineidddddddsssssss",line_ids,purchase_line_item.Id)

                if line_ids:
                    line_id = line_ids[0]
                    line_id.write(line)
                    # print ("LINEEEEEEE",line_id)
                else:
                    line_id = purchase_order_line_obj.create(line)
                    # print ("elseeeeeLINEEEEEEE",line_id)
        self.env.cr.commit()
        return True



    # @api.multi
    def import_invoice(self):
        # print "IIIIIIIIIIIII"
        # sale_order_obj = self.env['sale.order']
        account_invoice_obj = self.env['account.move']
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']
        payment_method_obj = self.env['payment.method']
        # account_payment_term_obj = self.env['account.payment.term']

        for rec in self:
            invoice_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_invoice_item = QuickBooks(
                                        session_manager= invoice_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )
            try:
                invoice = Invoice()
                invoices = Invoice.all(qb=qb_invoice_item)

                line = SalesItemLine()
    #
                for invoice_data in invoices:
                    query_invoice = Invoice.get(invoice_data.Id, qb=qb_invoice_item)
                    # print "invoiceiddddddd",query_invoice.Id
                    # print "invoiceiNOOOOOO",query_invoice.DocNumber
                    # print "PrintStatusssss",query_invoice.PrintStatus

                    custm_id = query_invoice.CustomerRef.value
                    # print("============custm_id======>",custm_id)

                    if not custm_id:
                        # print("===custm_idcustm_idcustm_id======>",custm_id)
                        partner_id = self[0].partner_id
                    else:
                        # print ("==esleeeeeeee2222222==***********")
                        customer = Customer()
                        query_customer = Customer.get(custm_id, qb=qb_invoice_item)

                        company_id = False
                        company_id = query_customer.CompanyName

                        if company_id:
                            company_ids = res_partner_obj.search([('name', '=', company_id)])
                            # print "cccccccccc",company_ids
                            if not company_ids:
                                company_id = res_partner_obj.create({'name':company_id}).id
                                # print "cccccccccc1111111111111",company_id
                            else:
                                # print "cccccccccc222222222"
                                company_id = company_ids[0].id
                                # print "cccccccccc222222222..22222222222"

                        country_ids = False

                        if query_customer.BillAddr:
                            c_country = query_customer.BillAddr.Country
                            c_country = c_country.upper()
                            c_state = query_customer.BillAddr.CountrySubDivisionCode
                            c_state = c_state.upper()
                            c_city = query_customer.BillAddr.City
                            c_postalcode = query_customer.BillAddr.PostalCode
                            c_line1 = query_customer.BillAddr.Line1
                            c_line2 = query_customer.BillAddr.Line2
                            # print "IIIIIFFFFFFBillLLLLLL",c_country,c_country,c_state,c_city,c_postalcode,c_line1,c_line2
                        else:
                            c_country  = False
                            c_state = False
                            c_city = False
                            c_postalcode = False
                            c_line1 = False
                            c_line2 = False
                            # print "ElseeeeeeeeBillLLLLLL",c_country,c_country,c_state,c_city,c_postalcode,c_line1,c_line2

                        if c_country != False:
                            country_ids = country_obj.search([('code', '=', c_country)])
                            if not country_ids:
                                country_id = country_obj.create({'name':c_country, 'code':c_country}).id
                            else:
                                country_id = country_ids[0].id
                                # logger.info('country id ===> %s', country_id)
                        else:
                            country_id = False

                        # c_state = query_customer.BillAddr.CountrySubDivisionCode
                        # c_state = c_state.upper()

                        if c_state != False:
                            state_ids = state_obj.search([('code', '=', c_state),('country_id', '=', country_id)])
                            if not state_ids:
                                state_id = state_obj.create({'name':c_state, 'code':c_state, 'country_id': country_id}).id
                            else:
                                state_id = state_ids[0].id
                                # logger.info('state id ===> %s', state_id)
                        else:
                            state_id = False

                        cust_vals = {
                                    'qbook_id': query_customer.Id,
                                    'name': query_customer.DisplayName,
                                    'customer' : True,
                                    'supplier' : False,
                                    'street':c_line1,
                                    'street2' : c_line2,
                                    'city': c_city,
                                    'zip': c_postalcode,
                                    'phone': query_customer.PrimaryPhone.FreeFormNumber if query_customer.PrimaryPhone != None else '',
                                    'state_id' :state_id,
                                    'country_id': country_id,
                                    'email': query_customer.PrimaryEmailAddr.Address if query_customer.PrimaryEmailAddr != None else '',
                                    'parent_id': company_id,
                                    'website': query_customer.WebAddr.URI if query_customer.WebAddr != None else '',
                                }

                        # print "cust_valsssssssssssssssssss",cust_vals
                        customer_ids = res_partner_obj.search([('qbook_id', '=', query_customer.Id)])
                        # print"==========>customer_ids>>>>>>>>>>",customer_ids
                        if not customer_ids:
                            partner_id = res_partner_obj.create(cust_vals)
                        else:
                            partner_id = customer_ids[0]
                            # logger.info('customer id ===> %s', cust_id.name)
                            partner_id.write(cust_vals)

                        # print "cust_iddddddddddddddd",partner_id

                    invoice_vals = {
                                  'partner_id': partner_id.id,
                                  'qbook_id' : query_invoice.Id,
                                  'number': query_invoice.DocNumber if query_invoice.DocNumber else False,
                                  'name':query_invoice.DocNumber,
                                  # 'payment_method':payment_id.id if payment_id != False else '',
                                  'date_invoice': query_invoice.TxnDate,
                                  'date': query_invoice.DueDate,
                                    }


                    # print "invoice_valssssssssssssssssssss",invoice_vals

                    invioce_ids = account_invoice_obj.search([('qbook_id', '=', query_invoice.Id)])
                    # invioce_ids = account_invoice_obj.search([('number','=', query_invoice.DocNumber)])
                    # print "invioce_idssssssssssssssssssssss",invioce_ids

                    if not invioce_ids:
                        inv_id = account_invoice_obj.create(invoice_vals)
                        self._cr.commit()
                        # print ("IIIIIIINNNVVVVD11111111111111",inv_id,inv_id.name)
                        self.QbookManageInvoiceLines(inv_id, query_invoice, qb_invoice_item, partner_id)
                        self.qbookManageDiscountInvoice(inv_id, query_invoice, qb_invoice_item, partner_id)
                    else:
                        for invioce_id in invioce_ids:
                            if invioce_id.state != 'done':
                                inv_id = invioce_id
                                # print ("IIIINNNVVVID22222222222",inv_id,inv_id.name)
                                # logger.info('create order ===> %s', inv_id.name)
                                inv_id.write(invoice_vals)
                                self.QbookManageInvoiceLines(inv_id, query_invoice,qb_invoice_item, partner_id)
                                self.qbookManageDiscountInvoice(inv_id, query_invoice, qb_invoice_item, partner_id)
                    self.env.cr.commit()

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_customer_invoice', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.one
    def QbookManageInvoiceLines(self, inv_id, query_invoice, qb_invoice_item, partner_id):
        # print "QbookManageInvoiceLineseeeeeeeee",inv_id,query_invoice,qb_invoice_item
        # sale_order_line_obj = self.env['sale.order.line']
        account_invoice_line_obj = self.env['account.move.line']
        prod_temp_obj = self.env['product.template']
        product_obj = self.env['product.product']
        bundle_obj = self.env['bundle.product']
        accounttax_obj = self.env['account.tax']
        acc_lines = []
        tax_id = []
        accounttax_id = False

        tax_idss = []
        for account_line_item in query_invoice.Line:
            # print "lineeeeeeeeee",account_line_item
            # bundle_price = str(account_line_item)
            # print "bundle_priceeeeeee",bundle_price,type(bundle_price)
            # bundle_new_price = bundle_price[9:]
            # print "bundle_priceeeeeee",bundle_new_price,type(bundle_new_price)

            if account_line_item.DetailType == 'SalesItemLineDetail' and account_line_item.SalesItemLineDetail.ItemRef.value == 'SHIPPING_ITEM_ID':
                    ship_value = account_line_item.SalesItemLineDetail.ItemRef.value
                    # print "1111111111111111111111iiiiiiiii",ship_value
                    ship_amount= account_line_item.Amount
                    # print "2222222222222222222222iiiiiiiiii",ship_amount

                    # p_id = False
                    # p_ids = product_obj.search([('name','=','Shipping and Handling'),('type','=','service')])
                    # # print ("P_IDSSSSSSSSSSSS",p_id)

                    # if p_ids:
                    #     p_id = p_ids[0]
                    #     # print ("iiiffffffffP_IDSSSSSSSSSSS",p_id)
                    # else:
                    #     p_id = product_obj.create({
                    #         'name': 'Shipping and Handling',
                    #         'type': 'service'
                    #         })
                    #     # print ("elseeeeeeeeP_IDSSSSSSSSSS",p_id)
                    #     self._cr.commit()

                    line = {
                        # 'product_id' : p_id and p_id.id,
                        'product_id' : self.shipping_product.id,
                        'price_unit': float(ship_amount),
                        # 'name': p_id.name,
                        'name': self.shipping_product.name,
                        'quantity': 1,
                        'invoice_id': inv_id.id,
                        'invoice_line_tax_ids': False,
                        'qbook_id': ship_value,
                        # 'uom_id': p_id and p_id.uom_id.id,
                        'uom_id': self.shipping_product.uom_id.id,
                        'account_id': partner_id.property_account_receivable_id.id,
                    }
                    # print ("LINEEEEEEEEEssssssssssssss",line)

                    line_ids = account_invoice_line_obj.search([('invoice_id', '=', inv_id.id), ('qbook_id', '=', ship_value)])
                    if line_ids:
                        line_id = line_ids[0]
                        # print ("line_idsssssssssss",line_ids)
                        line_id.write(line)
                    else:
                        # print "====elseeeeeeline===>",line
                        line_id = account_invoice_line_obj.create(line)
                    self.env.cr.commit()
                    continue


            if account_line_item.DetailType == 'SalesItemLineDetail' or account_line_item.DetailType == 'GroupLineDetail':
                if account_line_item.DetailType == 'SalesItemLineDetail':
                    tax = account_line_item.SalesItemLineDetail.TaxCodeRef.value
                    # print "taxxxxxxxxxxxxxxx",tax
                    if tax == 'TAX':
                        for tax_line in query_invoice.TxnTaxDetail.TaxLine:
                            tex_DetailType = tax_line.DetailType
                            if tex_DetailType == 'TaxLineDetail':
                                tax_qb_id  = tax_line.TaxLineDetail.TaxRateRef.value
                                # print "taxiddddddddddddddQQQQQQQQ",tax_qb_id
                                tax_id = accounttax_obj.search([('qbook_id','=',tax_qb_id)])
                                # print "taxiddddddddddddd",tax_id
                                # if tax_id:
                                #     accounttax_id = tax_id[0]
                                #     tax_ids.append(accounttax_id)
                                #     print "ttttttttttttttttt222222",tax_ids
                                if not tax_id:
                                    query_tax_rate = TaxRate.get(tax_qb_id, qb=qb_invoice_item)
                                    if query_tax_rate.AgencyRef:
                                        # print "AgencyReffffffffffVVVVv",query_tax_rate.AgencyRef.value
                                        query_tax_a = TaxAgency.get(query_tax_rate.AgencyRef.value, qb=qb_invoice_item)
                                        # print "aaaaaaaaaaiddddddddddddd",query_tax_a.Id
                                        # print "aaaaaaaaaanameeeeeeeeeee",query_tax_a.DisplayName
                                        agency_ids =self.env['account.agency'].search([('qbook_id', '=',query_tax_a)])
                                        agency_vals = {
                                                        'name':query_tax_a.DisplayName,
                                                        'qbook_id':query_tax_a.Id,
                                                      }
                                        # print "agency_valsssssssssssss",agency_vals
                                        if agency_ids:
                                            agency_id = agency_ids[0]
                                            agency_id.write(agency_vals)
                                        else:
                                            agency_id = self.env['account.agency'].create(agency_vals)

                                    tax_ids = accounttax_obj.search([('name', '=',query_tax_rate.Name)])
                                    # print "tax_idssssssssssssssss",tax_ids
                                    tax_vals = {
                                        'name': query_tax_rate.Name,
                                        'qbook_id': query_tax_rate.Id,
                                        'type_tax_use':'sale',
                                        'amount_type':'percent',
                                        'amount':query_tax_rate.RateValue,
                                        'account_agency': agency_id.id,
                                        }
                                    # print "tax_valsssssssssssssss",tax_vals
                                    tax_ids.write(tax_vals)

                                    if not tax_ids:
                                        # print "notttttttttttttt"
                                        tax_id = accounttax_obj.create(tax_vals)
                                        tax_id.write(tax_vals)

                                accounttax_id = tax_id[0]
                                tax_idss.append(accounttax_id)
                                # print "ttttttttttttttttt222222",tax_idss

                elif account_line_item.DetailType == 'GroupLineDetail':
                    # print "account_line_item.DetailTypetttttttttt",account_line_item
                    bundle_tax_line = account_line_item.GroupLineDetail
                    # print "tax_lineeeeeeeeee",bundle_tax_line

                    for bundle_item_tax in bundle_tax_line.Line:
                        # print "bundle_item_taxxxxxxxxxxx",bundle_item_tax
                        if bundle_item_tax.get('DetailType') == 'SalesItemLineDetail':
                            # print "//////////"
                            tax = bundle_item_tax.get('SalesItemLineDetail').get('TaxCodeRef').get('value')
                            # print("tax_nameeeeeeeeeee",tax)
                            if tax == 'TAX':
                                for tax_line in query_invoice.TxnTaxDetail.TaxLine:
                                    # print "tax_lineeeeeeeeeeeeee2222222===",tax_line
                                    tex_DetailType = tax_line.DetailType
                                    # print "tex_line_iddddddddddd",tex_DetailType
                                    if tex_DetailType == 'TaxLineDetail':
                                        tax_qb_id  = tax_line.TaxLineDetail.TaxRateRef.value
                                        # print "dataaaaaaaaaaaaaaaaaaaaa",tax_qb_id
                                        tax_id = accounttax_obj.search([('qbook_id','=',tax_qb_id)])
                                        # print "tax_iddddddddddddddd11111",tax_id
                                        # if tax_id:
                                        #     accounttax_id = tax_id[0]
                                        #     tax_ids.append(accounttax_id)
                                        #     print "ttttttttttt1111111111111",tax_ids
                                        if not tax_id:
                                            query_tax_rate = TaxRate.get(tax_qb_id, qb=qb_invoice_item)
                                            if query_tax_rate.AgencyRef:
                                                # print "AgencyReffffffffffVVVVv",query_tax_rate.AgencyRef.value
                                                query_tax_a = TaxAgency.get(query_tax_rate.AgencyRef.value, qb=qb_invoice_item)
                                                # print "aaaaaaaaaaiddddddddddddd",query_tax_a.Id
                                                # print "aaaaaaaaaanameeeeeeeeeee",query_tax_a.DisplayName
                                                agency_ids =self.env['account.agency'].search([('qbook_id', '=',query_tax_a)])
                                                agency_vals = {
                                                                'name':query_tax_a.DisplayName,
                                                                'qbook_id':query_tax_a.Id,
                                                              }
                                                # print "agency_valsssssssssssss",agency_vals
                                                if agency_ids:
                                                    agency_id = agency_ids[0]
                                                    agency_id.write(agency_vals)
                                                else:
                                                    agency_id = self.env['account.agency'].create(agency_vals)

                                            tax_ids = accounttax_obj.search([('name', '=',query_tax_rate.Name)])
                                            # print "tax_idssssssssssssssss",tax_ids
                                            tax_vals = {
                                                'name': query_tax_rate.Name,
                                                'qbook_id': query_tax_rate.Id,
                                                'type_tax_use':'sale',
                                                'amount_type':'percent',
                                                'amount':query_tax_rate.RateValue,
                                                'account_agency': agency_id.id,
                                                }
                                            # print "tax_valsssssssssssssss",tax_vals
                                            tax_ids.write(tax_vals)

                                            if not tax_ids:
                                                # print "notttttttttttttt"
                                                tax_id = accounttax_obj.create(tax_vals)
                                                tax_id.write(tax_vals)

                                        accounttax_id = tax_id[0]
                                        tax_idss.append(accounttax_id)
                                        # print "ttttttttttttttttt222222",tax_idss
                else:
                    accounttax_id = False

            if account_line_item.DetailType == 'SalesItemLineDetail' or account_line_item.DetailType == 'GroupLineDetail':
                if account_line_item.DetailType == 'SalesItemLineDetail':
                    prod_qbook_id = account_line_item.SalesItemLineDetail.ItemRef.value
                    # print "prodddddIIIIIDDDDDDDDD111111111",prod_qbook_id
                else:
                    prod_qbook_id = account_line_item.GroupLineDetail.GroupItemRef.get('value')
                    # print "prodddddIIIIIDDDDDDDDD111111111",prod_qbook_id


                if account_line_item.DetailType == 'SalesItemLineDetail':
                    prod_qbook_name = account_line_item.SalesItemLineDetail.ItemRef.name
                    # print "prodddddIIIIIDDDDDDNAMEEEEEE111",prod_qbook_name
                else:
                    prod_qbook_name = account_line_item.GroupLineDetail.GroupItemRef.get('name')
                    # print "prodddddIIIIIDDDDDDNAMEEEEEE111",prod_qbook_name

                if account_line_item.DetailType == 'SalesItemLineDetail':
                    prod_qbook_qty = account_line_item.SalesItemLineDetail.Qty
                    # print "prodddddQQQQtyyyyyyyyyyy1111111",prod_qbook_qty
                else:
                    prod_qbook_qty = account_line_item.GroupLineDetail.Quantity
                    # print "prodddddQQQQtyyyyyyyyyyy1111111",prod_qbook_qty

                if account_line_item.DetailType == 'SalesItemLineDetail':
                    prod_qbook_price = account_line_item.SalesItemLineDetail.UnitPrice
                else:
                    total = sum(total_bundle.get('Amount') for total_bundle in account_line_item.GroupLineDetail.Line)
                    # print "Totallllllbbbbbbbbbbbb",total
                    bundle_total_qty = account_line_item.GroupLineDetail.Quantity
                    # print "llllllllllllll",bundle_total_qty
                    total = total / bundle_total_qty
                    # print "Totallllllccccccccccccccccccc",total


                if prod_qbook_id:
                    temp_ids = prod_temp_obj.search([('qbooks_id', '=', prod_qbook_id)])

                    if temp_ids:
                        temp_id = temp_ids[0]
                        # print "iffffffffp_iddddddddddd",temp_id
                        # temp_ids.write(prd_tmp_vals)
                        # print "TEMP00000000000000",temp_id
                    else:
                        # print "ELSEEEEEEEEEEEEEEEEE"
                        item = Item()
                        query_item = Item.get(prod_qbook_id, qb=qb_invoice_item)
                        # print "query_itemquerrrrrrrr$$$$$$",query_item
                        # print "TYPE#############",query_item.Type

                        prd_tmp_vals = {
                                'qbooks_id': query_item.Id,
                                'name': query_item.Name,
                                'list_price': query_item.UnitPrice  or 0.00,
                                'standard_price': query_item.PurchaseCost  or 0.00,
                                'description_sale': query_item.Description,
                                }
                        # print "prodddddvalsssssssssssssss",prd_tmp_vals

                        if query_item.Type =='Inventory' or query_item.Type =='Group':
                            prd_tmp_vals.update({'type': 'product'})
                        elif query_item.Type =='NonInventory':
                            prd_tmp_vals.update({'type': 'consu'})
                        else:
                            prd_tmp_vals.update({'type': 'service'})


                        temp_ids = prod_temp_obj.search([('qbooks_id', '=', query_item.Id)])

                        if temp_ids:
                            temp_ids.write(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            # print "ifffffffffTEMP",temp_id
                        else:
                            temp_ids = prod_temp_obj.create(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            self._cr.commit()

                        if query_item.Type == 'Group':
                            # print "Groupppppppppppp", query_item.Type
                            # print "BuncleProceeeeeeeeee", query_item.UnitPrice
                            # print "BuncleAMntttttttttt", query_item.Amount

                            for bundle in query_item.ItemGroupDetail.get('ItemGroupLine'):
                                bundle_item_qty = bundle.get('Qty')
                                bundle_item_id = bundle.get('ItemRef').get('value')
                                prod_bundle_ids = product_obj.search([('qbooks_id', '=', bundle_item_id)])
                                if prod_bundle_ids:
                                    prod_bundle_id = prod_bundle_ids[0]
                                    # print "prod_bundle_idddddddddddd",prod_bundle_id
                                else:
                                    item = Item()
                                    query_item = Item.get(bundle_item_id, qb=qb_invoice_item)
                                    # print "query_itemSSSSSSSSSSS",query_item

                                    prd_vals = {
                                            'qbooks_id': query_item.Id,
                                            'name': query_item.Name,
                                            'list_price': query_item.UnitPrice  or 0.00,
                                            'standard_price': query_item.PurchaseCost  or 0.00,
                                            'description_sale': query_item.Description,
                                            }
                                    # print "prod_valsssssssssssssssss",prd_vals

                                    if query_item.Type =='Inventory' or query_item.Type =='Group':
                                        prd_vals.update({'type': 'product'})
                                    elif query_item.Type =='NonInventory':
                                        prd_vals.update({'type': 'consu'})
                                    else:
                                        prd_vals.update({'type': 'service'})

                                    prod_bundle_ids = product_obj.search([('qbooks_id', '=', query_item.Id)])
                                    if prod_bundle_ids:
                                        prod_bundle_id = prod_bundle_ids[0]
                                        prod_bundle_id.write(prd_vals)
                                    else:
                                        prod_bundle_id = product_obj.create(prd_vals)
                                        self._cr.commit()

                                product_ids = product_obj.search([('product_tmpl_id','=', temp_id.id)])
                                # print "TEMPPPMAINNNNNNNProdProd",product_ids

                                if product_ids:
                                    product_id = product_ids[0]

                                    bndl_id = bundle_obj.search([('name','=', prod_bundle_id.id),('prod_id','=', product_id.id)])
                                    # print "bndl_iddddddddddddddd",bndl_id

                                    if not bndl_id:
                                        bundle_id = bundle_obj.create({
                                            'name':  prod_bundle_id.id,
                                            # 'prod_id':pp and pp.id or False,
                                            'prod_id': product_id.id,
                                            'quantity': bundle_item_qty,
                                        })

                                        product_id.bundle_product = True

                    product_ids = product_obj.search([('product_tmpl_id','=', temp_id.id)])

                    if product_ids:
                        product_id = product_ids[0]

                    acc_line = {
                        'product_id' : product_id and product_id.id,
                        'name': prod_qbook_name or temp_id.name,
                        'quantity': float(prod_qbook_qty),
                        'invoice_id': inv_id.id,
                        'invoice_line_tax_ids': False,
                        'qbook_id': account_line_item.Id,
                        'account_id': partner_id.property_account_receivable_id.id,
                        'uom_id': product_id.uom_id.id,

                        # 'product_uom': temp_id and temp_id.uom_id.id
                    }
                    # print "LINE_VALSSSSSSSSSSSSSS",acc_line

                    if not accounttax_id == False:
                        # print "aaaaaaaaaaaaaaaaaa",accounttax_id
                        # acc_line['invoice_line_tax_ids'] = [(6, 0, [accounttax_id.id])]
                        acc_line['invoice_line_tax_ids'] = [(6, 0, [tax.id for tax in tax_idss])]
                        # print "iiiiifffffffacc_line['tax_id']ddddddddddd",acc_line['invoice_line_tax_ids']
                    else:
                        # print "eeeeeeeeeeeeeee"
                        acc_line['invoice_line_tax_ids'] =[]


                    if account_line_item.DetailType == 'SalesItemLineDetail':
                        # print "PPPPPPPPPPPPPPPPPPPPP",account_line_item.SalesItemLineDetail.UnitPrice
                        acc_line.update({'price_unit': prod_qbook_price})

                    elif account_line_item.DetailType == 'GroupLineDetail':
                    # print "ELSEELLLLLprodddddqtPriceeeeee2222222222222",prod_qbook_price
                        # acc_line.update({'price_unit': query_invoice.TotalAmt})
                        # acc_line.update({'price_unit': float(bundle_new_price)})
                        acc_line.update({'price_unit': total})


                    acc_line_ids = account_invoice_line_obj.search([('invoice_id', '=', inv_id.id),('qbook_id', '=',account_line_item.Id)])
                    # print ("Lineidddddddsssssss",acc_line_ids,account_line_item.Id)

                    if acc_line_ids:
                        line_id = acc_line_ids[0]
                        line_id.write(acc_line)
                        # print ("LINEEEEEEE",line_id)
                    else:
                        line_id = account_invoice_line_obj.create(acc_line)
                        # print ("elseeeeeLINEEEEEEE",line_id)
        self.env.cr.commit()
        return True



    # @api.one
    def qbookManageDiscountInvoice(self, inv_id, query_invoice, qb_invoice_item,partner_id):
        # print ("qbookManageDiscountttttttttttttt",inv_id,sales_order_query,qb_order_item)

        # sale_order_line_obj = self.env['sale.order.line']
        account_invoice_line_obj = self.env['account.move.line']
        product_obj = self.env['product.product']

        for line_item in query_invoice.Line:
            if line_item.DetailType == 'DiscountLineDetail':
                discount_line = line_item.DiscountLineDetail
                # print "discount_lineeeeeeeeeeeeeee",discount_line
                dis_name = discount_line.DiscountAccountRef.get('name')
                # print "discount_nmameeeeeeeeeeeeee",dis_name
                dis_id = discount_line.DiscountAccountRef.get('value')
                # print "discount_idddddddddddddddddddddd",dis_id

                discount_line_amount = line_item.Amount
                # print "discount_line_amounttttttttt",discount_line_amount

                # p_id = False
                # p_ids = product_obj.search([('name','=',dis_name),('type','=','service')])
                # print ("P_IDSSSSSSSSSSSS",p_id)

                # if p_ids:
                #     p_id = p_ids[0]
                #     print ("iiiffffffffP_IDSSSSSSSSSSS",p_id)
                # else:
                #     p_id = product_obj.create({
                #         'name': dis_name,
                #         'type': 'service'
                #         })
                #     print ("elseeeeeeeeP_IDSSSSSSSSSS",p_id)
                #     self._cr.commit()

                line = {
                    # 'product_id' : p_id and p_id.id,
                    'product_id' : self.discount_product.id,
                    'price_unit': -float(discount_line_amount),
                    # 'name': p_id.name,
                    'name': self.discount_product.name,
                    'quantity': 1,
                    'invoice_id': inv_id.id,
                    'tax_id': False,
                    'qbook_id':dis_id,
                    'invoice_line_tax_ids': False,
                    'account_id': partner_id.property_account_receivable_id.id,
                    # 'uom_id': p_id.uom_id.id,
                    'uom_id': self.discount_product.uom_id.id,
                }
                # print ("LINEEEEEEEEE",line)

                line_ids = account_invoice_line_obj.search([('invoice_id', '=', inv_id.id), ('qbook_id', '=', dis_id)])
                if line_ids:
                    line_id = line_ids[0]
                    # print ("line_idsssssssssss",line_ids)
                    # logger.info('order line id ===> %s', line_id.name)
                    line_id.write(line)
                else:
                    # print "====elseeeeeeline===>",line
                    line_id = account_invoice_line_obj.create(line)
                self.env.cr.commit()
        return True



    # @api.multi
    def import_vendor_bill(self):
        # print "VBVBVBVBBVBVBVBBVBV",self
        # sale_order_obj = self.env['sale.order']
        account_invoice_obj = self.env['account.move']
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']
        # qbook_id_vendor

        for rec in self:
            bill_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_bill_item = QuickBooks(
                                        session_manager= bill_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )
            # invoice = Invoice()
            # invoices = Invoice.all(qb=qb_bill_item)
            try:
                bill = Bill()
                # line = AccountBasedExpenseLine()
                bills = Bill.all(qb=qb_bill_item)
    #
                for bill_data in bills:
                    query_bill = Bill.get(bill_data.Id, qb=qb_bill_item)
                    # print "invoiceiddddddd",query_bill.Id
                    # print "invoiceiNOOOOOO",query_bill.DocNumber

                    vend_id = query_bill.VendorRef.value
                    # print "vend_idddddddddddddd",vend_id

                    vend_name = query_bill.VendorRef.name
                    # print "vend_nameeeeeeeeeeee",vend_name


                    if not vend_id:
                        partner_id = self[0].partner_id
                        # print "ifffffNOTVIDDDDDDDD",partner_id
                    else:
                        part_ids = res_partner_obj.search([('qbook_id', '=', vend_id)])
                        # print "ELSEEEEEEEpart_idssssssss",part_ids
                        if part_ids:
                            vend_id = part_ids[0]
                            # print "iffffffpart_iddddd",vend_id
                        else:
                            # print "esleeeeeeeeeeeeeeee"
                            vendor = Vendor()
                            query_vendor = Vendor.get(vend_id, qb=qb_bill_item)


                            company_id = False
                            company_id = query_vendor.CompanyName

                            if company_id:
                                company_ids = res_partner_obj.search([('name', '=', company_id)])
                                # print "ccccccccccoooooommpppp",company_ids
                                if not company_ids:
                                    company_id = res_partner_obj.create({'name':company_id}).id
                                    # print "ccccccccccoooommmmppp1111111111111",company_id
                                else:
                                    # print "cccccccccc222222222"
                                    company_id = company_ids[0].id
                                    # print "ccccccccccooooommmppp222222222..22222222222"

                            country_ids  = False

                            if query_vendor.BillAddr:
                                v_country = query_vendor.BillAddr.Country
                                v_country = v_country.upper()
                                v_state = query_vendor.BillAddr.CountrySubDivisionCode
                                v_state = v_state.upper()
                                v_city = query_vendor.BillAddr.City
                                v_postalcode = query_vendor.BillAddr.PostalCode
                                v_line1 = query_vendor.BillAddr.Line1
                                v_line2 = query_vendor.BillAddr.Line2
                            else:
                                v_country  = False
                                v_state = False
                                v_city = False
                                v_postalcode = False
                                v_line1 = False
                                v_line2 = False

                            if v_country != False:
                                country_ids = country_obj.search([('code', '=', v_country)])
                                # print "ccccccccccccccccc",country_ids
                                if not country_ids:
                                    country_id = country_obj.create({'name':v_country, 'code':v_country}).id
                                    # print "ccccccccccccccccc1111111111",country_ids
                                else:
                                    country_id = country_ids[0].id
                                    # print "ccccccccccccccccc22222222222",country_id
                            else:
                                # print "ccccccccccccccccc33333333333",country_ids
                                country_id = False

                            # bstate = query_vendor.BillAddr.CountrySubDivisionCode
                            # bstate = bstate.upper()

                            if v_state != False:
                                state_ids = state_obj.search([('code', '=', v_state),('country_id', '=', country_id)])
                                if not state_ids:
                                    state_id = state_obj.create({'name':v_state, 'code':v_state, 'country_id': country_id}).id
                                else:
                                    state_id = state_ids[0].id
                                    # logger.info('state id ===> %s', state_id)
                            else:
                                state_id = False

                            # print "=======================",query_vendor,query_vendor.PrimaryEmailAddr
                            # print"Vendor1099", query_vendor.Vendor1099

                            vals = {
                                    'qbook_id': query_vendor.Id,
                                    'name': query_vendor.DisplayName,
                                    'customer' : False,
                                    'supplier' : True,
                                    'street':v_line1,
                                    'street2' : v_line2,
                                    'city': v_city,
                                    'zip': v_postalcode,
                                    'phone': query_vendor.PrimaryPhone.FreeFormNumber if query_vendor.PrimaryPhone != None else '',
                                    'state_id' :state_id,
                                    'country_id': country_id,
                                    'email': query_vendor.PrimaryEmailAddr.Address if query_vendor.PrimaryEmailAddr != None else '',
                                    'parent_id': company_id,
                                    'website': query_vendor.WebAddr.URI if query_vendor.WebAddr != None else '',

                                    'vendor1099':query_vendor.Vendor1099 if query_vendor.Vendor1099 != None else '',
                                    'print_on_check_name':query_vendor.PrintOnCheckName,
                                    'balance':query_vendor.Balance if query_vendor.Balance != None else '',
                                    'acc_num':query_vendor.AcctNum if query_vendor.AcctNum != None else '',
                                    }

                            # print "valsssssssssssssssssss",vals
                            vendor_ids = res_partner_obj.search([('qbook_id', '=', query_vendor.Id)])
                            # print"==========>vendor_ids>>>>>>>>>>",vendor_ids
                            if not vendor_ids:
                                vend_id = res_partner_obj.create(vals)
                                # print "IFFFFFFFNNOTTTTVVVVVVVVVVVVV",vend_id
                            else:
                                vend_id = vendor_ids[0]
                                # print "ELSE2222VVVVVVVV",vend_id
                                vend_id.write(vals)
                                # print "ELSE2222VVVVVVVV",vend_id

                    # bill_vals = {
                    #               'partner_id': vend_id.id,
                    #               'qbook_id' : query_purchaseorder.Id,
                    #               'name': query_purchaseorder.DocNumber,
                    #               'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    #                 }

                    bill_vals = {
                                  'partner_id': vend_id.id,
                                  'qbook_id_vendor' : query_bill.Id,
                                  'number': query_bill.DocNumber if query_bill.DocNumber else False,
                                  # 'invoice_no':query_bill.DocNumber,
                                  'name':query_bill.DocNumber,
                                  # 'payment_method':payment_id.id if payment_id != False else '',
                                  'date_invoice': query_bill.TxnDate,
                                  'date_due': query_bill.DueDate,
                                    }

                    # print "bill_valssssssssssssss",bill_vals


                    # query_vendor.PrimaryPhone.FreeFormNumber if query_vendor.PrimaryPhone != None else '',

                    vendor_bill_ids = account_invoice_obj.search([('qbook_id_vendor', '=', bill_data.Id)])


                    if not vendor_bill_ids:
                        acc_vid = account_invoice_obj.create(bill_vals)
                        self._cr.commit()
                        self.QbookManageBillLines(acc_vid, query_bill, qb_bill_item, vend_id)
                    else:
                        if vendor_bill_ids.state != 'done':
                            acc_vid = vendor_bill_ids[0]
                            acc_vid.write(bill_vals)
                            self.QbookManageBillLines(acc_vid, query_bill, qb_bill_item, vend_id)
                    self.env.cr.commit()

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_vendor_bill', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.one
    def QbookManageBillLines(self, acc_vid, query_bill, qb_bill_item, vend_id):
        # print "QbookManageBillLinessssss......",acc_vid, query_bill, qb_bill_item, vend_id

        account_invoice_line_obj = self.env['account.move.line']
        prod_temp_obj = self.env['product.template']
        product_obj = self.env['product.product']
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']
        accounttax_obj = self.env['account.tax']

        tax_id = []
        accounttax_id = False

        for bill_line_item in query_bill.Line:
            # print "lineeeeeeeeee",bill_line_item
            # print "DetailTypeeee",bill_line_item.DetailType
            # if bill_line_item.DetailType == 'AccountBasedExpenseLineDetail':
            #     print "1111111111111111111",bill_line_item.DetailType
            #     tax = bill_line_item.AccountBasedExpenseLineDetail.TaxCodeRef.value
            #     print "ttttttttttttttttttt",tax
            #     if tax == 'TAX':
            #         for tax_line in query_bill.TxnTaxDetail.TaxLine:
            #             tex_DetailType = tax_line.DetailType
            #             if tex_DetailType == 'TaxLineDetail':
            #                 tax_qb_id  = tax_line.TaxLineDetail.TaxRateRef.value
            #                 tax_id = accounttax_obj.search([('qbook_id','=',tax_qb_id)])
            #                 if tax_id:
            #                     accounttax_id = tax_id[0]
            #     else:
            #         accounttax_id = False


            if bill_line_item.DetailType == 'ItemBasedExpenseLineDetail':
                prod_qbook_id = bill_line_item.ItemBasedExpenseLineDetail.ItemRef.value
                # print "prodddddIIIIIDDDDDDDDD111111111",prod_qbook_id
                prod_qbook_name = bill_line_item.ItemBasedExpenseLineDetail.ItemRef.name
                # print "prodddddIIIIIDDDDDDNAMEEEEEE111",prod_qbook_name
                prod_qbook_qty = bill_line_item.ItemBasedExpenseLineDetail.Qty
                # print "prodddddQQQQtyyyyyyyyyyy1111111",prod_qbook_qty
                prod_qbook_price = bill_line_item.ItemBasedExpenseLineDetail.UnitPrice
                # print "prodddddqtPriceeeeee1111111111111",prod_qbook_price

                if prod_qbook_id:
                    temp_ids = prod_temp_obj.search([('qbooks_id', '=', prod_qbook_id)])

                    if temp_ids:
                        temp_id = temp_ids[0]
                        # print "iffffffffp_iddddddddddd",temp_id
                        # temp_ids.write(prd_tmp_vals)
                        # print "TEMP00000000000000",temp_id
                    else:
                        # print "ELSEEEEEEEEEEEEEEEEE"
                        item = Item()
                        query_item = Item.get(prod_qbook_id, qb=qb_bill_item)
                        # print "query_itemquerrrrrrrr$$$$$$",query_item
                        # print "TYPE#############",query_item.Type

                        prd_tmp_vals = {
                                'qbooks_id': query_item.Id,
                                'name': query_item.Name,
                                'list_price': query_item.UnitPrice  or 0.00,
                                'standard_price': query_item.PurchaseCost  or 0.00,
                                'description_sale': query_item.Description,
                                }
                        # print "prodddddvalsssssssssssssss",prd_tmp_vals

                        if query_item.Type =='Inventory' or query_item.Type =='Group':
                            prd_tmp_vals.update({'type': 'product'})
                        elif query_item.Type =='NonInventory':
                            prd_tmp_vals.update({'type': 'consu'})
                        else:
                            prd_tmp_vals.update({'type': 'service'})


                        temp_ids = prod_temp_obj.search([('qbooks_id', '=', query_item.Id)])

                        if temp_ids:
                            temp_ids.write(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            # print "ifffffffffTEMP",temp_id
                        else:
                            temp_ids = prod_temp_obj.create(prd_tmp_vals)
                            temp_id = temp_ids[0]
                            self._cr.commit()


                    product_ids = product_obj.search([('product_tmpl_id','=', temp_id.id)])
                    if product_ids:
                        product_id = product_ids[0]
                        # print ("product_iddddddddddds",product_id)

                    acc_line = {
                        'product_id' : product_id and product_id.id,
                        'name': prod_qbook_name or temp_id.name,
                        'quantity': float(prod_qbook_qty),
                        'invoice_id': acc_vid.id,
                        'invoice_line_tax_ids': False,
                        'qbook_id': bill_line_item.Id,
                        'account_id': vend_id.property_account_receivable_id.id,
                        'price_unit': prod_qbook_price,
                    }
                    # print "LINE_VALSSSSSSSSSSSSSS",acc_line

                    # if not accounttax_id == False:
                    #     print "aaaaaaaaaaaaaaaaaa",accounttax_id
                    #     acc_line['invoice_line_tax_ids'] = [(6, 0, [accounttax_id.id])]
                    #     print ("iiiiifffffffline['tax_id']ddddddddddd",acc_line['invoice_line_tax_ids'])
                    # else:
                    #     print "eeeeeeeeeeeeeee"
                    #     acc_line['invoice_line_tax_ids'] =[]



                    if bill_line_item.ItemBasedExpenseLineDetail.BillableStatus == 'Billable':
                        # print "BILLLLLLL===>>>",bill_line_item.ItemBasedExpenseLineDetail.BillableStatus
                        acc_line.update({'is_billable':True})

                    elif bill_line_item.ItemBasedExpenseLineDetail.BillableStatus == 'NotBillable':
                        # print "BILLLLLLL===>>>",bill_line_item.ItemBasedExpenseLineDetail.BillableStatus
                        acc_line.update({'is_billable':False})


                    if bill_line_item.ItemBasedExpenseLineDetail.CustomerRef:
                        qbook_line_cust_id = bill_line_item.ItemBasedExpenseLineDetail.CustomerRef.value
                        # print "LINEEEECUSTIDDDDDDd",qbook_line_cust_id

                        qbook_line_cust_name = bill_line_item.ItemBasedExpenseLineDetail.CustomerRef.name
                        # print "LINEEEECUSTNameeeee",qbook_line_cust_name

                        if not qbook_line_cust_id:
                            line_cust_id = self[0].line_cust_id
                        else:
                            line_cust_ids = res_partner_obj.search([('qbook_id', '=', qbook_line_cust_id)])
                            if line_cust_ids:
                                line_cust_id = line_cust_ids[0]
                            else:
                                customer = Customer()
                                query_customer = Customer.get(qbook_line_cust_id, qb=qb_bill_item)
                                company_id = False
                                company_id = query_customer.CompanyName
                                if company_id:
                                    company_ids = res_partner_obj.search([('name', '=', company_id)])
                                    if not company_ids:
                                        company_id = res_partner_obj.create({'name':company_id}).id
                                    else:
                                        company_id = company_ids[0].id
                                country_ids  = False
                                if query_customer.BillAddr:
                                    c_country = query_customer.BillAddr.Country
                                    c_country = c_country.upper()
                                    c_state = query_customer.BillAddr.CountrySubDivisionCode
                                    c_state = c_state.upper()
                                    c_city = query_customer.BillAddr.City
                                    c_postalcode = query_customer.BillAddr.PostalCode
                                    c_line1 = query_customer.BillAddr.Line1
                                    c_line2 = query_customer.BillAddr.Line2
                                else:
                                    c_country  = False
                                    c_state = False
                                    c_city = False
                                    c_postalcode = False
                                    c_line1 = False
                                    c_line2 = False
                                if c_country != False:
                                    country_ids = country_obj.search([('code', '=', c_country)])
                                    if not country_ids:
                                        country_id = country_obj.create({'name':c_country, 'code':c_country}).id
                                    else:
                                        country_id = country_ids[0].id
                                else:
                                    country_id = False
                                if c_state != False:
                                    state_ids = state_obj.search([('code', '=', c_state),('country_id', '=', country_id)])
                                    if not state_ids:
                                        state_id = state_obj.create({'name':c_state, 'code':c_state, 'country_id': country_id}).id
                                    else:
                                        state_id = state_ids[0].id
                                else:
                                    state_id = False

                                line_cust_vals = {
                                            'qbook_id': query_customer.Id,
                                            'name': query_customer.DisplayName,
                                            'customer' : True,
                                            'supplier' : False,
                                            'street':c_line1,
                                            'street2' : c_line2,
                                            'city': c_city,
                                            'zip': c_postalcode,
                                            'phone': query_customer.PrimaryPhone.FreeFormNumber if query_customer.PrimaryPhone != None else '',
                                            'state_id' :state_id,
                                            'country_id': country_id,
                                            'email': query_customer.PrimaryEmailAddr.Address if query_customer.PrimaryEmailAddr != None else '',
                                            'parent_id': company_id,
                                            'website': query_customer.WebAddr.URI if query_customer.WebAddr != None else '',
                                        }
                                line_customer_ids = res_partner_obj.search([('qbook_id', '=', query_customer.Id)])
                                if not line_customer_ids:
                                    line_cust_id = res_partner_obj.create(line_cust_vals)
                                else:
                                    line_cust_id = line_customer_ids[0]
                                    line_cust_id.write(line_cust_vals)
                        acc_line.update({'line_customer':line_cust_id and line_cust_id.id})


                    acc_bill_line_ids = account_invoice_line_obj.search([('invoice_id', '=', acc_vid.id),('qbook_id', '=',bill_line_item.Id)])
                    # print ("Lineidddddddsssssss",acc_bill_line_ids)

                    if acc_bill_line_ids:
                        line_id = acc_bill_line_ids[0]
                        line_id.write(acc_line)
                        # print ("LINEEEEEEE",line_id)
                    else:
                        line_id = account_invoice_line_obj.create(acc_line)
                        # print ("elseeeeeLINEEEEEEE",line_id)
        self.env.cr.commit()
        return True




    # @api.multi
    def import_customer_payment(self):
        # print "cpcpcpcpcpcpcpcpcpcpcp",self
        # sale_order_obj = self.env['sale.order']
        account_paymant_obj = self.env['account.payment']
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']

        for rec in self:
            payment_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_payment_item = QuickBooks(
                                        session_manager= payment_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )

            try:
                payment = Payment()
                payments = Payment.all(qb=qb_payment_item)
                for payment_data in payments:
                    query_payment = Payment.get(payment_data.Id, qb=qb_payment_item)
                    # print "query_paymenttttttttt",query_payment

                    custm_id = query_payment.CustomerRef.value
                    # print "============custm_id======>",custm_id

                    # custm_name = query_payment.CustomerRef.name
                    # print "============custm_name======>",custm_name

                    # pay_method = query_payment.PaymentMethodRef
                    # print "============pay_meyhoddddd======>",pay_method

                    # a=query_payment.ARAccountRef
                    # print "============ARAccountRef======>",a

                    # b=query_payment.DepositToAccountRef
                    # print "============DepositToAccountRef======>",b

                    # c=query_payment.CurrencyRef
                    # print "============CurrencyRef======>",c

                    # d=query_payment.CreditCardPayment
                    # print "============CreditCardPayment======>",d


                    # print "============UnappliedAmt=====",query_payment.UnappliedAmt,
                    # print "============TotalAmt=====",query_payment.TotalAmt,

                    if not custm_id:
                        # print("===custm_idcustm_idcustm_id======>",custm_id)
                        partner_id = self[0].partner_id
                    else:
                        # print ("==esleeeeeeee2222222==***********")
                        customer = Customer()
                        query_customer = Customer.get(custm_id, qb=qb_payment_item)

                        company_id = False
                        company_id = query_customer.CompanyName

                        if company_id:
                            company_ids = res_partner_obj.search([('name', '=', company_id)])
                            # print "cccccccccc",company_ids
                            if not company_ids:
                                company_id = res_partner_obj.create({'name':company_id}).id
                                # print "cccccccccc1111111111111",company_id
                            else:
                                # print "cccccccccc222222222"
                                company_id = company_ids[0].id
                                # print "cccccccccc222222222..22222222222"

                        country_ids = False

                        if query_customer.BillAddr:
                            c_country = query_customer.BillAddr.Country
                            c_country = c_country.upper()
                            c_state = query_customer.BillAddr.CountrySubDivisionCode
                            c_state = c_state.upper()
                            c_city = query_customer.BillAddr.City
                            c_postalcode = query_customer.BillAddr.PostalCode
                            c_line1 = query_customer.BillAddr.Line1
                            c_line2 = query_customer.BillAddr.Line2
                            # print "IIIIIFFFFFFBillLLLLLL",c_country,c_country,c_state,c_city,c_postalcode,c_line1,c_line2
                        else:
                            c_country  = False
                            c_state = False
                            c_city = False
                            c_postalcode = False
                            c_line1 = False
                            c_line2 = False
                            # print "ElseeeeeeeeBillLLLLLL",c_country,c_country,c_state,c_city,c_postalcode,c_line1,c_line2


                        if c_country != False:
                            country_ids = country_obj.search([('code', '=', c_country)])
                            if not country_ids:
                                country_id = country_obj.create({'name':c_country, 'code':c_country}).id
                            else:
                                country_id = country_ids[0].id
                                # logger.info('country id ===> %s', country_id)
                        else:
                            country_id = False


                        if c_state != False:
                            state_ids = state_obj.search([('code', '=', c_state),('country_id', '=', country_id)])
                            if not state_ids:
                                state_id = state_obj.create({'name':c_state, 'code':c_state, 'country_id': country_id}).id
                            else:
                                state_id = state_ids[0].id
                                # logger.info('state id ===> %s', state_id)
                        else:
                            state_id = False

                        cust_vals = {
                                    'qbook_id': query_customer.Id,
                                    'name': query_customer.DisplayName,
                                    'customer' : True,
                                    'supplier' : False,
                                    'street':c_line1,
                                    'street2' : c_line2,
                                    'city': c_city,
                                    'zip': c_postalcode,
                                    'phone': query_customer.PrimaryPhone.FreeFormNumber if query_customer.PrimaryPhone != None else '',
                                    'state_id' :state_id,
                                    'country_id': country_id,
                                    'email': query_customer.PrimaryEmailAddr.Address if query_customer.PrimaryEmailAddr != None else '',
                                    'parent_id': company_id,
                                    'website': query_customer.WebAddr.URI if query_customer.WebAddr != None else '',
                                }

                        # print "cust_valsssssssssssssssssss",cust_vals
                        customer_ids = res_partner_obj.search([('qbook_id', '=', query_customer.Id)])
                        # print"==========>customer_ids>>>>>>>>>>",customer_ids
                        if not customer_ids:
                            partner_id = res_partner_obj.create(cust_vals)
                        else:
                            partner_id = customer_ids[0]
                            # logger.info('customer id ===> %s', cust_id.name)
                            partner_id.write(cust_vals)

                    # print "cust_iddddddddddddddd",partner_id
                    # print "query_payment.TotalAmt",query_payment.TotalAmt


                    # journal_id = self.env['account.journal'].search([('type','=','bank')])
                    # print "journal_iddddddddddddddddddd",journal_id

                    payment_vals = {

                                   'qbook_id':query_payment.Id,
                                   'partner_type':'customer' ,
                                   'partner_id': partner_id.id,
                                   'payment_date': query_payment.TxnDate,
                                   # 'journal_id': journal_id.id,
                                   'journal_id': self.customer_journal_id.id,

                                   # 'amount': abs(query_payment.TotalAmt),
                                   # 'communication': row[4],
                                   'payment_method_id': 1 ,
                                   'state': 'draft',
                                   'payment_type': 'inbound' ,
                                   }

                    if query_payment.TotalAmt > 0:
                        payment_vals.update({'amount': query_payment.TotalAmt})
                    else:
                        continue

                    # print "payment_valsssssssssssssss",payment_vals

                    payment_ids = account_paymant_obj.search([('qbook_id', '=', query_payment.Id)])
                    # print ("payment_idsIDDDDDDDD",payment_ids)

                    # if not payment_ids:
                    #     pay_id = account_paymant_obj.create(payment_vals)
                    #     # self._cr.commit()
                    #     print "crreateeeeeeeeeeee",pay_id
                    # else:
                    #     pay_id = payment_ids[0]
                    #     print ("elseeeeeeeeeeee",pay_id,pay_id.name)
                    # self.env.cr.commit()



                    if not payment_ids:
                        pay_id = account_paymant_obj.create(payment_vals)
                        # pay_id.write(payment_vals)
                    else:
                        payment_ids.write(payment_vals)

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_customer_payment', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def import_vendor_payment(self):
        # print "vpvpvpvpvpvp",self
        # sale_order_obj = self.env['sale.order']
        account_paymant_obj = self.env['account.payment']
        res_partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        state_obj = self.env['res.country.state']

        for rec in self:
            vendor_payment_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_vendor_payment_item = QuickBooks(
                                        session_manager= vendor_payment_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )
            try:
                bill_payment = BillPayment()
                bill_payments = BillPayment.all(qb=qb_vendor_payment_item)

                for bill_payment_data in bill_payments:
                    query_venfor_payment = BillPayment.get(bill_payment_data.Id, qb=qb_vendor_payment_item)
                    # print "query_paymenttttttttt",query_venfor_payment

                    vend_id = query_venfor_payment.VendorRef.value
                    # print "============custm_id======>",vend_id

                    vend_name = query_venfor_payment.VendorRef.name
                    # print "============vend_name======>",vend_name

                    pay_type = query_venfor_payment.PayType
                    # print "============pay_type======>",pay_type


                    # b = query_venfor_payment.CheckPayment
                    # print "============CheckPayment======>",b

                    if pay_type == 'Check' or pay_type == 'CreditCard':
                        if pay_type == 'Check':
                            # print "iffffffffchkeeeeeeee",pay_type
                            journal_ids = self.env['account.journal'].search([('name','=','Check')])
                            if journal_ids:
                                journal_id = journal_ids[0]
                                # print "iffffffffchkeeeeeeeejjjjjjjjjj",journal_id
                            else:
                                journal_vals = {
                                    'name': pay_type,
                                    'type': 'bank',
                                    'code':'CHK1',
                                    # 'qbook_id':
                                    }
                                # print "chk_valsssssssssssss",journal_vals
                                journal_ids = self.env['account.journal'].create(journal_vals)
                                journal_id = journal_ids[0]
                                # print "elseeeeeeeeeeechkeeeeeeeejjjjjjjjjj",journal_id

                        elif pay_type == 'CreditCard':
                            # print "iffffffffCreditCarddddddd",pay_type
                            journal_ids = self.env['account.journal'].search([('name','=','CreditCard')])
                            if journal_ids:
                                journal_id = journal_ids[0]
                                # print "iffffffffffffCredircardddddjjjjjjjjjj",journal_id
                            else:
                                journal_vals = {
                                    'name': pay_type,
                                    'type': 'bank',
                                    'code':'CCARD1',
                                    }
                                # print "carddddddd_valsssssssssssss",journal_vals
                                journal_ids = self.env['account.journal'].create(journal_vals)
                                journal_id = journal_ids[0]
                                # print "elseeeeeeeeeeeCredircardddddjjjjjjjjjj",journal_id
                        else:
                            journal_id =  self.customer_journal_id,
                            # print "**********************",self.customer_journal_id,
                            # journal_id = self.env['account.journal'].search([('type','=','bank')])
                            # print "elseeeeeeeeeeejjjjjjjjjjlastttt",journal_id


                    # print "journal_iddddddddddddddddddd",journal_id

                    # if query_venfor_payment.CheckPayment:
                    #     if query_venfor_payment.CheckPayment.BankAccountRef:
                    #         bb_n = query_venfor_payment.CheckPayment.BankAccountRef.name
                    #         # print "============CheckPaymentNAMEEE======>",bb_n

                    #         bb_v = query_venfor_payment.CheckPayment.BankAccountRef.value
                    #         # print "============CheckPaymentIDDDDDDDD======>",bb_v


                    # c = query_venfor_payment.CreditCardPayment
                    # print "============BankAccountRef======>",c

                    # if query_venfor_payment.CreditCardPayment:
                    #     cc = query_venfor_payment.CreditCardPayment.CCAccountRef
                    #     print "============CreditCardPayment.CCAccountRef======>",cc


                    # d = query_venfor_payment.APAccountRef
                    # print "============APAccountRef======>",d

                    # a = query_venfor_payment.DepartmentRef
                    # print "============DepartmentRef======>",a

                    # e = query_venfor_payment.CurrencyRef
                    # print "============CurrencyRef======>",e



                    if not vend_id:
                        partner_id = self[0].partner_id
                        # print "ifffffNOTVIDDDDDDDD",partner_id
                    else:
                        part_ids = res_partner_obj.search([('qbook_id', '=', vend_id)])
                        # print "ELSEEEEEEEpart_idssssssss",part_ids
                        if part_ids:
                            vend_id = part_ids[0]
                            # print "iffffffpart_iddddd",vend_id
                        else:
                            # print "esleeeeeeeeeeeeeeee"
                            vendor = Vendor()
                            query_vendor = Vendor.get(vend_id, qb=qb_bill_item)

                            company_id = False
                            company_id = query_vendor.CompanyName

                            if company_id:
                                company_ids = res_partner_obj.search([('name', '=', company_id)])
                                # print "ccccccccccoooooommpppp",company_ids
                                if not company_ids:
                                    company_id = res_partner_obj.create({'name':company_id}).id
                                    # print "ccccccccccoooommmmppp1111111111111",company_id
                                else:
                                    # print "cccccccccc222222222"
                                    company_id = company_ids[0].id
                                    # print "ccccccccccooooommmppp222222222..22222222222"

                            country_ids  = False

                            if query_vendor.BillAddr:
                                v_country = query_vendor.BillAddr.Country
                                v_country = v_country.upper()
                                v_state = query_vendor.BillAddr.CountrySubDivisionCode
                                v_state = v_state.upper()
                                v_city = query_vendor.BillAddr.City
                                v_postalcode = query_vendor.BillAddr.PostalCode
                                v_line1 = query_vendor.BillAddr.Line1
                                v_line2 = query_vendor.BillAddr.Line2
                            else:
                                v_country  = False
                                v_state = False
                                v_city = False
                                v_postalcode = False
                                v_line1 = False
                                v_line2 = False

                            if v_country != False:
                                country_ids = country_obj.search([('code', '=', v_country)])
                                # print "ccccccccccccccccc",country_ids
                                if not country_ids:
                                    country_id = country_obj.create({'name':v_country, 'code':v_country}).id
                                    # print "ccccccccccccccccc1111111111",country_ids
                                else:
                                    country_id = country_ids[0].id
                                    # print "ccccccccccccccccc22222222222",country_id
                            else:
                                # print "ccccccccccccccccc33333333333",country_ids
                                country_id = False

                            # bstate = query_vendor.BillAddr.CountrySubDivisionCode
                            # bstate = bstate.upper()

                            if v_state != False:
                                state_ids = state_obj.search([('code', '=', v_state),('country_id', '=', country_id)])
                                if not state_ids:
                                    state_id = state_obj.create({'name':v_state, 'code':v_state, 'country_id': country_id}).id
                                else:
                                    state_id = state_ids[0].id
                                    # logger.info('state id ===> %s', state_id)
                            else:
                                state_id = False

                            # print "=======================",query_vendor,query_vendor.PrimaryEmailAddr
                            # print"Vendor1099", query_vendor.Vendor1099

                            vals = {
                                    'qbook_id': query_vendor.Id,
                                    'name': query_vendor.DisplayName,
                                    'customer' : False,
                                    'supplier' : True,
                                    'street':v_line1,
                                    'street2' : v_line2,
                                    'city': v_city,
                                    'zip': v_postalcode,
                                    'phone': query_vendor.PrimaryPhone.FreeFormNumber if query_vendor.PrimaryPhone != None else '',
                                    'state_id' :state_id,
                                    'country_id': country_id,
                                    'email': query_vendor.PrimaryEmailAddr.Address if query_vendor.PrimaryEmailAddr != None else '',
                                    'parent_id': company_id,
                                    'website': query_vendor.WebAddr.URI if query_vendor.WebAddr != None else '',

                                    'vendor1099':query_vendor.Vendor1099 if query_vendor.Vendor1099 != None else '',
                                    'print_on_check_name':query_vendor.PrintOnCheckName,
                                    'balance':query_vendor.Balance if query_vendor.Balance != None else '',
                                    'acc_num':query_vendor.AcctNum if query_vendor.AcctNum != None else '',
                                    }

                            # print "valsssssssssssssssssss",vals
                            vendor_ids = res_partner_obj.search([('qbook_id', '=', query_vendor.Id)])
                            # print"==========>vendor_ids>>>>>>>>>>",vendor_ids
                            if not vendor_ids:
                                vend_id = res_partner_obj.create(vals)
                                # print "IFFFFFFFNNOTTTTVVVVVVVVVVVVV",vend_id
                            else:
                                vend_id = vendor_ids[0]
                                # print "ELSE2222VVVVVVVV",vend_id
                                vend_id.write(vals)
                                # print "ELSE2222VVVVVVVV",vend_id


                    # journal_id = self.env['account.journal'].search([('type','=','bank')])
                    # print "journal_iddddddddddddddddddd",journal_id

                    vendor_payment_vals = {

                                   'qbook_id_vendor':query_venfor_payment.Id,
                                   'partner_type':'supplier' ,
                                   'partner_id': vend_id.id,
                                   'payment_date': query_venfor_payment.TxnDate,
                                   'journal_id': journal_id.id,
                                   'payment_method_id': 2 ,
                                   'state': 'draft',
                                   'payment_type': 'outbound',
                                   }
                    # print "vendor_payment_valssssssssssssssss",vendor_payment_vals

                    if query_venfor_payment.TotalAmt > 0:
                        vendor_payment_vals.update({'amount': query_venfor_payment.TotalAmt})
                    else:
                        continue
                    # print "vendor_payment_valsssssssssssssss",vendor_payment_vals

                    vendor_payment_ids = account_paymant_obj.search([('qbook_id_vendor', '=', query_venfor_payment.Id)])
                    # print ("vendor_payment_idsIDDDDDDDD",vendor_payment_ids)

                    if not vendor_payment_ids:
                        pay_id = account_paymant_obj.create(vendor_payment_vals)
                    else:
                        vendor_payment_ids.write(vendor_payment_vals)

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_vendor_bills_payment', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def import_account(self):
        # print "aaaaaaaaaaaaaaaaa"
        account_obj = self.env['account.account']

        for rec in self:
            account_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_account_item = QuickBooks(
                                        session_manager= account_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )


            # tax_rate = TaxRate.all(qb=qb_account_item)
            # tax_rates = TaxRate.all(max_results=1, qb=qb_account_item)

            # for tax_rate_date in tax_rate:
            #     query_tax_rate = TaxRate.get(tax_rate_date.Id, qb=qb_account_item)
            #     print "query_tax_rate_iddddddd",query_tax_rate.Id
            #     print "query_tax_nameeeeeeeeee",query_tax_rate.Name
            #     print "query_tax_valueeeeeeeee",query_tax_rate.RateValue

            try:
                account = Account()
                accounts = Account.all(qb=qb_account_item)

                for account_data in accounts:
                    query_account = Account.get(account_data.Id, qb=qb_account_item)
                    # print "query_accounttttttttttttttt",query_account
                    acc_vals ={}
                    # print"FullyQualifiedName", query_account.FullyQualifiedName
                    # print"domain",  query_account.domain
                    # print "======================"
                    # print"Name",  query_account.Name
                    # print"idddd",  query_account.Id
                    # print"Classification",  query_account.Classification
                    # print"AccountType",  query_account.AccountType
                    # print"AccountSubType",  query_account.AccountSubType

                    # print"CurrentBalanceWithSubAccounts",  query_account.CurrentBalanceWithSubAccounts
                    # print"sparse",  query_account.sparse
                    # print"CurrentBalance",  query_account.CurrentBalance
                    # print"Active",  query_account.Active
                    # print"SyncToken",  query_account.SyncToken
                    # print"Idddddddddd",  query_account.Id
                    # print"SubAccount", query_account.SubAccount
                    # code = str(query_account.domain) + str(query_account.Id)
                    # print "CODEEEEEEEEEEEE",code

                    # if query_account.ParentRef:
                    #     print "parentnameeeeeee",query_account.ParentRef.name
                    #     print "parentiddddddddd",query_account.ParentRef.value


                    if query_account.AccountType == 'Income':
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Income')])
                        # print "acc_type_id11111111111",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Other Income':
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Other Income')])
                        # ***********
                        # print "acc_type_id2222222222222",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Expense':
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Expenses')])
                        # print "acc_type_id3333333333333",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Other Current Asset':
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Current Assets')])
                        # print "acc_type_id4444444444444",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Fixed Asset':
                        # acc_type_ids = self.env['account.account.type'].search([('name','=','Fixed Assets')])
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Non-current Assets')])
                        # print "acc_type_id5555555555555",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Other Asset':
                        # Fixed Asset
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Non-current Assets')])
                        # print "acc_type_id6666666666666",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Bank':
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Bank and Cash')])
                        # print "acc_type_id7777777777777",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Equity':
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Equity')])
                        # print "acc_type_id8888888888888",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Other Current Liability':
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Current Liabilities')])
                        # *****************
                        # print "acc_type_id9999999999999",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Long Term Liability':
                        # Current Liabilities
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Non-current Liabilities')])
                        # print "acc_type_id1101010101010",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                        # acc_type_ids = self.env['account.account.type'].search([('name','=','Long Term Liability')])
                        # if acc_type_ids:
                        #     acc_type_id = acc_type_ids[0]
                        # else:
                        #     acc_vals = {
                        #         'name': query_account.Name,
                        #         'type': 'other',
                        #         'include_initial_balance':True,
                        #         # 'qbook_id':
                        #         }
                        #     acc_type_ids = self.env['account.account.type'].create(acc_vals)
                        #     acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Credit Card':
                    # ****************
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Current Liabilities')])
                        # print "acc_type_id1.1.1.1.1.1.1.1",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    if query_account.AccountType=='Cost of Goods Sold':
                        # Cost of Revenue
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Cost of Revenue')])
                        # print "acc_type_id1212121212121212121212",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                    # acc_vals = {}
                    # acc_acc = self.env['account.account']
                    if query_account.AccountType == 'Accounts Receivable':
                        # continue
                        # You cannot have a receivable/payable account that is not reconciliable. (account code: 33)

                        acc_type_ids = self.env['account.account.type'].search([('name','=','Receivable')])
                        # print "acc_type_id13131313131313131313",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]


                    if query_account.AccountType == 'Accounts Payable':
                        # continue
                        # You cannot have a receivable/payable account that is not reconciliable. (account code: 33)

                        acc_type_ids = self.env['account.account.type'].search([('name','=','Payable')])
                        # print "acc_type_id14141414141414141414",acc_type_ids
                        if acc_type_ids:
                            # print "1111111111111111",acc_type_ids
                            acc_type_id = acc_type_ids[0]


                    if query_account.AccountType=='Other Expense':
                        # acc_type_ids = self.env['account.account.type'].search([('name','=','Other Expenses')])
                        acc_type_ids = self.env['account.account.type'].search([('name','=','Expenses')])
                        # print "acc_type_id151515151515151515151",acc_type_ids
                        if acc_type_ids:
                            acc_type_id = acc_type_ids[0]

                        # else:
                        #     print "ELSEEEEEEE"
                        #     acc_vals = {
                        #         'name': query_account.AccountType,
                        #         'type': 'other',
                        #         }
                        #     print"acc_valssssssssssss",acc_vals
                        #     acc_type_ids = self.env['account.account.type'].create(acc_vals)
                        #     acc_type_id = acc_type_ids[0]
                        #     print "acc_type_idddddddd",acc_type_id



                    # print "acc_type_iddddd------------",acc_type_id
                    account_ids = account_obj.search([('qbooks_id', '=',query_account.Id)])


                    acc_vals = {
                        'name': query_account.Name,
                        'qbooks_id': query_account.Id,
                        'code': query_account.Id + query_account.domain,
                        'user_type_id':acc_type_id.id,
                        }
                    # print"==============acc_vals==>>>>>>>>>>",acc_vals

                    if query_account.AccountType =='Accounts Receivable' or query_account.AccountType =='Accounts Payable':
                        acc_vals.update({'reconcile':True })
                    # print"==============acc_vals22222222==>>>>>>>>>>",acc_vals

                    account_ids.write(acc_vals)

                    if not account_ids:
                        acc_id = account_obj.create(acc_vals)
                        acc_id.write(acc_vals)

            except Exception as e:
                # print "eeeeeeeeeeeeeeeeeeeeee",e
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_accounts', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def import_tax(self):
        # print "ttttttaaaaaaaaaaaaaaaaaxxxxxxxxx"
        tax_obj = self.env['account.tax']
        for rec in self:
            tax_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_tax_item = QuickBooks(
                                        session_manager= tax_session_manager,
                                        sandbox=True,
                                        # company_id=os.environ.get('COMPANY_ID')
                                        company_id= rec.company_id,
                                    )

            try:
                tax_rate = TaxRate.all(qb=qb_tax_item)
                for tax_rate_date in tax_rate:
                    query_tax_rate = TaxRate.get(tax_rate_date.Id, qb=qb_tax_item)
                    # print "query_tax_rate_iddddddd",query_tax_rate.Id
                    # print "query_tax_nameeeeeeeeee",query_tax_rate.Name
                    # print "query_tax_rate_valueeeeeeeee",query_tax_rate.RateValue
                    # print "query_tax_decssssssssss",query_tax_rate.Description

                    # print "query_tax_SpecialTaxType",query_tax_rate.SpecialTaxType,
                    # print "query_tax_DisplayType",query_tax_rate.DisplayType,

                    if query_tax_rate.AgencyRef:
                        # print "AgencyReffffffffffVVVVv",query_tax_rate.AgencyRef.value

                        query_tax_a = TaxAgency.get(query_tax_rate.AgencyRef.value, qb=qb_tax_item)
                        # print "aaaaaaaaaaiddddddddddddd",query_tax_a.Id
                        # print "aaaaaaaaaanameeeeeeeeeee",query_tax_a.DisplayName

                        agency_ids =self.env['account.agency'].search([('qbook_id', '=',query_tax_a)])

                        agency_vals = {
                                        'name':query_tax_a.DisplayName,
                                        'qbook_id':query_tax_a.Id,
                                      }
                        # print "agency_valsssssssssssss",agency_vals
                        if agency_ids:
                            agency_id = agency_ids[0]
                            agency_id.write(agency_vals)
                        else:
                            agency_id = self.env['account.agency'].create(agency_vals)


                    tax_ids = tax_obj.search([('name', '=',query_tax_rate.Name)])
                    # print "tax_idssssssssssssssss",tax_ids
                    tax_vals = {
                        'name': query_tax_rate.Name,
                        'qbook_id': query_tax_rate.Id,
                        'type_tax_use':'sale',
                        'amount_type':'percent',
                        'amount':query_tax_rate.RateValue,
                        'account_agency': agency_id.id,
                        }
                    # print "tax_valsssssssssssssss",tax_vals
                    tax_ids.write(tax_vals)

                    if not tax_ids:
                        # print "notttttttttttttt"
                        tax_id = tax_obj.create(tax_vals)
                        tax_id.write(tax_vals)

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'import_tax', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)

                # tax_code = TaxCode()
                # tax_codes = TaxCode.all(qb=qb_tax_item)
                # for tax_code_date in tax_codes:
                #     print "query_tax_code",tax_code_date.Name

                # tax_agency = TaxAgency()
                # print "aaaaaaaaa11111111111111111110",tax_agency
                # tax_agency = TaxAgency.all(qb=qb_tax_item)
                # print "aaaaaaaaa22222222222222222220",tax_agency
                # for tax_a in tax_agency:
                #     query_tax_a = TaxAgency.get(tax_a.Id, qb=qb_tax_item)
                #     print "aaaaaaaaaaiddddddddddddd",query_tax_a
                #     print "aaaaaaaaaanameeeeeeeeeee",query_tax_a.DisplayName



    # @api.multi
    def exportQbooksCustomers(self):
        # print "exportQbooksCustomerssssss",
        res_partner_obj = self.env['res.partner']

        for rec in self:
            cust_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,

                                    )
            qb_client = QuickBooks(
                                        session_manager= cust_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            # print "qb_client111111111111",qb_client

            # customer = Customer()
            # customer = Customer.all(qb=qb_client)
            # customer = Customer.all(max_results=1, qb=qb_client)[0]
            try:
                if self.env.context.get('export_cust'):
                    # customer_ids = self.env.context.get('export_cust')
                    customer_ids = res_partner_obj.browse(self.env.context.get('export_cust'))
                    # print "customer_ids1111111111111111",customer_ids
                else:
                    # customer_ids = res_partner_obj.browse(self.env.context.get('active_id'))
                    customer_ids = res_partner_obj.search([('to_be_exported', '=', True)])
                    # order_ids = sale_order_obj.search([('to_be_exported', '=', True)])
                    # print "customer_ids2222222222222222",customer_ids

                # print "customer_idssssssssssssssss",customer_ids
                for customer in customer_ids:
                    # print "customerrrrrrrrr",customer
                    customer_name = customer.name
                    name_list = customer_name.split(' ')
                    first_name = name_list[0]
                    # print ""
                    if len(name_list) > 1:
                        last_name = name_list[1]
                    else:
                        last_name = name_list[0]

                    data = json.dumps({
                                          "FullyQualifiedName": customer.name,
                                          "PrimaryEmailAddr": {
                                            "Address": customer.email
                                          },
                                          "DisplayName": customer.name,
                                          # "Suffix": "Jr",
                                          "Title": customer.title.name,
                                          "GivenName": first_name,
                                          "MiddleName": last_name,
                                          "Notes": customer.comment,
                                          # "FamilyName": first_name,
                                          "PrimaryPhone": {
                                            "FreeFormNumber": customer.phone
                                          },
                                          "CompanyName": customer.parent_id.name or '',
                                          "BillAddr": {
                                            "CountrySubDivisionCode": customer.country_id.code,
                                            "City": customer.city or '',
                                            "PostalCode": customer.zip or '',
                                            "Line1": customer.street  or '',
                                            "Country": customer.country_id.code,
                                          },

                                          # "PreferredDeliveryMethod": customer.preferred_delivery_method,
                                          # "BalanceWithJobs": customer.balance_job,
                                          # "PrintOnCheckName": customer.print_on_check_name,
                                          # "Taxable": customer.is_taxable,
                                    })

                    # print "dataaaaaaaaaaaaaaaa",data
                    cust_export_res = qb_client.create_object("Customer", data)
                    if cust_export_res:
                        # print ("cust_export_resssssssssssssssss",cust_export_res.get('Customer').get('Id'))
                        customer.write({'qbook_id': cust_export_res.get('Customer').get('Id'),'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_customer', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)



    # @api.multi
    def exportQbooksVendors(self):
        # print "exportQbooksVendorrrrrrrrr",
        res_partner_obj = self.env['res.partner']
        for rec in self:
            vend_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,

                                    )
            qb_client_vendor = QuickBooks(
                                        session_manager= vend_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            # print "qb_client111111111111",qb_client_vendor

            try:
                if self.env.context.get('export_vend'):
                    # customer_ids = self.env.context.get('export_cust')
                    vendor_ids = res_partner_obj.browse(self.env.context.get('export_vend'))
                    # print "vendor_ids1111111111111111",vendor_ids
                else:
                    # vendor_ids = res_partner_obj.browse(self.env.context.get('active_id'))
                    vendor_ids = res_partner_obj.search([('to_be_exported', '=', True)])
                    # print "vendor_ids2222222222222222",vendor_ids

                # print "vendor_idssssssssssssssss",vendor_ids
                for vendor in vendor_ids:
                    # print "vendorrrrrrrrr",vendor
                    vendor_name = vendor.name
                    name_list = vendor_name.split(' ')
                    first_name = name_list[0]
                    # print ""
                    if len(name_list) > 1:
                        last_name = name_list[1]
                    else:
                        last_name = name_list[0]

                    data_vendor = json.dumps({
                                          "PrimaryEmailAddr": {
                                            "Address": vendor.email
                                          },
                                          "WebAddr": {
                                            "URI": vendor.website
                                          },
                                          "PrimaryPhone": {
                                            "FreeFormNumber": vendor.phone
                                          },
                                          "DisplayName": vendor.name,
                                          "Title": vendor.title.name,
                                          "Mobile": {
                                            "FreeFormNumber":vendor.mobile
                                          },
                                          # "FamilyName": first_name,
                                          "CompanyName": vendor.parent_id.name or '',
                                          # "AcctNum": "35372649",


                                          "FullyQualifiedName": vendor.name,
                                          # "Suffix": "Jr",
                                          "GivenName": first_name,
                                          "MiddleName": last_name,

                                          "BillAddr": {
                                            "CountrySubDivisionCode": vendor.country_id.code,
                                            "City": vendor.city or '',
                                            "PostalCode": vendor.zip or '',
                                            "Line1": vendor.street  or '',
                                            "Line2": vendor.street2  or '',
                                            "Country": vendor.country_id.code,
                                          },
                                          # "PrintOnCheckName": "Dianne's Auto Shop"

                                    })

                    # print "data_vendorrrrrrrrrrrrrrrr",data_vendor
                    vend_export_res = qb_client_vendor.create_object("Vendor", data_vendor)
                    if vend_export_res:
                        # print ("vend_export_resssssssssssssssss",vend_export_res.get('Vendor').get('Id'))
                        vendor.write({'qbook_id': vend_export_res.get('Vendor').get('Id'), 'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_vendor', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def exportQbooksEmployee(self):
        # print "exportQbooksEmployeeeeeeeee",
        # res_partner_obj = self.env['res.partner']
        emp_obj = self.env['hr.employee']

        for rec in self:
            emp_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,

                                    )
            qb_client_employee = QuickBooks(
                                        session_manager= emp_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            # print "qb_client111111111111",qb_client_employee
            try:
                if self.env.context.get('export_emp'):
                    # customer_ids = self.env.context.get('export_cust')
                    employee_ids = emp_obj.browse(self.env.context.get('export_emp'))
                    # print "employee_ids111111111111111",employee_ids
                else:
                    # employee_ids = emp_obj.browse(self.env.context.get('active_id'))
                    employee_ids = emp_obj.search([('to_be_exported', '=', True)])
                    # print "employee_ids2222222222222222",employee_ids

                for employee in employee_ids:
                    emp_name = employee.name
                    name_list = emp_name.split(' ')
                    first_name = name_list[0]
                    if len(name_list) > 1:
                        last_name = name_list[1]
                    else:
                        last_name = name_list[0]

                    data_emp = json.dumps({
                      "GivenName": first_name ,

                      # "SSN": employee.identification_id,

                      "PrimaryAddr": {
                        "CountrySubDivisionCode": employee.country_id.code or False,
                        "City": employee.work_location or False,
                        "PostalCode":  employee.address_id.zip if employee.address_id else False,
                        # "Id": "50",
                        "Line1": employee.address_id.name or False,
                      },
                      "PrimaryPhone": {
                        "FreeFormNumber": employee.work_phone or False,
                      },
                      "FamilyName": last_name,
                    })

                    # print "data_empppppppppppppp",data_emp
                    emp_export_res = qb_client_employee.create_object("Employee", data_emp)
                    if emp_export_res:
                        # print "emp_export_resssssssssssssssss",emp_export_res
                        employee.write({'qbook_id': emp_export_res.get('Employee').get('Id'), 'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_employee', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def exportQbooksDepartment(self):
        # print "exportQbooksDepartment.......",
        emp_obj = self.env['hr.department']

        for rec in self:
            dept_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,

                                    )
            qb_client_department = QuickBooks(
                                        session_manager= dept_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            # print "qb_client111111111111",qb_client_department
            try:
                if self.env.context.get('export_dept'):
                    # customer_ids = self.env.context.get('export_cust')
                    dept_ids = emp_obj.browse(self.env.context.get('export_dept'))
                    # print "dept_ids111111111111111",dept_ids
                else:
                    # dept_ids = emp_obj.browse(self.env.context.get('active_id'))
                    dept_ids = emp_obj.search([('to_be_exported', '=', True)])
                    # print "dept_ids2222222222222222",dept_ids

                for dept in dept_ids:
                    data_dept = json.dumps({
                                              "Name": dept.name or False,
                                              "SubDepartment": dept.sub_department or False,
                                              "FullyQualifiedName":dept.name or False,
                                            })

                    dept_export_res = qb_client_department.create_object("Department", data_dept)
                    if dept_export_res:
                        # print "dept_export_resssssssssssssssss",dept_export_res
                        dept.write({'qbook_id': dept_export_res.get('Department').get('Id'), 'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_department', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def exportQbooksPaymentMethod(self):
        # print "exportQbooksPaymentMethod......."

        payment_method_obj  = self.env['payment.method']
        for rec in self:
            payment_method_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_client_payment_method = QuickBooks(
                                        session_manager= payment_method_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                if self.env.context.get('export_payment_method'):
                    payment_method_ids = payment_method_obj.browse(self.env.context.get('export_payment_method'))
                    # print "payment_method_ids111111111111111",payment_method_ids
                else:
                    # payment_method_ids = payment_method_obj.browse(self.env.context.get('active_id'))
                    payment_method_ids = payment_method_obj.search([('to_be_exported', '=', True)])
                    # print "payment_method_ids2222222222222222",payment_method_ids

                for payment_method in payment_method_ids:

                    data_payment_method = json.dumps({
                                              "Name": payment_method.title or False,
                                              "Type":payment_method.payment_type or False,
                                            })

                    payment_method_export_res = qb_client_payment_method.create_object("PaymentMethod", data_payment_method)

                    if payment_method_export_res:
                        # print "payment_method_export_resssssssssssssssss",payment_method_export_res.get('PaymentMethod').get('Id')
                        payment_method.write({'qbooks_id': payment_method_export_res.get('PaymentMethod').get('Id'), 'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_payment_method', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def exportQbooksCategory(self):
        # print "exportQbooksCattttttttt......."

        # payment_method_obj  = self.env['payment.method']
        categ_obj  = self.env['product.category']

        for rec in self:
            cat_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )

            qb_client_cat = QuickBooks(
                                        session_manager= cat_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                if self.env.context.get('export_cat'):
                    cat_ids = categ_obj.browse(self.env.context.get('export_cat'))
                    # print "cat_ids111111111111111",cat_ids
                else:
                    # cat_ids = categ_obj.browse(self.env.context.get('active_id'))
                    cat_ids = categ_obj.search([('to_be_exported','=',True)])
                    # print "cat_ids2222222222222222",cat_ids

                for categ in cat_ids:

                    data_categ = json.dumps({
                                              "Name": categ.name or False,
                                              "Type": "Category",
                                              "SubItem": True,
                                              "ParentRef":
                                                    {
                                                      "name": categ.parent_id.name or False,
                                                      "value": categ.parent_id.qbook_id or '',
                                                      # "Type": "Category",
                                                    },
                                            })
                    # print "data_categtypeeeeeee",type(data_categ),data_categ


                    categ_export_res = qb_client_cat.create_object("Item", data_categ)

                    if categ_export_res:
                        # print "categ_export_resssssssssssssssss",categ_export_res.get('Item').get('Id')
                        categ.write({'qbook_id': categ_export_res.get('Item').get('Id'),'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_category', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)



    # @api.multi
    def exportQbooksProduct(self):
        # print "exportQbooksProducttttttttt......."

        prod_temp_obj = self.env['product.template']
        prdct_obj = self.env['product.product']
        stock_quanty = self.env['stock.quant']
        # product_obj = self.env['product.product']
        # bundle_obj = self.env['bundle.product']

        for rec in self:
            prod_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )

            qb_client_prod = QuickBooks(
                                        session_manager= prod_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                if self.env.context.get('export_prod'):
                    prod_temp_ids = prod_temp_obj.browse(self.env.context.get('export_prod'))
                    # print "prod_temp_ids111111111111111",prod_temp_ids
                else:
                    # prod_temp_ids = prod_temp_obj.browse(self.env.context.get('active_id'))
                    prod_temp_ids = prod_temp_obj.search([('to_be_exported','=',True)])
                    # print "prod_temp_ids2222222222222222",prod_temp_ids

                for prod in prod_temp_ids:
                    # data_prod = {}
                    p_ids = prdct_obj.search([('product_tmpl_id', '=' ,prod[0].id)])
                    # print "p_idssssssssssssssssssssssss",p_ids
                    qaunt = 0
                    stock = False
                    if p_ids:
                        stck_quant_id = stock_quanty.search([('product_id','=',p_ids[0].id),('location_id','=',self.warehouse_id.lot_stock_id.id)])
                        # print "stck_quant_iddddddddd",stck_quant_id
                        for stock in stck_quant_id:
                            qaunt += stock.quantity
                    # print "STOCKKKKKKKKKKKKK",stock

                    date_today = date.today()
                    # print "ddd111111111111111",date_today,type(date_today)
                    if isinstance(date_today, (datetime.date, date)):
                       date_today = date_today.isoformat()
                       # print "ddd333333333333",date_today,type(date_today)

                    inv_type_ids = self.env['account.account'].search([('name','=','Inventory Asset'),('qbooks_id','!=',False)])
                    # print "inv_type_idsssssssssssssss",inv_type_ids

                    # data_prod = json.dumps({
                    data_prod = {
                                    "Name": prod.name,
                                    "IncomeAccountRef": {
                                            "name": prod.property_account_income_id.name,
                                            "value": prod.property_account_income_id.qbooks_id,
                                          },

                                    "UnitPrice": prod.list_price,
                                    "PurchaseCost": prod.standard_price,
                                    "Active": True,
                                    "Sku":prod.default_code,
                                }
    # employee.address_id.zip if employee.address_id else False,
                    # print "data_proddddddddd",data_prod
                    if prod.type == 'product':
                        data_prod.update({
                                            "QtyOnHand": int(qaunt),
                                            "InvStartDate": stock.in_date if stock else date_today,
                                            "Type": "Inventory",
                                            "TrackQtyOnHand": True,
                                            "AssetAccountRef": {
                                                "name": inv_type_ids.name,
                                                "value": inv_type_ids.qbooks_id,
                                              },
                                            "ExpenseAccountRef": {
                                                "name": prod.property_account_expense_id.name,
                                                "value": prod.property_account_expense_id.qbooks_id,
                                              },
                                        })
                        # print "data_proddddddddd",data_prod
                    elif prod.type == 'consu':
                        data_prod.update({
                                            "Type": "NonInventory",
                                        })

                    else:
                        data_prod.update({
                                            "Type": "Service",
                                        })
                    # print "data_proddddddddd2222222222222",data_prod
                    data_prod = json.dumps(data_prod)
                    # print "data_proddddddddd333333",type(data_prod)
                    prod_export_res = qb_client_prod.create_object("Item", data_prod)
                    if prod_export_res:
                        # print "prod_export_resssssssssssssssss",prod_export_res.get('Item').get('Id')
                        prod.write({'qbooks_id': prod_export_res.get('Item').get('Id'),'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_product', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)



    # @api.multi
    # def exportQbooksProductBundle(self):
    #     print "exportQbooksProducttttttttt......."

    #     prod_temp_obj = self.env['product.template']
    #     prod_prod_obj = self.env['product.product']
    #     stock_quanty = self.env['stock.quant']
    #     # product_obj = self.env['product.product']
    #     # bundle_obj = self.env['bundle.product']

    #     for rec in self:
    #         prod_bundle_session_manager = Oauth2SessionManager(
    #                                     sandbox=True,
    #                                     client_id=rec.client_id,
    #                                     client_secret=rec.client_secret,
    #                                     # base_url=rec.base_url,
    #                                     access_token=rec.access_token,
    #                                 )

    #         qb_client_prod_bundle = QuickBooks(
    #                                     session_manager= prod_bundle_session_manager,
    #                                     sandbox=True,
    #                                     company_id= rec.company_id,
    #                                     minorversion=4,
    #                                 )

    #         if self.env.context.get('export_prod_bndl'):
    #             prod_bundle_ids = prod_prod_obj.browse(self.env.context.get('export_prod_bndl'))
    #             print "prod_bundle_ids111111111111111",prod_bundle_ids
    #         else:
    #             prod_bundle_ids = prod_prod_obj.search([('bundle_product', '=', True)])
    #             print "prod_bundle_ids2222222222222222",prod_bundle_ids

    #         for product in prod_bundle_ids:
    #             if not product.bundle_product:
    #                 raise UserError(_("Sorry You Can Only Export The Bundle Product Form Here."))
    #             else:
    #                 data_prod = {
    #                             "Name": product.name,
    #                             "UnitPrice": product.list_price,
    #                             "PurchaseCost": product.standard_price,
    #                             "Active": True,
    #                             "Sku":product.default_code,
    #                             "Type": "Group",
    #                             "TrackQtyOnHand": False,
    #                         }

    #                 data_prod = json.dumps(data_prod)
    #                 prod_bundle_export_res = qb_client_prod_bundle.create_object("Item", data_prod)
    #                 if prod_bundle_export_res:
    #                     product.write({'qbooks_id': prod_bundle_export_res.get('Item').get('Id')})




    # @api.multi
    def exportQbooksOrder(self):
        # print "exportQbooksOrderrrrrrrrrr......."
        sale_order_obj = self.env['sale.order']

        for rec in self:
            order_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )

            qb_client_order = QuickBooks(
                                        session_manager= order_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                if self.env.context.get('export_order'):
                    sale_ids = sale_order_obj.browse(self.env.context.get('export_order'))
                    # print "sale_ids111111111111111",sale_ids
                else:
                    # sale_ids = sale_order_obj.browse(self.env.context.get('active_id'))
                    sale_ids = sale_order_obj.search([('to_be_exported','=',True)])
                    # print "sale_ids2222222222222222",sale_ids


                for sale_id in sale_ids:

                    data_order = {}
                    if sale_id.order_line:
                        # print ("IIIIIIFFFFFFFFFFFF")
                        Line = []
                        for line in sale_id.order_line:
                            # print "lineidddddddddddddd",line.product_id
                            if line.product_id.bundle_product == True:
                                # print "bbbbbbbbbbbbbbbbbbbbbbb"
                                product = line.product_id.product_tmpl_id
                                Line.append({
                                              "Description": product.name,
                                              "DetailType": "GroupLineDetail",
                                              "GroupLineDetail": {
                                                "Quantity": line.product_uom_qty,
                                                # "UnitPrice": product.list_price,
                                                "GroupItemRef": {
                                                  "name": product.name,
                                                  "value": product.qbooks_id,
                                                }
                                              },
                                              # "LineNum": 1,
                                              "Amount": product.list_price,
                                              # "Id": "1"
                                            })
                            else:
                                # print "pppppppppppppppppppppppp"
                                product = line.product_id.product_tmpl_id
                                # print "productttttttttttttttttt",product
                                Line.append({
                                              "Description": product.name,
                                              "DetailType": "SalesItemLineDetail",
                                              "SalesItemLineDetail": {
                                                "Qty": line.product_uom_qty,
                                                "UnitPrice": product.list_price,
                                                "ItemRef": {
                                                  "name": product.name,
                                                  "value": product.qbooks_id,
                                                }
                                              },
                                              # "LineNum": 1,
                                              "Amount": product.list_price * line.product_uom_qty,
                                              # "Id": "1"
                                            })
                            # print "LINEEEEEEEEEEEEEEEEEEEEE",Line
                    else:
                        raise UserError(_("Please Enter Products In The Order Line To Export The Order."))

                    data_order = json.dumps({
                    # {
                      "DocNumber": sale_id.name,
                      # "SyncToken": "0",
                      # "domain": "QBO",

                      # "Balance": 0,
                      "PaymentMethodRef": {
                        "name": sale_id.payment_method.title,
                        "value": sale_id.payment_method.qbooks_id,
                      },
                      "BillAddr": {
                        "Line1": sale_id.partner_id.street,
                      },
                      # "DepositToAccountRef": {
                      #   "name": "Checking",
                      #   "value": "35"
                      # },
                      "TxnDate": sale_id.confirmation_date.strftime('%m/%d/%Y'),
                      "TotalAmt": sale_id.amount_total,
                      "CustomerRef": {
                        "name": sale_id.partner_id.name,
                        "value": sale_id.partner_id.qbook_id,
                      },
                      # "CustomerMemo": {
                      #   "value": "An updated customer memo."
                      # },
                      # "PrintStatus": "NotSet",
                      # "PaymentRefNum": "10264",
                      # "EmailStatus": "NotSet",
                      # "sparse": false,
                      "Line": Line,

                      # "ApplyTaxAfterDiscount": false,
                      # "CustomField": [
                      #   {
                      #     "DefinitionId": "1",
                      #     "Type": "StringType",
                      #     "Name": "Crew #"
                      #   }
                      # ],

                      # "TxnTaxDetail": {
                      #   "TotalTax": 0
                      # },
                      # "MetaData": {
                      #   "CreateTime": "2014-09-16T14:59:48-07:00",
                      #   "LastUpdatedTime": "2014-09-16T14:59:48-07:00"
                      # }
                    # }
                    })
                    # print "data_ordereeeeeeeeeeeeeeeeeeeeee",data_order

                    order_export_res = qb_client_order.create_object("SalesReceipt", data_order)

                    if order_export_res :
                        # print "order_export_resssssssssssssssss",order_export_res
                        sale_id.write({'qbook_id': order_export_res.get('SalesReceipt').get('Id'), 'to_be_exported': False})

            except Exception as e:
                # print "eeeeeeeeeeeeeeeeeee",e
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_sale_orders', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)



    # @api.multi
    def exportQbooksPurchaseOrder(self):
        # print "EEEE_PUrchase.........."

        purchase_order_obj  = self.env['purchase.order']

        for rec in self:
            purchase_order_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )

            qb_client_purchase_order = QuickBooks(
                                        session_manager= purchase_order_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                if self.env.context.get('export_purchase_order'):
                    purchase_ids = purchase_order_obj.browse(self.env.context.get('export_purchase_order'))
                    # print "purchase_ids111111111111111",purchase_ids
                else:
                    # purchase_ids = purchase_order_obj.browse(self.env.context.get('active_id'))
                    purchase_ids = purchase_order_obj.search([('to_be_exported','=',True)])
                    # print "purchase_ids2222222222222222",purchase_ids

                for purchase_id in purchase_ids:
                    data_purchase_order = {}
                    if purchase_id.order_line:
                        Line = []
                        for line in purchase_id.order_line:
                            product = line.product_id.product_tmpl_id
                            Line.append({
                                          "Description": product.name,
                                          "DetailType": "ItemBasedExpenseLineDetail",
                                          "ItemBasedExpenseLineDetail":
                                                {
                                                    "Qty": line.product_qty,
                                                    "UnitPrice": line.price_unit,
                                                    "ItemRef": {
                                                      "name": product.name,
                                                      "value": product.qbooks_id,
                                                    },
                                                    "CustomerRef": {
                                                        "name": line.line_customer.name or '',
                                                        "value": line.line_customer.qbook_id or '',
                                                    },
                                                },
                                          "Amount": line.price_unit * line.product_qty,
                                        })

                    else:
                        raise UserError(_("Please Enter Products In The Order Line To Export The Purchase Order."))


                    data_purchase_order = json.dumps({
                      "DocNumber": purchase_id.name,

                      "VendorAddr": {
                        "Line1": purchase_id.partner_id.street,
                        "Line2": purchase_id.partner_id.street2,
                      },
                      "TxnDate": purchase_id.date_order,
                      "TotalAmt": purchase_id.amount_total,
                      "VendorRef": {
                        "name": purchase_id.partner_id.name,
                        "value": purchase_id.partner_id.qbook_id,
                      },
                      "Line": Line,
                    })
                    # print "data_purchase_ordereeeeeeeeeeeeeeeeeeeeee",data_purchase_order

                    order_export_res = qb_client_purchase_order.create_object("PurchaseOrder", data_purchase_order)

                    if order_export_res :
                        # print "order_export_resssssssssssssssss",order_export_res
                        purchase_id.write({'qbook_id': order_export_res.get('PurchaseOrder').get('Id'), 'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_purchase_orders', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def exportQbooksInvoice(self):
        # print "Invoiceeeeeeee.........."

        # purchase_order_obj  = self.env['purchase.order']
        inv_obj  = self.env['account.move']

        for rec in self:
            purchase_order_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )

            qb_client_invoice = QuickBooks(
                                        session_manager= purchase_order_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                if self.env.context.get('export_invoice'):
                    invoice_ids = inv_obj.browse(self.env.context.get('export_invoice'))
                    # print "invoice_ids111111111111111",invoice_ids
                else:
                    # invoice_ids = inv_obj.browse(self.env.context.get('active_id'))
                    invoice_ids = inv_obj.search([('to_be_exported','=',True)])
                    # print "invoice_ids2222222222222222",invoice_ids

                for invoice in invoice_ids:
                    if invoice.invoice_line_ids:
                        Line = []
                        for line in invoice.invoice_line_ids:
                            if line.product_id.bundle_product == True:
                                # print "bbbbbbbbbbbbbbbbbbbbbbb"
                                # continue
                                product = line.product_id.product_tmpl_id
                                Line.append({
                                              "DetailType": "GroupLineDetail",
                                              "Amount": line.price_unit * line.quantity,
                                              "GroupLineDetail": {
                                                "Quantity": line.quantity,
                                                # "UnitPrice": product.list_price,
                                                "GroupItemRef": {
                                                  "name": product.name,
                                                  "value": product.qbooks_id,
                                                }
                                              },

                                            })

                            else:
                                # print "ppppppppppppppppppppp"
                                product = line.product_id.product_tmpl_id
                                Line.append({
                                              "DetailType": "SalesItemLineDetail",
                                              "Amount": line.price_unit * line.quantity,
                                              "SalesItemLineDetail":
                                                    {
                                                        "Qty": line.quantity,
                                                        "UnitPrice": line.price_unit,
                                                        "ItemRef": {
                                                          "name": product.name,
                                                          "value": product.qbooks_id,
                                                        },
                                                    },
                                            })
                    else:
                        raise UserError(_("Please Enter Products In The Invoice Line To Export The Invoice"))

                    data_invoice = json.dumps({
                      "DocNumber": invoice.number,
                      "CustomerRef": {
                                      "name": invoice.partner_id.name,
                                      "value": invoice.partner_id.qbook_id,
                                    },
                      "ShipAddr": {
                                  "City": invoice.partner_id.city or False,
                                  "Line1": invoice.partner_id.street or False,
                                  "PostalCode": invoice.partner_id.zip or False,
                                  "CountrySubDivisionCode": invoice.partner_id.country_id.code or False,
                                },
                      "TxnDate": invoice.date_invoice,
                      "TotalAmt": invoice.amount_total,
                      "DueDate": invoice.date_due,

                      "Line": Line,
                    })
                    # print "data_invoiceeeeeeeeeeeeeeeeeeeeeee",data_invoice

                    invoice_export_res = qb_client_invoice.create_object("Invoice", data_invoice)

                    if invoice_export_res :
                        # print "invoice_export_resssssssssssssssss",invoice_export_res
                        invoice.write({'qbook_id': invoice_export_res.get('Invoice').get('Id'), 'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_invoice', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)


    # @api.multi
    def exportQbooksAccount(self):
        # print "aaaaaaacccccccchhhhhhh.........."
        inv_obj = self.env['account.account']

        for rec in self:
            ch_acc_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )

            qb_client_ch_acc = QuickBooks(
                                        session_manager= ch_acc_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                if self.env.context.get('export_chh_acc'):
                    chh_acc_ids = inv_obj.browse(self.env.context.get('export_chh_acc'))
                    # print "chh_acc_ids111111111111111",chh_acc_ids
                else:
                    # chh_acc_ids = inv_obj.browse(self.env.context.get('active_id'))
                    chh_acc_ids = inv_obj.search([('to_be_exported', '=', True)])
                    # print "chh_acc_ids2222222222222222",chh_acc_ids

                for chh_acc_id in chh_acc_ids:

                    if chh_acc_id.user_type_id.name == 'Bank and Cash':
                        acc_type = 'Bank'

                    if chh_acc_id.user_type_id.name == 'Income' or chh_acc_id.user_type_id.name == 'Other Income':
                        acc_type = 'Income'

                    if chh_acc_id.user_type_id.name == 'Expenses':
                        acc_type = 'Expense'

                    if chh_acc_id.user_type_id.name == 'Fixed Assets':
                        acc_type = 'Fixed Asset'

                    if chh_acc_id.user_type_id.name == 'Equity':
                        acc_type = 'Equity'

                    if chh_acc_id.user_type_id.name == 'Credit Card':
                        acc_type = 'Credit Card'

                    if chh_acc_id.user_type_id.name == 'Cost of Revenue':
                         acc_type = 'Cost of Goods Sold'

                    if chh_acc_id.user_type_id.name == 'Receivable':
                        acc_type = 'Accounts Receivable'

                    if chh_acc_id.user_type_id.name == 'Payable':
                        acc_type = 'Accounts Payable'

                    if chh_acc_id.user_type_id.name == 'Current Assets':
                        acc_type = 'Other Current Asset'

                    if chh_acc_id.user_type_id.name == 'Non-current Assets':
                        acc_type = 'Other Asset'

                    if chh_acc_id.user_type_id.name == 'Current Liabilities':
                        acc_type = 'Other Current Liability'

                    if chh_acc_id.user_type_id.name == 'Non-current Liabilities':
                        acc_type = 'Long Term Liability'

                    if chh_acc_id.user_type_id.name == 'Prepayments':
                        # acc_type = ''
                        continue

                    if chh_acc_id.user_type_id.name == 'Depreciation':
                        # acc_type = ''
                        continue

                    if chh_acc_id.user_type_id.name == 'Current Year Earnings':
                        # acc_type = ''
                        continue

                    acc_vals = json.dumps({
                        'Name': chh_acc_id.name,
                        # 'qbooks_id': query_account.Id,
                        # 'code':query_account.Id,
                        'AccountType':acc_type,
                        })
                    # print "accccchhh_valssssssssss",acc_vals
                    ch_acc_export_res = qb_client_ch_acc.create_object("Account", acc_vals)

                    if ch_acc_export_res :
                        # print "ch_acc_export_resssssssssssssssss",ch_acc_export_res
                        chh_acc_id.write({'qbooks_id': ch_acc_export_res.get('Account').get('Id'),'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_account', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)

    # @api.multi
    def exportQbooksTax(self):
        # print "aaaaaaacccccccchhhhhhh.........."
        tax_obj = self.env['account.tax']

        for rec in self:
            ch_acc_session_manager = Oauth2SessionManager(
                                        sandbox=True,
                                        client_id=rec.client_id,
                                        client_secret=rec.client_secret,
                                        # base_url=rec.base_url,
                                        access_token=rec.access_token,
                                    )
            qb_client_tax = QuickBooks(
                                        session_manager= ch_acc_session_manager,
                                        sandbox=True,
                                        company_id= rec.company_id,
                                        minorversion=4,
                                    )
            try:
                if self.env.context.get('export_tax'):
                    tax_ids = tax_obj.browse(self.env.context.get('export_tax'))
                    # print "export_tax11111111111111",tax_ids
                else:
                    # tax_ids = tax_obj.browse(self.env.context.get('active_id'))
                    tax_ids = tax_obj.search([('to_be_exported', '=', True)])
                    # print "export_tax2222222222222222",tax_ids

                line =[]
                for tax_id in tax_ids:
                    if tax_id.amount_type == 'group':
                        # print "iffffffffffffffff"
                        total_tax = sum(rec.amount for rec in tax_id.children_tax_ids)
                        line.append({
                          "RateValue": total_tax,
                          # "TaxApplicableOn": "Sales",
                          "TaxAgencyId": tax_id.account_agency.qbook_id,
                          "TaxRateName":tax_id.name,
                        })
                    else:
                        # print "elseeeeeeeeeeeeeee"
                        line.append({
                         "RateValue": tax_id.amount,
                          # "TaxApplicableOn": "Sales",
                          "TaxAgencyId": tax_id.account_agency.id,
                          "TaxRateName":tax_id.name,
                        })

                    tax_vals = json.dumps({
                        'TaxCode': tax_id.name,
                        'TaxRateDetails':line,
                        })

                    # print "taxxxxxxxsssssssss",tax_vals
                    tax_export_res = qb_client_tax.create_object("TaxService/Taxcode", tax_vals)

                    if tax_export_res :
                        # print "tax_export_resssssssssssssssss",tax_export_res
                        tax_id.write({'qbook_id': tax_export_res.get('TaxCodeId'), 'to_be_exported': False})

            except Exception as e:
                if self.env.context.get('log_id'):
                    log_id = self.env.context.get('log_id')
                    self.env['log.error'].create({'log_description': str(e), 'log_id': log_id})
                else:
                    log_id = self.env['qbook.log'].create({'all_operations':'export_tax', 'error_lines': [(0, 0, {'log_description': str(e)})]})
                    self = self.with_context(log_id=log_id.id)
