# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Odoo Quickbook online Connector",
    "version" : "1.0",
    "author" : "Globalteckz",
    "category" : "Sales",
    "license" : "Other proprietary",
    'images': ['static/description/banner.png'],
    "price": "99.00",
    "currency": "USD",
    "depends" : ['base','account','sale','stock','purchase','hr','gt_bundle_product'],
    "summary":"Odoo quickbook online connector will help to import / export data between odoo and quickbooks Odoo QuickBooks Bundle Odoo Quickbooks Desktop Connector Odoo Quickbooks integration QuickBooks Credit Memo Quickbooks reports odoo quickbooks connect accounting app accounting reports QuickBook Online connector online odoo accounting app Synchronise data between Odoo and Quickbooks Desktop Quickbooks Odoo Quickbooks Odoo connector odoo quickbooks integration ",
    "description": """
    Odoo quickbook online connector will help to import / export data between odoo and quickbooks """,
    "data": [
      'data/product_data.xml',
      'data/schedualr_data.xml',
      # 'data/qbook_sequence_data.xml',
      'security/ir.model.access.csv',

      'views/quickbook_integration.xml',
      'wizard/quickbooks_connector_wizard_view.xml',
      'wizard/qbook_export_customer_view.xml',
      'wizard/qbook_export_employee_view.xml',
      'wizard/qbook_export_department_view.xml',
      'wizard/qbook_export_payment_method_view.xml',
      'wizard/qbook_export_category.xml',
      'wizard/qbook_export_product.xml',
      # 'wizard/qbook_export_product bundle.xml',
      'wizard/qbook_export_order.xml',
      'wizard/qbook_export_purchase_order.xml',
      'wizard/qbook_export_invoice.xml',
      'wizard/qbook_export_chart_of_account.xml',
      'wizard/qbook_export_tax.xml',

      'views/res_partner_view.xml',
      'views/employee_view.xml',
      'views/payment_method_view.xml',
      'views/payment_term.xml',
      'views/department.xml',
      'views/category_view.xml',
      'views/product_view.xml',
      'views/chart_of_account.xml',
      'views/sale_order_view.xml',
      'views/invoice.xml',
      'views/purchase_order_view.xml',

      'views/dashboard_qbooks_view.xml',
      'views/Qbook_log_view.xml',

      'views/quickbook_menu.xml',


    ],
    "installable": True,
    "active": True,
}
