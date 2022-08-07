# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import base64
import xlrd
import xlwt
from datetime import datetime
from dateutil import parser
from odoo.tests import Form, tagged
import pytz
utc = pytz.utc
import json
import logging
_logger = logging.getLogger(__name__)


class ExcelReport(models.Model):
    _name = 'excel.report'

    xls_file = fields.Binary('file')
    report_for = fields.Selection([('create_xls_file', 'create_xls_file'),('invoice', 'Invoice'), ('old_invoice_date_update', 'Profit and Lose Updation'), ('validate_sale_order_unpaid_shipped', 'Validate Sale Order Unpaid Shipped'), ('product', 'Product'), ('product_cost', 'Product Cost'), ('product_forcast', 'Product Forcast'), ('check_true', 'Check True'), ('compare_onhand_stock', 'Compare onhand Stock'), ('compare_forcast_stock', 'Compare forcast Stock'), ('check_false', 'Check False'), ('product_stock', 'Product Stock'), ('pack_price', 'Pack Price'), ('price_list', 'Price List'), ('validate_sale_order', 'Validate Sale Order'), ('sale_order', 'Sale Order'), ('purchase_order', 'Purchase Order'), ('customer', 'Customer')])
    order_name = fields.Char()

    def create_transfer(self):
        pass

        # # # # # # # # # # # # #

        # name_list = []
        # sale_orders = self.env['sale.order'].search([('date_order', '>=', '01/07/2022'), ('date_order', '<=', '31/07/2022')])
        # i = 0
        # for sale in sale_orders:
        #     if sale.sale_api_data and sale.state != 'cancel':
        #         payload = json.loads(sale.sale_api_data)
        #         payload_payment = payload.get("financial_status")
        #         payload_delivery = payload.get("fulfillment_status")
        #         payload_restock = payload.get("restock")
        #         payload_refund = payload.get('refunds')
        #         invoice = sale.invoice_ids.filtered(
        #             lambda r: r.move_type == 'out_invoice' and r.state == 'posted' and r.amount_residual == 0)
        #         refund = sale.invoice_ids.filtered(
        #             lambda r: r.move_type == 'out_refund' and r.state == 'posted' and r.amount_residual == 0)
        #         delivry_partial = sale.picking_ids.filtered(lambda p: p.state != 'done')
        #         delivry_full = sale.picking_ids.filtered(lambda p: p.state == 'done')
        #         if payload_delivery == 'fulfilled' and len(delivry_partial):
        #             name_list.append(sale.name)
        #         elif len(payload_refund) and not refund:
        #             name_list.append(sale.name)
        #         elif payload_payment == 'paid' and not invoice:
        #             name_list.append(sale.name)
        #         elif payload_restock and not len(sale.moves_count):
        #             name_list.append(sale.name)
        # print(name_list)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

            # if a != b:
            #     i +=1
                # print('count ' + str(i) + "  " + str(invoice.invoice_date) + "     " + str(invoice.invoice_date_due))
            # if i > 80:
            #     print()
                # print()
                # print()
                # print()
            # if invoice.invoice_date:
            #     in_1_31 = invoice.invoice_date <= datetime. strptime("31/07/22", '%d/%m/%y').date() and invoice.invoice_date >= datetime. strptime("01/07/22", '%d/%m/%y').date()
            #
            # if not invoice.invoice_date:
            #     # name_list.append([invoice.name,invoice.invoice_origin])
            #     continue
            #
            # elif not in_1_31:
            #     name_list.append([invoice.name,invoice.invoice_origin])
        #
        # print(name_list)
        # z = 0
        # workbook = xlwt.Workbook()
        # sheetwt = workbook.add_sheet('test')
        # sheetwt.write(0, 0, 'invoice name')
        # sheetwt.write(0, 1, 'sale order number')
        # roww = 1
        # for x in name_list:
        #     sheetwt.write(roww, 0, x[0])
        #     sheetwt.write(roww, 1, x[1])
        #     roww += 1
        #     z += 1
        # workbook.save('/home/hafiz/sale_orders_qb/draft_order/invoices_no_4.xls')

        # products = self.env['product.product'].search([])
        # stock_picking_obj = self.env['stock.picking']
        # picking = stock_picking_obj.create({
        #     'name': 'Cake Delivery Order 2.1',
        #     'partner_id': 1,
        #     'picking_type_id': self.env.ref('stock.picking_type_out').id,
        #     'location_id': 27,
        #     'location_dest_id': self.env.ref("stock.stock_location_stock").id,
        # })
        # for product in products:
        #     customer_location = product.stock_quant_ids.filtered(lambda inv: inv.location_id.id == 27)
        #     bom_ids = product.bom_ids.filtered(lambda l: l.product_id.id == product.id)
        #     if customer_location and not bom_ids:
        #         self.env['stock.move'].create({
        #             "name": product.name,
        #             'product_id': product.id,
        #             'product_uom_qty': customer_location.quantity,
        #             'product_uom': product.uom_id.id,
        #             'quantity_done': customer_location.quantity,
        #             'location_id': 27,
        #             'location_dest_id': self.env.ref("stock.stock_location_stock").id,
        #             'picking_id': picking.id,
        #
        #         })


    def import_xls(self):
        main_list = []
        wb = xlrd.open_workbook(file_contents=base64.decodestring(self.xls_file))
        if self.report_for == "customer":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            i = 0
            for inner_list in main_list:
                try:
                    customer = self.env['res.partner'].search([('employee_id', '=', inner_list[0])])
                    if not customer:
                        state_name = self.env['res.country.state'].search([('name', '=', str(inner_list[29]))]).id
                        country_name = self.env['res.country'].search([('name', '=', str(inner_list[30]))]).id

                        if not country_name:
                            country_name = inner_list[30]
                            country_name = self.env['res.country'].create({
                                'name': country_name
                            })
                            country_name = country_name.id
                        # if not state_name:
                        #     state_name = inner_list[29]
                        #     state_name = self.env['res.country.state'].create({
                        #         'name': state_name,
                        #         'country_id': country_name,
                        #         'code': inner_list[31],
                        #     })
                        #     state_name = state_name.id

                        self.env['res.partner'].create({
                            'name': inner_list[1],
                            'employee_id': inner_list[0],
                            'email': inner_list[2],
                            'website': str(inner_list[3]),
                            'company_typeee': inner_list[5],
                            'phone': str(inner_list[6]),
                            'description': inner_list[9],
                            'comment': inner_list[10],
                            'mobile': str(inner_list[15]),
                            'b2b': inner_list[21],
                            'street': str(inner_list[25]),
                            'street2': str(inner_list[26]),
                            'city': str(inner_list[28]),
                            # 'state_id': state_name,
                            'country_id': country_name,
                        })
                        i += 1
                        if (int(i % 500) == 0):
                            print("Record created_________________" + str(i) + "\n")
                except(Exception) as error:
                    print('Error occur at %s' %(str(inner_list[0])))

        elif self.report_for == "old_invoice_date_update":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)

            i = 0
            for nam in main_list:
                try:
                    print(str(i) + "   " + nam[0])
                    i += 1
                    acc = self.env['account.move'].search([('name', '=', nam[0])])
                    if not acc:
                        continue
                    if acc.name == acc.name[:4] + str(acc.invoice_date)[:4] + '/' + str(acc.invoice_date)[
                                                                                    5:7] + acc.name[
                                                                                           11:] and acc.date == acc.invoice_date:
                        continue
                    acc.write({'name': acc.name[:4] + str(acc.invoice_date)[:4] + '/' + str(acc.invoice_date)[
                                                                                        5:7] + acc.name[11:],
                               'date': acc.invoice_date})
                    # acc.name = acc.name[:4]+str(acc.invoice_date)[:4]+'/'+str(acc.invoice_date)[5:7]+acc.name[11:]
                    acc._onchange_invoice_date()
                    if (int(i % 500) == 0):
                        _logger.info("Record created___" + str(i) + '  Order___ ' + str(nam[0]))
                        print("Record created___" + str(i) + '  Order___ ' + str(nam[0]))
                        acc._cr.commit()
                except(Exception) as error:
                    print('Error occur at %s' % (str(nam[0])))
                    _logger.info('Error occur at %s' % (str(nam[0])))


        elif self.report_for == "price_list":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            for inner_list in main_list:
                product_varient = self.env['product.product'].search([('default_code', '=', inner_list[16])], limit=1)
                if product_varient:
                    self.env['product.pricelist.item'].create({
                        "applied_on": "0_product_variant",
                        "product_id": product_varient.id,
                        "product_tmpl_id": product_varient.product_tmpl_id.id,
                        "min_quantity": 1,
                        "fixed_price": 0 if inner_list[38] == "" else float(inner_list[38]),
                        "pricelist_id": self.env['product.pricelist'].search([('price_check_box', '=', True)], limit=1).id,
                    })
            print("price add hogai hy")
        elif self.report_for == "product_cost":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            for inner_list in main_list:
                product_varient = self.env['product.product'].search([('default_code', '=', inner_list[2])], limit=1)
                if product_varient:
                    product_varient.standard_price = 0 if inner_list[6] == '' else float(inner_list[6])
            print("cost add hogai hy")

        elif self.report_for == "check_true":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            for inner_list in main_list:
                product_varient = self.env['product.product'].search([('default_code', '=', inner_list[16])], limit=1)
                if product_varient:
                    product_varient.product_tmpl_id.temp_checkbox = True
        elif self.report_for == "check_false":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            for inner_list in main_list:
                product_varient = self.env['product.product'].search([('default_code', '=', inner_list[16])], limit=1)
                if product_varient:
                    product_varient.product_tmpl_id.temp_checkbox = False

        elif self.report_for == "compare_onhand_stock":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            for inner_list in main_list:
                product_varient = self.env['product.product'].search([('default_code', '=', inner_list[16])], limit=1)
                is_bom = product_varient.bom_ids.filtered(lambda l: l.product_id.id == product_varient.id)
                if is_bom:
                    continue
                if product_varient:
                    if str(inner_list[29]) == '-':
                        if product_varient.qty_available != 0:
                            product_varient.stock_onhand_not_match = True

                    elif product_varient.qty_available != float(inner_list[29]):
                        product_varient.stock_onhand_not_match = True

                    else:
                        product_varient.stock_onhand_not_match = False


        elif self.report_for == "compare_forcast_stock":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            list = []
            for inner_list in main_list:
                product_varient = self.env['product.product'].search([('default_code', '=', inner_list[16])], limit=1)
                is_bom = product_varient.bom_ids.filtered(lambda l: l.product_id.id == product_varient.id)
                if is_bom:
                    continue
                if product_varient:
                    if inner_list[31] == '-':
                        if product_varient.virtual_available != 0:
                            product_varient.stock_forcast_not_match = True
                            list.append(product_varient.default_code)
                    elif product_varient.virtual_available != float(inner_list[31]):
                        product_varient.stock_forcast_not_match = True
                        list.append(product_varient.default_code)

                    else:
                        product_varient.stock_forcast_not_match = False
            print(list)

        elif self.report_for == "product_forcast":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)

            sale = self.env['sale.order'].create({'partner_id': 2})
            purchase = self.env['purchase.order'].create({'partner_id': 2})
            for inner_list in main_list:
                product_varient = self.env['product.product'].search([('default_code', '=', inner_list[16])], limit=1)
                is_bom = product_varient.bom_ids.filtered(lambda l: l.product_id.id == product_varient.id)
                if is_bom:
                    continue
                if product_varient.default_code == 'POSX14x8':
                    print('assaasdasdadsdsd')
                if str(inner_list[30]) == '-':
                    if product_varient.virtual_available < 0:
                        self.env['purchase.order.line'].create({
                                'product_id': product_varient.id,
                                'product_qty': -1 * product_varient.virtual_available,
                                'product_uom': product_varient.uom_id.id,
                                'order_id': purchase.id,
                            })
                    if product_varient.virtual_available > 0:
                        self.env['sale.order.line'].create({
                            'product_id': product_varient.id,
                            'product_uom_qty': product_varient.virtual_available,
                            'product_uom': product_varient.uom_id.id,
                            'order_id': sale.id,
                        })
                elif int(inner_list[31]) == 0 and product_varient.virtual_available != 0:
                    if product_varient.virtual_available < 0:
                        self.env['purchase.order.line'].create({
                                'product_id': product_varient.id,
                                'product_qty': -1 * product_varient.virtual_available,
                                'product_uom': product_varient.uom_id.id,
                                'order_id': purchase.id,
                            })
                    if product_varient.virtual_available > 0:
                        self.env['sale.order.line'].create({
                            'product_id': product_varient.id,
                            'product_uom_qty': product_varient.virtual_available,
                            'product_uom': product_varient.uom_id.id,
                            'order_id': sale.id,
                        })
                elif product_varient.virtual_available > inner_list[31]:
                    self.env['sale.order.line'].create({
                        'product_id': product_varient.id,
                        'product_uom_qty': product_varient.virtual_available - inner_list[31],
                        'product_uom': product_varient.uom_id.id,
                        'order_id': sale.id,
                    })

                elif product_varient.virtual_available < inner_list[31]:
                    self.env['purchase.order.line'].create({
                        'product_id': product_varient.id,
                        'product_qty': inner_list[31] - product_varient.virtual_available,
                        'product_uom': product_varient.uom_id.id,
                        'order_id': purchase.id,
                    })







        elif self.report_for == "product_stock":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            for inner_list in main_list:
                product_varient = self.env['product.product'].search([('default_code', '=', inner_list[16])], limit=1)
                # product_varient.product_tmpl_id.temp_checkbox = True
                if product_varient.default_code == 'TBCH30':
                    print('sadasd')
                is_bom = product_varient.bom_ids.filtered(lambda l: l.product_id.id == product_varient.id)
                if is_bom:
                    continue
                if product_varient:
                    if inner_list[29] == '-' or not inner_list[29]:
                        stock_quant_ids = product_varient.stock_quant_ids.filtered(
                            lambda inv: inv.location_id.usage == 'internal')
                        if len(stock_quant_ids):
                            for stock_quant in stock_quant_ids:
                                stock_quant.quantity = 0
                        else:
                            vals = {
                                'product_id': product_varient.id,
                                'product_uom_id': product_varient.uom_id.id,
                                'location_id': 8,
                                'quantity': 0,
                            }
                            self.env['stock.quant'].create(vals)
                    else:
                        product_varient.dummy_forcast = inner_list[31] if inner_list[31] != '-' else 0
                        stock_quant_ids = product_varient.stock_quant_ids.filtered(lambda inv: inv.location_id.usage == 'internal')
                        first = True
                        if len(stock_quant_ids) > 1:
                            for stock_quant in stock_quant_ids:
                                if first:
                                    stock_quant.quantity = inner_list[29]
                                else:
                                    stock_quant.quantity = 0
                                first = False

                        elif len(stock_quant_ids) == 1:
                            stock_quant_ids.quantity = inner_list[29]

                        else:
                            vals = {
                                'product_id': product_varient.id,
                                'product_uom_id': product_varient.uom_id.id,
                                'location_id': 8,
                                'quantity': inner_list[29],
                            }
                            self.env['stock.quant'].create(vals)


                #
                # if product_varient:
                #     product_varient.qty_available = inner_list[29] if inner_list[29] != '-' else 0
                #     product_varient.dummy_forcast = inner_list[31]

            print("stock updated")


        elif self.report_for == "product":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            for inner_list in main_list:
                type = self.env['product.type'].search([('name', '=', inner_list[3])])
                if not type:
                    type = self.env['product.type'].create({
                        "name": inner_list[3]
                    })
                product = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
                if product:
                    if not product.shopify_product_type:
                        product.shopify_product_type = type.id
            print("complete")
            # For CSV_0 one variant
            # for inner_list in main_list:
            #     product = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
            #     uom = self.env['uom.uom'].search([('name', '=', inner_list[34])])
            #     brand_name = self.env['common.product.brand.ept'].search(
            #         [('name', '=', inner_list[6])]).id
            #     if not brand_name:
            #         brand_name = self.env['common.product.brand.ept'].create({
            #             'name': inner_list[6],
            #         }).id
            #     if not product:
            #         product_tmpl_id = self.env['product.template'].create({
            #             "name": inner_list[2],
            #             "uom_id": uom.id if uom else 1,
            #             "uom_po_id": uom.id if uom else 1,
            #             "type": "product",
            #             "invoice_policy": "order",
            #             "categ_id": self.env.ref('product.product_category_all').id,
            #             "qb_templ_id": inner_list[0],
            #             'default_code': inner_list[16],
            #             "description": inner_list[4],
            #             # "supplier": inner_list[5],
            #             "product_brand_id": brand_name,
            #         })
            #         product_product = self.env['product.product'].search([('product_tmpl_id', '=',product_tmpl_id.id)])
            #         product_product.qb_varient_id = inner_list[1]


# <----------------------------------------------------------------------------------------------------------------------------->


            #  Csv_1 for 2 variants
            # for inner_list in main_list:
            #     if inner_list[0] == float(45095266):
            #         print('hello')
            #
            #     product_temp = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
            #     if not product_temp and inner_list[49] == 'y':
            #         continue
            #     if product_temp and inner_list[49] == 'y':
            #         package = self.env['variant.package'].search([('qb_variant_id', '=', inner_list[1])])
            #         if not package:
            #             product_temp.product_variant_ids[0].variant_package_ids.create({
            #               "name": inner_list[15],
            #               "code": inner_list[16],
            #               "product_id": product_temp.product_variant_ids[0].id,
            #               "value_name": inner_list[10],
            #               "qty": int(inner_list[50]),
            #               "qb_variant_id": inner_list[1],
            #             })
            #         else:
            #             package.product_id = product_temp.product_variant_ids[0].id
            #         continue
            #     if product_temp:
            #         product_vari = self.env['product.product'].search([('qb_varient_id', '=', inner_list[1])])
            #         list_of_attr = []
            #         if not product_vari:
            #             if inner_list[9] and inner_list[10]:
            #                 attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[9])], limit=1)
            #                 if not attribute_id:
            #                     attribute_id = self.env['product.attribute'].create({
            #                         'name': inner_list[9]
            #                     })
            #                 self.create_variants_by_attribute(product_temp, attribute_id,
            #                                                   str(inner_list[10]))
            #                 list_of_attr.append(str(inner_list[10]))
            #
            #             new_product = self.env['product.product'].search(
            #                 [('id', 'in', product_temp.product_variant_ids.ids),
            #                  ('qb_varient_id', '=', False)])
            #
            #             for val in new_product:
            #                 set_list = []
            #                 for value_name in val.product_template_attribute_value_ids:
            #                     set_list.append(value_name.name)
            #                 if sorted(set_list) == sorted(list_of_attr):
            #                     val.write({
            #                         'qb_varient_id': inner_list[1],
            #                         'default_code': inner_list[16],
            #                         'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
            #                     })
            #     else:
            #         list_of_attr = []
            #         uom = self.env['uom.uom'].search([('name', '=', inner_list[34])])
            #         brand_name = self.env['common.product.brand.ept'].search(
            #             [('name', '=', inner_list[6])]).id
            #         if not brand_name:
            #             brand_name = self.env['common.product.brand.ept'].create({
            #                 'name': inner_list[6],
            #             }).id
            #         product_temp = self.env['product.template'].create({
            #             "name": inner_list[2],
            #             "uom_id": uom.id if uom else 1,
            #             "uom_po_id": uom.id if uom else 1,
            #             "type": "product",
            #             "invoice_policy": "order",
            #             "categ_id": self.env.ref('product.product_category_all').id,
            #             "qb_templ_id": inner_list[0],
            #             "description": inner_list[4],
            #             "product_brand_id": brand_name,
            #         })
            #         if inner_list[9] and inner_list[10]:
            #             attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[9])], limit=1)
            #             if not attribute_id:
            #                 attribute_id = self.env['product.attribute'].create({
            #                     'name': inner_list[9]
            #                 })
            #             self.create_variants_by_attribute(product_temp, attribute_id,
            #                                               str(inner_list[10]))
            #             list_of_attr.append(str(inner_list[10]))
            #
            #         new_product = self.env['product.product'].search(
            #             [('id', 'in', product_temp.product_variant_ids.ids),
            #              ('qb_varient_id', '=', False)])
            #
            #         for val in new_product:
            #             set_list = []
            #             for value_name in val.product_template_attribute_value_ids:
            #                 set_list.append(value_name.name)
            #             if sorted(set_list) == sorted(list_of_attr):
            #                 val.write({
            #                     'qb_varient_id': inner_list[1],
            #                     'default_code': inner_list[16],
            #                     'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
            #                 })

#<------------------------------------------------------------------------------------------------------------------------->
        # Csv_02 ,Csv_03, csv_08, csv_10 without packes for 3,4, 22 varents 40 variants length grater then 12

            # for inner_list in main_list:
            #     if len(inner_list[15]) >= 10:
            #         product_temp = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
            #         uom = self.env['uom.uom'].search([('name', '=', inner_list[34])])
            #         brand_name = self.env['common.product.brand.ept'].search(
            #             [('name', '=', inner_list[6])]).id
            #         if not brand_name:
            #             brand_name = self.env['common.product.brand.ept'].create({
            #                 'name': inner_list[6],
            #             }).id
            #         if not product_temp:
            #             product_temp = self.env['product.template'].create({
            #                 "name": inner_list[2],
            #                 "uom_id": uom.id if uom else 1,
            #                 "uom_po_id": uom.id if uom else 1,
            #                 "type": "product",
            #                 "invoice_policy": "order",
            #                 "categ_id": self.env.ref('product.product_category_all').id,
            #                 "qb_templ_id": inner_list[0],
            #                 'default_code': inner_list[16],
            #                 "description": inner_list[4],
            #                 # "supplier": inner_list[5],
            #                 "product_brand_id": brand_name,
            #             })
            #             list_of_attr = []
            #             if inner_list[9] and inner_list[10]:
            #                 attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[9])], limit=1)
            #                 if not attribute_id:
            #                     attribute_id = self.env['product.attribute'].create({
            #                         'name': inner_list[9]
            #                     })
            #                 self.create_variants_by_attribute(product_temp, attribute_id,
            #                                                   str(inner_list[10]))
            #                 list_of_attr.append(str(inner_list[10]))
            #
            #             new_product = self.env['product.product'].search(
            #                 [('id', 'in', product_temp.product_variant_ids.ids),
            #                  ('qb_varient_id', '=', False)])
            #
            #             for val in new_product:
            #                 set_list = []
            #                 for value_name in val.product_template_attribute_value_ids:
            #                     set_list.append(value_name.name)
            #                 if sorted(set_list) == sorted(list_of_attr):
            #                     val.write({
            #                         'qb_varient_id': inner_list[1],
            #                         'default_code': inner_list[16],
            #                         'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
            #                     })
            #         else:
            #             product_vari = self.env['product.product'].search([('qb_varient_id', '=', inner_list[1])])
            #             list_of_attr = []
            #             if not product_vari:
            #
            #                 if inner_list[9] and inner_list[10]:
            #                     attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[9])], limit=1)
            #                     if not attribute_id:
            #                         attribute_id = self.env['product.attribute'].create({
            #                             'name': inner_list[9]
            #                         })
            #                     self.create_variants_by_attribute(product_temp, attribute_id,
            #                                                       str(inner_list[10]))
            #                     list_of_attr.append(str(inner_list[10]))
            #
            #                 new_product = self.env['product.product'].search(
            #                     [('id', 'in', product_temp.product_variant_ids.ids),
            #                      ('qb_varient_id', '=', False)])
            #
            #                 for val in new_product:
            #                     set_list = []
            #                     for value_name in val.product_template_attribute_value_ids:
            #                         set_list.append(value_name.name)
            #                     if sorted(set_list) == sorted(list_of_attr):
            #                         val.write({
            #                             'qb_varient_id': inner_list[1],
            #                             'default_code': inner_list[16],
            #                             'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
            #                         })


# for length less then 12
#             for inner_list in main_list:
#                 if len(inner_list[15]) <= 12:
#                     product_temp = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
#                     if product_temp:
#                         package = self.env['variant.package'].search([('qb_variant_id', '=', inner_list[1])])
#                         if len(inner_list[16].split('x')) != 2:
#                             print("hello")
#                         else:
#
#                             if not package:
#                                 is_product_product = self.env['product.product'].search(
#                                     [('default_code', '=', inner_list[16].split('x')[0])])
#                                 if is_product_product:
#                                     product_temp.product_variant_ids[0].variant_package_ids.create({
#                                       "name": inner_list[15],
#                                       "code": inner_list[16],
#                                       "product_id": is_product_product.id,
#                                       "value_name": inner_list[10],
#                                       "qty": int(inner_list[16].split('x')[1]),
#                                       "qb_variant_id": inner_list[1],
#                                       "price": 0 if inner_list[39] == "" else float(inner_list[39]),
#                                     })
#                             # else:
#                             #     package.product_id = product_temp.product_variant_ids[0].id
#                             continue



# <--------------------------------------------------------------------------------------------------------------------------------->
# Csv_4 for 5 varients
#             for inner_list in main_list:
#                     product_temp = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
#                     uom = self.env['uom.uom'].search([('name', '=', inner_list[34])])
#                     brand_name = self.env['common.product.brand.ept'].search(
#                         [('name', '=', inner_list[6])]).id
#                     if not brand_name:
#                         brand_name = self.env['common.product.brand.ept'].create({
#                             'name': inner_list[6],
#                         }).id
#                     if not product_temp:
#                         product_temp = self.env['product.template'].create({
#                             "name": inner_list[2],
#                             "uom_id": uom.id if uom else 1,
#                             "uom_po_id": uom.id if uom else 1,
#                             "type": "product",
#                             "invoice_policy": "order",
#                             "categ_id": self.env.ref('product.product_category_all').id,
#                             "qb_templ_id": inner_list[0],
#                             'default_code': inner_list[16],
#                             "description": inner_list[4],
#                             # "supplier": inner_list[5],
#                             "product_brand_id": brand_name,
#                         })
#                         list_of_attr = []
#                         if inner_list[9] and inner_list[10]:
#                             attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[9])], limit=1)
#                             if not attribute_id:
#                                 attribute_id = self.env['product.attribute'].create({
#                                     'name': inner_list[9]
#                                 })
#                             self.create_variants_by_attribute(product_temp, attribute_id,
#                                                               str(inner_list[10]))
#                             list_of_attr.append(str(inner_list[10]))
#
#                         new_product = self.env['product.product'].search(
#                             [('id', 'in', product_temp.product_variant_ids.ids),
#                              ('qb_varient_id', '=', False)])
#
#                         for val in new_product:
#                             set_list = []
#                             for value_name in val.product_template_attribute_value_ids:
#                                 set_list.append(value_name.name)
#                             if sorted(set_list) == sorted(list_of_attr):
#                                 val.write({
#                                     'qb_varient_id': inner_list[1],
#                                     'default_code': inner_list[16],
#                                     'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
#                                 })
#                     else:
#                         product_vari = self.env['product.product'].search([('qb_varient_id', '=', inner_list[1])])
#                         list_of_attr = []
#                         if not product_vari:
#                             if inner_list[9] and inner_list[10]:
#                                 attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[9])], limit=1)
#                                 if not attribute_id:
#                                     attribute_id = self.env['product.attribute'].create({
#                                         'name': inner_list[9]
#                                     })
#                                 self.create_variants_by_attribute(product_temp, attribute_id,
#                                                                   str(inner_list[10]))
#                                 list_of_attr.append(str(inner_list[10]))
#
#                             new_product = self.env['product.product'].search(
#                                 [('id', 'in', product_temp.product_variant_ids.ids),
#                                  ('qb_varient_id', '=', False)])
#
#                             for val in new_product:
#                                 set_list = []
#                                 for value_name in val.product_template_attribute_value_ids:
#                                     set_list.append(value_name.name)
#                                 if sorted(set_list) == sorted(list_of_attr):
#                                     val.write({
#                                         'qb_varient_id': inner_list[1],
#                                         'default_code': inner_list[16],
#                                         'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
#                                     })


# <------------------------------------------------------------------------------------------------------------------------------------------------------->
# for csv_5, csv_6 for 2 attributes
#                     for inner_list in main_list:
#                         if len(inner_list[15]) >= 10:
#                             product_temp = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
#                             uom = self.env['uom.uom'].search([('name', '=', inner_list[34])])
#                             brand_name = self.env['common.product.brand.ept'].search(
#                                 [('name', '=', inner_list[6])]).id
#                             if not brand_name:
#                                 brand_name = self.env['common.product.brand.ept'].create({
#                                     'name': inner_list[6],
#                                 }).id
#                             if not product_temp:
#                                 product_temp = self.env['product.template'].create({
#                                     "name": inner_list[2],
#                                     "uom_id": uom.id if uom else 1,
#                                     "uom_po_id": uom.id if uom else 1,
#                                     "type": "product",
#                                     "invoice_policy": "order",
#                                     "categ_id": self.env.ref('product.product_category_all').id,
#                                     "qb_templ_id": inner_list[0],
#                                     'default_code': inner_list[16],
#                                     "description": inner_list[4],
#                                     # "supplier": inner_list[5],
#                                     "product_brand_id": brand_name,
#                                 })
#                                 list_of_attr = []
#                                 if inner_list[9] and inner_list[10]:
#                                     attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[9])],
#                                                                                         limit=1)
#                                     if not attribute_id:
#                                         attribute_id = self.env['product.attribute'].create({
#                                             'name': inner_list[9]
#                                         })
#                                     self.create_variants_by_attribute(product_temp, attribute_id,
#                                                                       str(inner_list[10]))
#                                     list_of_attr.append(str(inner_list[10]))
#
#                                 if inner_list[11] and inner_list[12]:
#                                     attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[11])],
#                                                                                         limit=1)
#                                     if not attribute_id:
#                                         attribute_id = self.env['product.attribute'].create({
#                                             'name': inner_list[11]
#                                         })
#                                     self.create_variants_by_attribute(product_temp, attribute_id,
#                                                                       str(inner_list[12]))
#                                     list_of_attr.append(str(inner_list[12]))
#
#                                 new_product = self.env['product.product'].search(
#                                     [('id', 'in', product_temp.product_variant_ids.ids),
#                                      ('qb_varient_id', '=', False)])
#
#                                 for val in new_product:
#                                     set_list = []
#                                     for value_name in val.product_template_attribute_value_ids:
#                                         set_list.append(value_name.name)
#                                     if sorted(set_list) == sorted(list_of_attr):
#                                         val.write({
#                                             'qb_varient_id': inner_list[1],
#                                             'default_code': inner_list[16],
#                                             'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
#                                         })
#                             else:
#                                 product_vari = self.env['product.product'].search(
#                                     [('qb_varient_id', '=', inner_list[1])])
#                                 list_of_attr = []
#                                 if not product_vari:
#
#                                     if inner_list[9] and inner_list[10]:
#                                         attribute_id = self.env['product.attribute'].search(
#                                             [('name', '=', inner_list[9])], limit=1)
#                                         if not attribute_id:
#                                             attribute_id = self.env['product.attribute'].create({
#                                                 'name': inner_list[9]
#                                             })
#                                         self.create_variants_by_attribute(product_temp, attribute_id,
#                                                                           str(inner_list[10]))
#                                         list_of_attr.append(str(inner_list[10]))
#                                     if inner_list[11] and inner_list[12]:
#                                         attribute_id = self.env['product.attribute'].search(
#                                             [('name', '=', inner_list[11])], limit=1)
#                                         if not attribute_id:
#                                             attribute_id = self.env['product.attribute'].create({
#                                                 'name': inner_list[11]
#                                             })
#                                         self.create_variants_by_attribute(product_temp, attribute_id,
#                                                                           str(inner_list[12]))
#                                         list_of_attr.append(str(inner_list[12]))
#
#                                     new_product = self.env['product.product'].search(
#                                         [('id', 'in', product_temp.product_variant_ids.ids),
#                                          ('qb_varient_id', '=', False)])
#
#                                     for val in new_product:
#                                         set_list = []
#                                         for value_name in val.product_template_attribute_value_ids:
#                                             set_list.append(value_name.name)
#                                         if sorted(set_list) == sorted(list_of_attr):
#                                             val.write({
#                                                 'qb_varient_id': inner_list[1],
#                                                 'default_code': inner_list[16],
#                                                 'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
#                                             })


        # for length less then 12
        #             for inner_list in main_list:
        #                 if len(inner_list[15]) <= 10:
        #                     product_temp = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
        #                     if product_temp:
        #                         package = self.env['variant.package'].search([('qb_variant_id', '=', inner_list[1])])
        #                         if len(inner_list[16].split('x')) != 2:
        #                             print("hello")
        #                         else:
        #
        #                             if not package:
        #                                 is_product_product = self.env['product.product'].search(
        #                                     [('default_code', '=', inner_list[16].split('x')[0])])
        #                                 if is_product_product:
        #                                     product_temp.product_variant_ids[0].variant_package_ids.create({
        #                                       "name": inner_list[15],
        #                                       "code": inner_list[16],
        #                                       "product_id": is_product_product.id,
        #                                       "value_name": inner_list[10],
        #                                       "qty": int(inner_list[16].split('x')[1]),
        #                                       "qb_variant_id": inner_list[1],
        #                                       "price": 0 if inner_list[39] == "" else float(inner_list[39]),
        #                                     })
        #                             # else:
        #                             #     package.product_id = product_temp.product_variant_ids[0].id
        #                             continue




# <------------------------------------------------------------------------------------------------------------------------------------------------------>
# for csv_7, csv_09 file
#                 for inner_list in main_list:
#                     if len(inner_list[15]) >= 10:
#                         product_temp = self.env['product.template'].search(
#                             [('qb_templ_id', '=', inner_list[0])])
#                         uom = self.env['uom.uom'].search([('name', '=', inner_list[34])])
#                         brand_name = self.env['common.product.brand.ept'].search(
#                             [('name', '=', inner_list[6])]).id
#                         if not brand_name:
#                             brand_name = self.env['common.product.brand.ept'].create({
#                                 'name': inner_list[6],
#                             }).id
#                         if not product_temp:
#                             product_temp = self.env['product.template'].create({
#                                 "name": inner_list[2],
#                                 "uom_id": uom.id if uom else 1,
#                                 "uom_po_id": uom.id if uom else 1,
#                                 "type": "product",
#                                 "invoice_policy": "order",
#                                 "categ_id": self.env.ref('product.product_category_all').id,
#                                 "qb_templ_id": inner_list[0],
#                                 'default_code': inner_list[16],
#                                 "description": inner_list[4],
#                                 # "supplier": inner_list[5],
#                                 "product_brand_id": brand_name,
#                             })
#                             list_of_attr = []
#                             if inner_list[11] and inner_list[12]:
#                                 attribute_id = self.env['product.attribute'].search(
#                                     [('name', '=', inner_list[11])],
#                                     limit=1)
#                                 if not attribute_id:
#                                     attribute_id = self.env['product.attribute'].create({
#                                         'name': inner_list[11]
#                                     })
#                                 self.create_variants_by_attribute(product_temp, attribute_id,
#                                                                   str(inner_list[12]))
#                                 list_of_attr.append(str(inner_list[12]))
#
#                             if inner_list[13] and inner_list[14]:
#                                 attribute_id = self.env['product.attribute'].search(
#                                     [('name', '=', inner_list[13])],
#                                     limit=1)
#                                 if not attribute_id:
#                                     attribute_id = self.env['product.attribute'].create({
#                                         'name': inner_list[13]
#                                     })
#                                 self.create_variants_by_attribute(product_temp, attribute_id,
#                                                                   str(inner_list[14]))
#                                 list_of_attr.append(str(inner_list[14]))
#
#                             new_product = self.env['product.product'].search(
#                                 [('id', 'in', product_temp.product_variant_ids.ids),
#                                  ('qb_varient_id', '=', False)])
#
#                             for val in new_product:
#                                 set_list = []
#                                 for value_name in val.product_template_attribute_value_ids:
#                                     set_list.append(value_name.name)
#                                 if sorted(set_list) == sorted(list_of_attr):
#                                     val.write({
#                                         'qb_varient_id': inner_list[1],
#                                         'default_code': inner_list[16],
#                                         'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
#                                     })
#                         else:
#                             product_vari = self.env['product.product'].search(
#                                 [('qb_varient_id', '=', inner_list[1])])
#                             list_of_attr = []
#                             if not product_vari:
#
#                                 if inner_list[11] and inner_list[12]:
#                                     attribute_id = self.env['product.attribute'].search(
#                                         [('name', '=', inner_list[11])], limit=1)
#                                     if not attribute_id:
#                                         attribute_id = self.env['product.attribute'].create({
#                                             'name': inner_list[11]
#                                         })
#                                     self.create_variants_by_attribute(product_temp, attribute_id,
#                                                                       str(inner_list[12]))
#                                     list_of_attr.append(str(inner_list[12]))
#                                 if inner_list[13] and inner_list[14]:
#                                     attribute_id = self.env['product.attribute'].search(
#                                         [('name', '=', inner_list[13])], limit=1)
#                                     if not attribute_id:
#                                         attribute_id = self.env['product.attribute'].create({
#                                             'name': inner_list[13]
#                                         })
#                                     self.create_variants_by_attribute(product_temp, attribute_id,
#                                                                       str(inner_list[14]))
#                                     list_of_attr.append(str(inner_list[14]))
#
#                                 new_product = self.env['product.product'].search(
#                                     [('id', 'in', product_temp.product_variant_ids.ids),
#                                      ('qb_varient_id', '=', False)])
#
#                                 for val in new_product:
#                                     set_list = []
#                                     for value_name in val.product_template_attribute_value_ids:
#                                         set_list.append(value_name.name)
#                                     if sorted(set_list) == sorted(list_of_attr):
#                                         val.write({
#                                             'qb_varient_id': inner_list[1],
#                                             'default_code': inner_list[16],
#                                             'lst_price': 0 if inner_list[39] == "" else float(
#                                                 inner_list[39]),
#                                         })

# for length less then 12
#                 for inner_list in main_list:
#                     if len(inner_list[15]) <= 10:
#                         product_temp = self.env['product.template'].search(
#                             [('qb_templ_id', '=', inner_list[0])])
#                         if product_temp:
#                             package = self.env['variant.package'].search(
#                                 [('qb_variant_id', '=', inner_list[1])])
#                             if len(inner_list[16].split('x')) != 2:
#                                 print("hello")
#                             else:
#
#                                 if not package:
#                                     is_product_product = self.env['product.product'].search(
#                                         [('default_code', '=', inner_list[16].split('x')[0])])
#                                     if is_product_product:
#                                         product_temp.product_variant_ids[0].variant_package_ids.create({
#                                             "name": inner_list[15],
#                                             "code": inner_list[16],
#                                             "product_id": is_product_product.id,
#                                             "value_name": inner_list[10],
#                                             "qty": int(inner_list[16].split('x')[1]),
#                                             "qb_variant_id": inner_list[1],
#                                             "price": 0 if inner_list[39] == "" else float(inner_list[39]),
#                                         })
#                                 # else:
#                                 #     package.product_id = product_temp.product_variant_ids[0].id
#                                 continue













































        # 4th step with not template and varient
            #
            # template_list = []
            # varient_list = []
            # for inner_list in main_list:
            #     product_temp = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
            #     if not product_temp:
            #         template_list.append(inner_list[0])
            #     product_temp = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
            #     if product_temp:
            #         product_vari = self.env['product.product'].search([('qb_varient_id', '=', inner_list[1])])
            #         if not product_vari:
            #             varient_list.append(inner_list[2])
            #
            # for inner_list in main_list:
            #     if inner_list[0] in template_list:
            #         product = self.env['product.template'].search([('qb_templ_id', '=', inner_list[0])])
            #         uom = self.env['uom.uom'].search([('name', '=', inner_list[34])])
            #         brand_name = self.env['common.product.brand.ept'].search(
            #             [('name', '=', inner_list[6])]).id
            #         if not brand_name:
            #             brand_name = self.env['common.product.brand.ept'].create({
            #                 'name': inner_list[6],
            #             }).id
            #         if not product:
            #             product_tmpl_id = self.env['product.template'].create({
            #                 "name": inner_list[2],
            #                 "uom_id": uom.id if uom else 1,
            #                 "uom_po_id": uom.id if uom else 1,
            #                 "type": "product",
            #                 "invoice_policy": "order",
            #                 "categ_id": self.env.ref('product.product_category_all').id,
            #                 "qb_templ_id": inner_list[0],
            #                 # "qb_product_type": inner_list[3],
            #                 "description": inner_list[4],
            #                 # "supplier": inner_list[5],
            #                 "product_brand_id": brand_name,
            #             })
            #             product_id = self.env['product.product'].search([('qb_varient_id', '=', inner_list[1])])
            #             # if self.env['product.product'].search([('default_code', '=', inner_list[16])]):
            #             #     continue
            #
            #             list_of_attr = []
            #             if not product_id:
            #                 # not_any = True
            #                 # if inner_list[9] and inner_list[10]:
            #                 #     not_any = False
            #                 #     attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[9])], limit=1)
            #                 #     if not attribute_id:
            #                 #         attribute_id = self.env['product.attribute'].create({
            #                 #             'name': inner_list[9]
            #                 #         })
            #                 #     self.create_variants_by_attribute(product_tmpl_id, attribute_id,
            #                 #                                       str(inner_list[10]))
            #                 #     list_of_attr.append(str(inner_list[10]))
            #                 #
            #                 # if inner_list[11] and inner_list[12]:
            #                 #     not_any = False
            #                 #     attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[11])], limit=1)
            #                 #     if not attribute_id:
            #                 #         attribute_id = self.env['product.attribute'].create({
            #                 #             'name': inner_list[11]
            #                 #         })
            #                 #     self.create_variants_by_attribute(product_tmpl_id, attribute_id,
            #                 #                                       str(inner_list[12]))
            #                 #     list_of_attr.append(str(inner_list[12]))
            #                 #
            #                 # if inner_list[13] and inner_list[14]:
            #                 #     not_any = False
            #                 #     attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[13])], limit=1)
            #                 #     if not attribute_id:
            #                 #         attribute_id = self.env['product.attribute'].create({
            #                 #             'name': inner_list[13]
            #                 #         })
            #                 #     self.create_variants_by_attribute(product_tmpl_id, attribute_id,
            #                 #                                       str(inner_list[14]))
            #                 #     list_of_attr.append(str(inner_list[14]))
            #                 # if not_any:
            #                 attribute_id = self.env.ref('quickbook_integiration.product_attribute_weight')
            #                 tax = self.env['account.tax'].search([("type_tax_use", "=", "sale")], limit=1)
            #                 attribute_value = inner_list[16]
            #                 self.create_variants_by_attribute(product_tmpl_id, attribute_id, str(attribute_value))
            #                 list_of_attr.append(str(inner_list[16]))
            #
            #                 new_product = self.env['product.product'].search(
            #                     [('id', 'in', product_tmpl_id.product_variant_ids.ids),
            #                      ('qb_varient_id', '=', False)])
            #
            #                 for val in new_product:
            #                     set_list = []
            #                     # for value_name in val.product_template_attribute_value_ids:
            #                     #     set_list.append(value_name.name)
            #                     # if sorted(set_list) == sorted(list_of_attr):
            #                     val.write({
            #                         # 'varient_name': inner_list[15],
            #                         # 'varient_description': inner_list[26],
            #                         'qb_varient_id': inner_list[1],
            #                         # 'weight_value': inner_list[33],
            #                         'default_code': inner_list[16],
            #                         # 'buy_price':  0 if inner_list[37] == "" else float(inner_list[37]),
            #                         # 'wholesale_price': 0 if inner_list[38] == "" else float(inner_list[38]),
            #                         # 'retail_price': 0 if inner_list[39] == "" else float(inner_list[39]),
            #                         'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
            #                         "taxes_id": tax if inner_list[27] == 'true' else None,
            #                         # 'option1_label': inner_list[9],
            #                         # 'option1_value': inner_list[10],
            #                         # 'option2_label': inner_list[11],
            #                         # 'option2_value': inner_list[12],
            #                         # 'option3_label': inner_list[13],
            #                         # 'option3_value': inner_list[14],
            #                     })
            #                     c_club_price = self.env['product.pricelist'].search([('id', '=', 13)])
            #                     if c_club_price:
            #                         self.env['product.pricelist.item'].create({
            #                             "product_tmpl_id": product_tmpl_id.id,
            #                             "product_id": product_id.id,
            #                             "min_quantity": 1,
            #                             "fixed_price": 0 if inner_list[39] == "" else float(inner_list[39]),
            #                             "pricelist_id": c_club_price.id
            #                         })
            #                     # quant = self.env['stock.quant'].sudo().create({
            #                     #     'product_id': val.id,
            #                     #     'location_id': 8,
            #                     #     'quantity': 0 if inner_list[29] == "-" else float(inner_list[29]),
            #                     # })
            #                     # quant
            #             else:
            #                 pass
            #
            #         else:
            #             # if self.env['product.product'].search([('default_code', '=', inner_list[16])]):
            #             #     continue
            #             product_id = self.env['product.product'].search([('qb_varient_id', '=', inner_list[1])])
            #             if not product_id:
            #                 # not_any = True
            #                 # if inner_list[9] and inner_list[10]:
            #                 #     not_any = False
            #                 #     list_of_attr = []
            #                 #     attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[9])], limit=1)
            #                 #     if not attribute_id:
            #                 #         attribute_id = self.env['product.attribute'].create({
            #                 #             'name': inner_list[9]
            #                 #         })
            #                 #     self.create_variants_by_attribute(product, attribute_id,
            #                 #                                       str(inner_list[10]))
            #                 #     list_of_attr.append(str(inner_list[10]))
            #                 #
            #                 # if inner_list[11] and inner_list[12]:
            #                 #     not_any = False
            #                 #     attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[11])], limit=1)
            #                 #     if not attribute_id:
            #                 #         attribute_id = self.env['product.attribute'].create({
            #                 #             'name': inner_list[11]
            #                 #         })
            #                 #     self.create_variants_by_attribute(product, attribute_id,
            #                 #                                       str(inner_list[12]))
            #                 #     list_of_attr.append(str(inner_list[12]))
            #                 #
            #                 # if inner_list[13] and inner_list[14]:
            #                 #     not_any = False
            #                 #     attribute_id = self.env['product.attribute'].search([('name', '=', inner_list[13])], limit=1)
            #                 #     if not attribute_id:
            #                 #         attribute_id = self.env['product.attribute'].create({
            #                 #             'name': inner_list[13]
            #                 #         })
            #                 #     self.create_variants_by_attribute(product, attribute_id,
            #                 #                                       str(inner_list[14]))
            #                 #     list_of_attr.append(str(inner_list[14]))
            #                 #
            #                 # if not_any:
            #                 attribute_id = self.env.ref('quickbook_integiration.product_attribute_weight')
            #                 tax = self.env['account.tax'].search([("type_tax_use", "=", "sale")], limit=1)
            #                 attribute_value = inner_list[16]
            #                 self.create_variants_by_attribute(product, attribute_id, str(attribute_value))
            #                 list_of_attr.append(str(inner_list[16]))
            #
            #                 new_product = self.env['product.product'].search(
            #                     [('id', 'in', product.product_variant_ids.ids),
            #                      ('qb_varient_id', '=', False)])
            #
            #                 for val in new_product:
            #                     set_list = []
            #                     # for value_name in val.product_template_attribute_value_ids:
            #                     #     set_list.append(value_name.name)
            #                     # if sorted(set_list) == sorted(list_of_attr):
            #                     val.write({
            #                         # 'varient_name': inner_list[15],
            #                         # 'varient_description': inner_list[26],
            #                         'qb_varient_id': inner_list[1],
            #                         # 'option1_label': inner_list[9],
            #                         # 'weight_value': inner_list[33],
            #                         # 'buy_price':  0 if inner_list[37] == "" else float(inner_list[37]),
            #                         # 'wholesale_price': 0 if inner_list[38] == "" else float(inner_list[38]),
            #                         # 'retail_price': 0 if inner_list[39] == "" else float(inner_list[39]),
            #                         'lst_price': 0 if inner_list[39] == "" else float(inner_list[39]),
            #                         # 'option1_value': inner_list[10],
            #                         # 'option2_label': inner_list[11],
            #                         'default_code': inner_list[16],
            #                         "taxes_id": tax if inner_list[27] == 'true' else None,
            #                         # 'option2_value': inner_list[12],
            #                         # 'option3_label': inner_list[13],
            #                         # 'option3_value': inner_list[14],
            #                     })
            #                     c_club_price = self.env['product.pricelist'].search([('id', '=', 13)])
            #                     if c_club_price:
            #                         self.env['product.pricelist.item'].create({
            #                             "product_tmpl_id": product_tmpl_id.id,
            #                             "product_id": product_id.id,
            #                             "min_quantity": 1,
            #                             "fixed_price": 0 if inner_list[39] == "" else float(inner_list[39]),
            #                             "pricelist_id": c_club_price.id
            #                         })
            #
            #                     # quant = self.env['stock.quant'].sudo().create({
            #                     #     'product_id': val.id,
            #                     #     'location_id': 8,
            #                     #     'quantity':  0 if inner_list[29] == "-" else float(inner_list[29]),
            #                     # })
            #                     # quant
            #             else:
            #                 if product_id.attribute_line_ids:
            #                     for att in product_id.attribute_line_ids:
            #                         attribute = self.env['product.template.attribute.value'].search(
            #                             [('attribute_id', '=', att.attribute_id.id)])
            #                         if attribute:
            #                             for p in attribute:
            #                                 p.price_extra = 0 if inner_list[39] == '' else float(inner_list[39]) - 1

 # <------------------------------------------------------------------------------------------------------------------------->

        # 2nd step for applying qb template id and qb vairent id on products

        # for val in main_list:
        #     product_varient = self.env['product.product'].search([('default_code', '=', str(val[16]))])
        #     if product_varient:
        #         product_varient.write({
        #             'qb_varient_id': val[1],
        #         })
        #         product_varient.product_tmpl_id.qb_templ_id = val[0]

        # <--------------------------------------------------------------------------------------------------------------------------------------->

        # for adding price list of products imported from quickbook

        # for price in main_list:
        #     product_temp = self.env['product.template'].search([('qb_templ_id', '=', price[0])], limit=1)
        #     if product_temp:
        #         product_vari = self.env['product.product'].search([('qb_varient_id', '=', price[1])], limit=1)
        #         if product_vari:
        #             c_club_price = self.env['product.pricelist'].search(
        #                 [('id', '=', 2)])
        #             if c_club_price:
        #                 product = c_club_price.item_ids.search([('product_tmpl_id.qb_templ_id', '=', product_temp.qb_templ_id), ('product_id.qb_varient_id', '=', product_vari.qb_varient_id)])
        #                 if not product:
        #                     self.env['product.pricelist.item'].create({
        #                         "product_tmpl_id": product_temp.id,
        #                         "product_id": product_vari.id,
        #                         "min_quantity": 1,
        #                         "fixed_price": 0 if price[39] == "" else float(price[39]),
        #                         "pricelist_id": c_club_price.id
        #                 })
        # <--------------------------------------------------------------------------------------------------------------------------------------------------------->

                    # i += 1
                    # if (int(i % 100) == 0):
                    #     print("Record created_________________" + str(i) + "\n")
                    # except(Exception) as error:
                    #     print('Error occur at %s with error '%(str(inner_list[0])))
        #code for updat order
        # try:
        #     sale_order = self.env['sale.order'].search([('name', '=', '#' + str(inner_list[0]).split('.')[0])], limit=1)
        #     if sale_order and not sale_order.from_excel:
        #         sale_order.write({
        #             "date_order": datetime.strptime(inner_list[13], "%Y-%m-%d").date()
        #         })

        elif self.report_for == "sale_order":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            i = 0
            for inner_list in main_list:
                try:
                    partner = self.env['res.partner'].search([('name', '=', inner_list[21]), ('email', '=', inner_list[22])], limit=1)
                    if not partner:
                        partner = self.env['res.partner'].create({
                            'name': inner_list[21],
                            'email': inner_list[22],
                        })

                    sale_order = self.env['sale.order'].search([('name', '=', '#'+str(inner_list[0]).split('.')[0])],
                                                               limit=1)
                    if sale_order and not sale_order.from_excel:
                        continue

                    if not sale_order:
                        sale_order = self.env['sale.order'].create({
                            "name": '#'+str(inner_list[0]).split('.')[0],
                            "partner_id": partner.id,
                            "date_order": datetime.strptime(inner_list[13], "%Y-%m-%d").date(),
                            "from_excel": True,
                        })

                    if inner_list[1]:
                        varient = self.env['product.product'].search([('default_code', '=', inner_list[1])],
                                                                     limit=1)
                        tax_id = [self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', float(inner_list[11]))], limit=1).id] if float(inner_list[11]) > 0 else []
                        if varient:
                            sale_order_line = self.env['sale.order.line'].create({
                                "name": varient.name,
                                "product_id": varient.id,
                                "product_uom": varient.uom_id.id,
                                "price_unit": float(inner_list[8]) if inner_list[8] else 0,
                                "product_uom_qty": inner_list[7],
                                'order_id': sale_order.id,
                                'discount': float(inner_list[9]) if inner_list[9] else 0,
                                'tax_id': tax_id
                            })
                        else:
                            varient = self.env['product.product'].create({
                                "name": inner_list[3],
                                "default_code": inner_list[1],
                                "list_price": inner_list[8],
                                "invoice_policy": 'order',
                                "product_not_found": True,
                            })
                            sale_order_line = self.env['sale.order.line'].create({
                                "name": varient.name,
                                "product_id": varient.id,
                                "product_uom": varient.uom_id.id,
                                "price_unit": float(inner_list[8]) if inner_list[8] else 0,
                                "product_uom_qty": inner_list[7],
                                'order_id': sale_order.id,
                                'discount': float(inner_list[9]) if inner_list[9] else 0,
                                'tax_id': tax_id
                            })
                    else:
                        tax_id = [self.env['account.tax'].search(
                            [('type_tax_use', '=', 'sale'), ('amount', '=', float(inner_list[11]))],
                            limit=1).id] if float(inner_list[11]) > 0 else []
                        shipment = self.env.ref("excel_report.shipping_product_for_excel")
                        sale_order_line = self.env['sale.order.line'].create({
                            "name": "shippment",
                            "product_id": shipment.id,
                            "product_uom": shipment.uom_id.id,
                            "product_uom_qty": inner_list[7],
                            "price_unit": float(inner_list[8]) if inner_list[8] else 0,
                            'order_id': sale_order.id,
                            'discount': float(inner_list[9]) if inner_list[9] else 0,
                            'tax_id': tax_id,
                        })
                        # sale_order_line._onchange_qty
                        i += 1
                        if (int(i % 500) == 0):
                            print("Record created_________________" + str(i) + "\n")
                except(Exception) as error:
                    print('Error occur at %s' %(str(inner_list[0])))

        elif self.report_for == "validate_sale_order":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            i = 0
            for inner_list in main_list:
                try:
                    inner_list[7] = str(inner_list[7]).split('.')[0]
                    sale_order = self.env['sale.order'].search([('name', '=', '#'+str(inner_list[7]))],
                                                               limit=1)

                    if sale_order and sale_order.from_excel:
                        old_date = sale_order.date_order
                        if inner_list[4] == 'paid' and inner_list[5] == 'shipped':
                            if not sale_order.picking_ids:
                                sale_order.action_confirm()
                                sale_order.date_order = old_date
                                sale_order.after_live = True
                                for pick in sale_order.picking_ids:
                                    for line in pick.move_ids_without_package:
                                        line.quantity_done = line.product_uom_qty
                                    pick.action_assign()
                                    pick.button_validate()
                                Form(self.env['stock.immediate.transfer']).save().process()
                                sale_order.delivery = True
                                print("delivery created of sale order"+ str(sale_order.name) + "\n")

                                for pick in sale_order.picking_ids:
                                    for line in pick.move_ids_without_package:
                                        sale_line_id = self.env['sale.order.line'].search([('order_id', '=', sale_order.id )] ,limit=1)
                                        vals = {
                                            'name': _('Auto processed move : %s') % line.product_id.name,
                                            'company_id': self.env.company.id,
                                            'origin': sale_order.name,
                                            'product_id': line.product_id.id,
                                            'product_uom_qty': line.product_uom_qty,
                                            'product_uom': line.product_id.uom_id.id,
                                            'location_id': self.env.ref("shopify_ept.customer_location").id,
                                            'location_dest_id': self.env.ref("stock.stock_location_stock").id,
                                            'state': 'confirmed',
                                            'sale_line_id': sale_line_id.id
                                        }
                                        stock_move = self.env['stock.move'].create(vals)
                                        stock_move._action_assign()
                                        stock_move._set_quantity_done(line.product_uom_qty)
                                        stock_move._action_done()


                            if sale_order.picking_ids and sale_order.picking_ids[0].state != 'done':
                                for pick in sale_order.picking_ids:
                                    for line in pick.move_ids_without_package:
                                        line.quantity_done = line.product_uom_qty
                                    pick.action_assign()
                                    pick.button_validate()
                                Form(self.env['stock.immediate.transfer']).save().process()
                                sale_order.delivery = True

                                for pick in sale_order.picking_ids:
                                    for line in pick.move_ids_without_package:
                                        sale_line_id = self.env['sale.order.line'].search([('order_id', '=', sale_order.id )] ,limit=1)
                                        vals = {
                                            'name': _('Auto processed move : %s') % line.product_id.name,
                                            'company_id': self.env.company.id,
                                            'origin': sale_order.name,
                                            'product_id': line.product_id.id,
                                            'product_uom_qty': line.product_uom_qty,
                                            'product_uom': line.product_id.uom_id.id,
                                            'location_id': self.env.ref("shopify_ept.customer_location").id,
                                            'location_dest_id': self.env.ref("stock.stock_location_stock").id,
                                            'state': 'confirmed',
                                            'sale_line_id': sale_line_id.id
                                        }
                                        stock_move = self.env['stock.move'].create(vals)
                                        stock_move._action_assign()
                                        stock_move._set_quantity_done(line.product_uom_qty)
                                        stock_move._action_done()

                                print("delivery created of sale order" + str(sale_order.name) + "\n")
                            # creating invoice here
                            if sale_order.state == 'draft' and sale_order.order_line:
                                sale_order.action_confirm()
                                sale_order.date_order = old_date
                                sale_order.after_live = True
                            if sale_order.invoice_ids and sale_order.invoice_ids[0].state == 'posted':
                                continue
                            if sale_order.amount_total <= 0:
                                continue
                            wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=sale_order.ids,
                                                                                    open_invoices=True).create({})
                            res = wiz.create_invoices()
                            print("invoice created of sale order" + str(sale_order.name) + "\n")
                            invoices = sale_order.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                            for invoice in invoices:
                                invoice.invoice_date = old_date
                                invoice.action_post()
                                action_data = invoice.action_register_payment()
                                wizard = self.env['account.payment.register'].with_context(
                                    action_data['context']).create({})
                                wizard.action_create_payments()
                            sale_order.invoiced = True
                            print("invoice validated of sale order" + str(sale_order.name) + "\n")

                    i += 1
                    if (int(i % 20) == 0):
                        _logger.info("Record created___" + str(i) + '  Order___ ' + str(inner_list[7]))
                        sale_order._cr.commit()

                except(Exception) as error:
                    _logger.info('Error occur at ' + str(inner_list[7]) + '  Due to   ' + str(error))
                    print('Error occur at %s' %(str(inner_list[7])))
                    sale_order.error_in_order = True
        elif self.report_for == "validate_sale_order_unpaid_shipped":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            i = 0
            dict_of_product = {}
            for inner_list in main_list:
                try:
                    inner_list[7] = str(inner_list[7]).split('.')[0]
                    sale_order = self.env['sale.order'].search([('name', '=', '#'+str(inner_list[7]))],
                                                               limit=1)
                    moves = self.env["stock.move"].search_count([("picking_id", "=", False),
                                                                ("sale_line_id", "in", sale_order.order_line.ids)])
                    if sale_order and moves > 0:
                        continue
                    if sale_order and not sale_order.picking_ids:
                        continue
                    if sale_order.name in ['#34858530', '#34890473', '#34883929', '#34877745', '#34881437', '#34869648', '']:
                        continue
                    if sale_order.picking_ids:
                        for pick in sale_order.picking_ids:
                            if pick.state != "done":
                                for line in pick.move_ids_without_package:
                                    line.quantity_done = line.product_uom_qty
                                    if dict_of_product.get(line.product_id.default_code):
                                        dict_of_product[line.product_id.default_code] += line.quantity_done
                                    else:
                                        dict_of_product[line.product_id.default_code] = line.quantity_done

                                pick.action_assign()
                                pick.button_validate()
                            Form(self.env['stock.immediate.transfer']).save().process()

                        for pick in sale_order.picking_ids:
                            for line in pick.move_ids_without_package:
                                sale_line_id = self.env['sale.order.line'].search([('order_id', '=', sale_order.id)],
                                                                                  limit=1)
                                vals = {
                                    'name': _('Auto processed move : %s') % line.product_id.name,
                                    'company_id': self.env.company.id,
                                    'origin': sale_order.name,
                                    'product_id': line.product_id.id,
                                    'product_uom_qty': line.product_uom_qty,
                                    'product_uom': line.product_id.uom_id.id,
                                    'location_id': self.env.ref("shopify_ept.customer_location").id,
                                    'location_dest_id': self.env.ref("stock.stock_location_stock").id,
                                    'state': 'confirmed',
                                    'sale_line_id': sale_line_id.id
                                }
                                stock_move = self.env['stock.move'].create(vals)
                                stock_move._action_assign()
                                stock_move._set_quantity_done(line.product_uom_qty)
                                stock_move._action_done()
                except(Exception) as error:
                    _logger.info('Error occur at ' + str(inner_list[7]) + '  Due to   ' + str(error))
                    print('Error occur at %s' %(str(inner_list[7])))

            for inner_list in main_list:
                inner_list[7] = str(inner_list[7]).split('.')[0]
                sale_order = self.env['sale.order'].search([('name', '=', '#' + str(inner_list[7]))],
                                                           limit=1)
                if sale_order:
                    for pick in sale_order.picking_ids:
                        if pick.state != 'done':
                            _logger.info("Delivery not validated of order number ___" + str(inner_list[7]))
            adjstment_sale_order = self.env['sale.order'].create({
                "name": self.order_name,
                "partner_id": self.env['res.partner'].search([("name", '=', "Administrator")], limit=1).id
            })
            if dict_of_product:
                for key in dict_of_product:
                    order_lines = self.env['sale.order.line'].create({
                        "product_id": self.env['product.product'].search([('default_code', '=', key)]).id,
                        "product_uom_qty": dict_of_product[key],
                        "price_unit": 0,
                        "order_id": adjstment_sale_order.id,
                    })
            adjstment_sale_order.action_confirm()

                    # i += 1
                    # if (int(i % 20) == 0):
                    #     _logger.info("Record created___" + str(i) + '  Order___ ' + str(inner_list[7]))
                        # sale_order._cr.commit()

                # except(Exception) as error:
                #     _logger.info('Error occur at ' + str(inner_list[7]) + '  Due to   ' + str(error))
                #     print('Error occur at %s' %(str(inner_list[7])))
        elif self.report_for == "create_xls_file":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            i = 0
            workbook = xlwt.Workbook()
            sheetwt = workbook.add_sheet('test')
            sheetwt.write(0, 0, 'Assignee First Name')
            sheetwt.write(0, 1, 'Assignee Last Name')
            sheetwt.write(0, 2, 'Order Status')
            sheetwt.write(0, 3, 'Invoice Status')
            sheetwt.write(0, 4, 'Payment Status')
            sheetwt.write(0, 5, 'Fulfillment Status')
            sheetwt.write(0, 6, 'Return Status')
            sheetwt.write(0, 7, 'Order Number')
            sheetwt.write(0, 8, 'Ship At')
            sheetwt.write(0, 9, 'Quantity')
            # sheetwt.write(0, 10, 'Odoo Invoice Status')
            # sheetwt.write(0, 11, 'Odoo Delivery Status')
            roww = 1
            a_list = ['#SO1461', '#349127172', '#349126840', '#349127069', '#349126537', '#349126398', '#349126294', '#349125743', '#349125831', '#349125575', '#349125414', '#349125422', '#SO1424', '#349125229', '#349125026', '#349125096', '#349124381', '#349124468', '#349124033', '#349124066', '#SO1415', '#349124271', '#349123958', '#349123964', '#349123562', '#SO1405', '#SO1406', '#349123404', '#SO1402', '#349123292', '#349123095', '#SO1394', '#SO1395', '#SO1387', '#SO1390', '#349121173', '#349120813', '#349120667', '#349120683', '#349119441', '#349118767', '#349117372', '#349117427', '#349117242', '#349116401', '#349115842', '#SO1344', '#349115437', '#349114485', '#SO1343', '#349114131', '#349113663', '#349112808', '#349112809', '#349112687', '#349112144', '#SO1314', '#SO1317', '#349111147', '#349111202', '#349110909', '#SO1206', '#349110329', '#349109991', '#SO1297', '#349109895', '#349109641', '#SO1286', '#349108744', '#SO1284', '#349108252', '#349107863', '#SO1275', '#349107026', '#349106533', '#SO1268', '#SO1260', '#SO1259', '#SO1253', '#349104090', '#SO1239', '#349100795', '#34899325', '#34899148', '#34899013', '#SO1194', '#34897317', '#SO1180', '#34897308', '#34897040', '#34896802', '#34896318', '#34895850', '#34895590', '#34894450', '#SO1133', '#34892180', '#SO1115', '#SO1109', '#34888941', '#SO1101', '#SO1096', '#SO1081', '#SO1077', '#34884689', '#SO1060', '#SO1056', '#SO1048', '#34881445', '#SO0996', '#SO0972', '#SO0973', '#SO0955', '#SO0939', '#SO0938', '#SO0935', '#SO0901', '#34851663', '#34851140', '#34851154', '#34851055', '#SO0888', '#SO0886', '#34850003', '#34850044', '#34849599', '#34849614', '#34849668', '#34849214', '#34848888', '#34848813', '#SO0876', '#34848080', '#34846513', '#34845194', '#34844763', '#SO0850', '#SO0847', '#34843419', '#34843050', '#34842928', '#34842635', '#34841408', '#SO0821', '#34836720', '#34836109', '#34835217', '#SO0804', '#34834130', '#34833462', '#SO0792', '#34832773', '#34832851', '#34832565', '#34832314', '#34832068', '#34831195', '#34830820', '#34830547', '#SO0759', '#SO0756', '#SO0752', '#34828662', '#34828307', '#34827572', '#34827573', '#34827492', '#SO0728', '#34826838', '#34825767', '#34825768', '#34825798', '#34825740', '#SO0583', '#SO0577', '#SO0559', '#34815539', '#SO0501', '#SO0493', '#SO0469', '#SO0462', '#SO0460', '#SO0456', '#SO0455', '#SO0443', '#SO0441', '#SO0438', '#SO0439', '#SO0435', '#SO0434', '']
            for inner_list in main_list:
                sale_order = self.env['sale.order'].search([('name', '=', '#'+str(inner_list[7]).split('.')[0])])
                if sale_order and sale_order.name in a_list:
                    # if sale_order.picking_ids and sale_order.picking_ids[0].state == 'done':
                    #
                    #     odoo_delivery_status = 'shipped'
                    # else:
                    #
                    #     odoo_delivery_status = 'unshipped'
                    # if sale_order.invoice_ids and sale_order.invoice_ids[0].state == 'posted':
                    #
                    #     odoo_invoice_status = 'paid'
                    # else:
                    #
                    #     odoo_invoice_status = 'unpaid'

                    # if inner_list[4] != odoo_invoice_status or inner_list[5] != odoo_delivery_status:
                    sheetwt.write(roww, 0, inner_list[0])
                    sheetwt.write(roww, 1, inner_list[1])
                    sheetwt.write(roww, 2, inner_list[2])
                    sheetwt.write(roww, 3, inner_list[3])
                    sheetwt.write(roww, 4, inner_list[4])
                    sheetwt.write(roww, 5, inner_list[5])
                    sheetwt.write(roww, 6, inner_list[6])
                    sheetwt.write(roww, 7, inner_list[7])
                    sheetwt.write(roww, 8, inner_list[8])
                    sheetwt.write(roww, 9, inner_list[9])
                    # sheetwt.write(roww, 10, odoo_invoice_status)
                    # sheetwt.write(roww, 11, odoo_delivery_status)
                    roww +=1
                    i += 1
                    if (int(i % 500) == 0):
                        print("lines created" + str(i))
            workbook.save('/home/hafiz/sale_orders_qb/draft_order/draft_order_file2.xls')

        elif self.report_for == "purchase_order":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            i = 0
            # products_not_found = []
            for inner_list in main_list:
                try:
                    partner = self.env['res.partner'].search([('name', '=', inner_list[16]),('email', '=', inner_list[14])], limit=1)
                    if not partner:
                        partner = self.env['res.partner'].create({
                            "name": inner_list[16],
                            "email": inner_list[14],
                            "vat": inner_list[18],
                        })

                    purchase_order = self.env['purchase.order'].search([('name', '=', str(inner_list[0]))], limit=1)
                    date_order = parser.parse(inner_list[9]).astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
                    curruncy = self.env['res.currency'].search([('name', '=', inner_list[12])])
                    if not purchase_order:
                        purchase_order = self.env['purchase.order'].create({
                            "name": str(inner_list[0]),
                            "partner_id": partner.id,
                            "date_order": date_order,
                            "currency_id": curruncy.id if curruncy else False,
                        })
                        if inner_list[1]:
                            varient = self.env['product.product'].search([('default_code', '=', inner_list[1])],
                                                                         limit=1)
                            tax_id = [self.env['account.tax'].search(
                                [('type_tax_use', '=', 'purchase'), ('amount', '=', float(inner_list[7]))],
                                limit=1).id] if float(inner_list[7]) > 0 else []
                            if varient:
                                purchase_order_line = self.env['purchase.order.line'].create({
                                    "name": varient.name,
                                    "product_id": varient.id,
                                    "product_uom": varient.uom_id.id,
                                    'order_id': purchase_order.id,
                                    "product_qty": inner_list[5],
                                    "price_unit": float(inner_list[6]) if inner_list[6] else 0,
                                    'taxes_id': tax_id,

                                })
                            else:
                                print('TTTTT')

                    else:

                        if inner_list[1]:
                            varient = self.env['product.product'].search([('default_code', '=', inner_list[1])],
                                                                         limit=1)
                            tax_id = [self.env['account.tax'].search(
                                [('type_tax_use', '=', 'purchase'), ('amount', '=', float(inner_list[7]))],
                                limit=1).id] if float(inner_list[7]) > 0 else []

                            if varient:
                                purchase_order_line = self.env['purchase.order.line'].create({
                                    "name": varient.name,
                                    "product_id": varient.id,
                                    "product_uom": varient.uom_id.id,
                                    'order_id': purchase_order.id,
                                    "product_qty": inner_list[5],
                                    "price_unit": float(inner_list[6]) if inner_list[6] else 0,
                                    'taxes_id': tax_id,

                                })
                            else:
                                print("TEST")
                                # purchase_order_line._onchange_qty
                            # else:
                            #     products_not_found.append([str(inner_list[1]), purchase_order.name])
                        i += 1
                        if (int(i % 500) == 0):
                            print("Record created_________________" + str(i) + "\n")
                except(Exception) as error:
                    print('Error occur at %s' %(str(inner_list[0])))
            # print((products_not_found))













        elif self.report_for == "invoice":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)
            i = 0
            for inner_list in main_list:
                try:
                    sale_order = self.env['sale.order'].search([('name', '=', str(inner_list[0]).split('.')[0])])
                    if sale_order and sale_order.state == 'draft':
                        sale_order.action_confirm()
                        context = {
                            "active_model": 'sale.order',
                            "active_ids": sale_order.id,
                        }
                        payment = self.env['sale.advance.payment.inv'].create({
                            'advance_payment_method': 'delivered',
                        })
                        action_invoice = payment.with_context(context).create_invoices()

                        invoices = self.env['account.move'].search([('invoice_origin', '=', sale_order.name)])
                        if invoices:
                            for invo in invoices:

                                # invo.invoice_line_ids.unlink()

                                invo.write({
                                    "name": str(inner_list[1]).split('.')[0],
                                })
                                # if inner_list[2]:
                                #     varient_sku = self.env['product.product'].search([('default_code', '=', inner_list[2])], limit=1)
                                #     if not varient_sku:
                                #         pass
                                #     if varient_sku:
                                #         for i in invo.invoice_line_ids:
                                #             invoice_line = i.write({
                                #                 "name": varient_sku.name,
                                #                 "product_id": varient_sku.id,
                                #                 "quantity": float(inner_list[7]),
                                #                 "product_uom_id": varient_sku.uom_id.id,
                                #                 "price_unit": varient_sku.list_price,
                                #                 'move_id': invo.id,
                                #                 'discount': 0 if inner_list[9] == '' else float(inner_list[9]),
                                #             })
                                #
                                #
                                #     else:
                                #         shipment = self.env['product.product'].search([('name', '=', "shippment")])
                                #         for i in invo.invoice_line_ids:
                                #             invoice_line = i.write({
                                #                 "name": "shippment",
                                #                 "product_id": shipment.id,
                                #                 "product_uom_id": shipment.uom_id.id,
                                #                 "price_unit": shipment.list_price,
                                #                 'move_id': invo.id,
                                #                 'discount': 0 if inner_list[9] == '' else float(inner_list[9]),
                                #
                                #             })

                        i += 1
                        if (int(i % 500) == 0):
                            print("Record created_________________" + str(i) + "\n")

                    # if sale_order and sale_order.state == 'sale':
                    #     context = {
                    #         "active_model": 'sale.order',
                    #         "active_ids": sale_order.id,
                    #     }
                    #     payment = self.env['sale.advance.payment.inv'].create({
                    #         'advance_payment_method': 'delivered',
                    #     })
                    #     action_invoice = payment.with_context(context).create_invoices()
                    #
                    #     invoices = self.env['account.move'].search([('invoice_origin', '=', sale_order.name)])
                    #     if invoices:
                    #         for invo in invoices:
                    #
                    #             # invo.invoice_line_ids.unlink()
                    #
                    #             invo.write({
                    #                 "name": str(inner_list[1]).split('.')[0],
                    #             })
                    #             if inner_list[2]:
                    #                 varient_sku = self.env['product.product'].search(
                    #                     [('default_code', '=', inner_list[2])], limit=1)
                    #                 if not varient_sku:
                    #                     pass
                    #                 # if varient_sku:
                    #                 #     for i in invo.invoice_line_ids:
                    #                 #         invoice_line = i.write({
                    #                 #             "name": varient_sku.name,
                    #                 #             "product_id": varient_sku.id,
                    #                 #             "quantity": float(inner_list[7]),
                    #                 #             "product_uom_id": varient_sku.uom_id.id,
                    #                 #             "price_unit": varient_sku.list_price,
                    #                 #             'move_id': invo.id,
                    #                 #             'discount': 0 if inner_list[9] == '' else float(inner_list[9]),
                    #                 #         })
                    #
                    #
                    #                 else:
                    #                     shipment = self.env['product.product'].search([('name', '=', "shippment")])
                    #                     # for i in invo.invoice_line_ids:
                    #                     #     invoice_line = i.write({
                    #                     #         "name": "shippment",
                    #                     #         "product_id": shipment.id,
                    #                     #         "product_uom_id": shipment.uom_id.id,
                    #                     #         "price_unit": shipment.list_price,
                    #                     #         'move_id': invo.id,
                    #                     #         'discount': 0 if inner_list[9] == '' else float(inner_list[9]),
                    #                     #
                    #                     #     })
                    #
                    #     i += 1
                    #     if (int(i % 500) == 0):
                    #         print("Record created_________________" + str(i) + "\n")

                    i += 1
                    if (int(i % 500) == 0):
                        print("Record created_________________" + str(i) + "\n")

                except(Exception) as error:
                    print('Error occur at %s' %(str(inner_list[0])))



    def create_variants_by_attribute(self, p_template_id, attribute_id, attribute_value):
        att_id = False
        all_atts = []

        for att_value in attribute_id.value_ids:
            if att_value.name == attribute_value:
                att_id = att_value
                break

        if not att_id:
            att_id = self.env['product.attribute.value'].create({
                'name': attribute_value,
                'attribute_id': attribute_id.id,
            })

        all_atts.append(att_id.id)

        if p_template_id.attribute_line_ids:
            for att_line in p_template_id.attribute_line_ids:
                if att_line.attribute_id == attribute_id:
                    all_atts = all_atts + att_line.value_ids.ids
                    att_line.update({
                        'value_ids': [(6, 0, all_atts)],
                    })
                    return

        else:
            self.env['product.template.attribute.line'].create({
                'product_tmpl_id': p_template_id.id,
                'attribute_id': attribute_id.id,
                'value_ids': [(6, 0, all_atts)],
            })
            return

        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': p_template_id.id,
            'attribute_id': attribute_id.id,
            'value_ids': [(6, 0, all_atts)],
        })