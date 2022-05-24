# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2013-Today Globalteckz (http://www.globalteckz.com)
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
    'name': "Odoo Product Pack (Bundle) or Combo Products",
    'summary': """App website product pack website product kit pos product bundle pos product pack  website product combo pos bundle product bundle product pack kit all in one product bundle pack all in one bundle product pack shop product pack ecommerce product bundle pack Combine two or more product pack product kit product bundle product pack item on product combo product on sale bundle product delivery bundle product pack kit combine product combine product variant bundle item pack sales bundle delivery pack bundle""",
    'description': """
Odoo Product Pack Module or Combo Product module helps you to combine several products together with special      pricing. Bundle products or Product Pack helps you to enhance sales with special discounts.
combo product
bundle product
product pack
Product bundle pack
bundle pack
Product Pack (Bundle) or Combo Products
product pack
product bundle
product combo
combo products
combo product
combo pack
combo
product bundle
""",

    'author': "Globalteckz",
    'website': "http://www.globalteckz.com",
    "license" : "Other proprietary",
    'images': ['static/description/Banner.png'],
    "price": "40.00",
    "currency": "USD",
    'category': 'Sales',
    'version': '1.0',
    'depends': ['base',"product","sale","stock","sale_management"],
    'data': [
        'security/ir.model.access.csv',
        'views/bundle_product_view.xml',

    ],
    'qweb': [],
}
