# -*- coding: utf-8 -*-
{
    'name': "qubee_stock_handlling",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'product', 'account', 'purchase', 'stock'],



    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_product.xml',
        'views/sale_order_line.xml',
        'views/purchase_order.xml',
        'views/account_move.xml',
        'views/stock_picking.xml',
        'views/packs_form.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
