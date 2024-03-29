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
    report_for = fields.Selection([('create_xls_file', 'create_xls_file'),('invoice', 'Invoice'), ('invoice_payment_validate', 'OLD Invoice Payment Validation'), ('old_invoice_date_update', 'Profit and Lose Updation'), ('validate_sale_order_unpaid_shipped', 'Validate Sale Order Unpaid Shipped'), ('product', 'Product'), ('product_cost', 'Product Cost'), ('product_forcast', 'Product Forcast'), ('check_true', 'Check True'), ('compare_onhand_stock', 'Compare onhand Stock'), ('compare_forcast_stock', 'Compare forcast Stock'), ('check_false', 'Check False'), ('product_stock', 'Product Stock'), ('pack_price', 'Pack Price'), ('price_list', 'Price List'), ('validate_sale_order', 'Validate Sale Order'), ('sale_order', 'Sale Order'), ('purchase_order', 'Purchase Order'), ('customer', 'Customer')])
    order_name = fields.Char()

    def create_order_report(self):

        workbook = xlwt.Workbook()
        sheetwt = workbook.add_sheet('Orders Report')
        sheetwt.write(0, 0, 'Order Number')
        sheetwt.write(0, 1, 'Order Date')
        sheetwt.write(0, 2, 'Date Of Invoice')
        sheetwt.write(0, 3, 'Total Paid Amount')
        sheetwt.write(0, 4, 'Customer Name')
        sheetwt.write(0, 5, 'Invoice Status')
        roww = 1
        sale_orders = self.env['sale.order'].search([('date_order', '<=', '30/06/2022:23:59:59'), ('state', '=', 'sale')])
        i = 0
        for order in sale_orders:
            july_1st_date = datetime. strptime("01/07/22", '%d/%m/%y').date()
            if order.invoice_ids:
                for invoice in order.invoice_ids:
                    if invoice.invoice_date and invoice.invoice_date >= july_1st_date:
                        sheetwt.write(roww, 0, order.name)
                        sheetwt.write(roww, 1, str(order.date_order))
                        sheetwt.write(roww, 2, str(invoice.invoice_date))
                        sheetwt.write(roww, 3, invoice.amount_total)
                        sheetwt.write(roww, 4, invoice.partner_id.name)
                        sheetwt.write(roww, 5, invoice.payment_state)
                        roww += 1
                        i += 1

                        if (int(i % 100) == 0):
                            print("Record Created_________________" + str(i) + "\n")
        workbook.save('/home/hafiz/garron_sale/orders_updated_file.xls')

            # pmt_wizard = self.env['account.payment.register'].with_context(active_model='account.move',
            #                                                                active_ids=caba_inv.ids).create({
            #     'payment_date': '2017-01-01',
            #     'journal_id': self.company_data['default_journal_bank'].id,
            #     'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            # })


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
    def create_transfer(self):

        # cirrent_move = self.env['account.move'].search([('id', '=', 346614)])
        # cirrent_move.invoice_payments_widget
        # json.loads(cirrent_move.invoice_payments_widget)
        # reconsiles = json.loads(cirrent_move.invoice_payments_widget)['content'][0]['account_payment_id']
        start_date = datetime. strptime('01/06/22', '%d/%m/%y').date()
        end_date = datetime. strptime('30/06/22', '%d/%m/%y').date()
        all_invoices = self.env['account.move'].search(
            [('move_type', '=', 'out_invoice'), ('invoice_date', '<=', end_date),('invoice_date', '>=', start_date ),
             ('payment_state', '=', 'in_payment'), ('state', '=', 'posted')])

        # payment_jaurnal = self.env['account.journal'].search([('name','=', 'Old Everyday Account'),('type', '=', 'bank')],limit=1)
        i = 0
        for invoice in all_invoices:
            try:
                payment_reconsile = json.loads(invoice.invoice_payments_widget)['content']
                if payment_reconsile:
                    for payment in payment_reconsile:
                        reconsile = self.env['account.payment'].search([('id', '=', payment.get('account_payment_id'))])
                        if reconsile:
                            reconsile.action_draft()
                            reconsile.action_cancel()
                            reconsile.unlink()
                invoice.button_draft()
                invoice.button_cancel()
                invoice.was_invoiced = True
                # action_data = invoice.action_register_payment()
                # wizard = self.env['account.payment.register'].with_context(
                #     action_data['context']).create({
                #     'payment_date': invoice.invoice_date,
                #     'journal_id': payment_jaurnal.id,
                # })
                # wizard.action_create_payments()
                i +=1
                print(invoice.name)
                if (int(i % 10) == 0):
                    print("Record Deleted_________________"+ invoice.name+' count '+ str(i) + "\n")
                    _logger.info("Record Deleted_________________"+ invoice.name+' count '+ str(i) + "\n")
                    invoice._cr.commit()
            except(Exception) as error:
                print(('Error occur at ' + invoice.name + '  Due to   ' + str(error)))
                _logger.info(('Error occur at ' + invoice.name + '  Due to   ' + str(error)))


            # pmt_wizard = self.env['account.payment.register'].with_context(active_model='account.move',
            #                                                                active_ids=caba_inv.ids).create({
            #     'payment_date': '2017-01-01',
            #     'journal_id': self.company_data['default_journal_bank'].id,
            #     'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            # })


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
                    sale_order = self.env['sale.order'].search([('name', '=', '#'+str(inner_list[0]).split('.')[0])])
                    if sale_order:
                        customer = self.env['res.partner'].search([('name', '=', str(inner_list[3]))], limit=1)
                        if not customer:
                            customer = self.env['res.partner'].create({
                                'name': inner_list[3]
                            })
                        sale_order.partner_id = customer.id
                        sale_order.onchange_partner_id()
                        # sale_order.partner_invoice_id = customer.partner_invoice_id.id
                        # sale_order.partner_shipping_id = customer.partner_shipping_id.id
                        if sale_order.picking_ids:
                            for pick in sale_order.picking_ids:
                                pick.partner_id = customer.id
                        if sale_order.invoice_ids:
                            for invoic in sale_order.invoice_ids:
                                invoic.partner_id = customer.id
                                invoic._onchange_partner_id()
                        i += 1
                        if (int(i % 10) == 0):
                            print("Record created_________________" + str(i) + "\n")
                            _logger.info("Record created_________________" + str(i) + "\n")
                except(Exception) as error:
                    _logger.info('Error occur at %s' %(str(inner_list[0])))

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
                    _logger.info('Error occur at ' + str(nam[0] + '  Due to   ' + str(error)))
                    print('Error occur at %s' % (str(nam[0])))
        elif self.report_for == "invoice_payment_validate":
            for sheet in wb.sheets():
                for row in range(1, sheet.nrows):
                    list = []
                    for col in range(sheet.ncols):
                        list.append(sheet.cell(row, col).value)
                    main_list.append(list)

            i = int(self.order_name)
            for inner_list in main_list:
                try:
                    inner_list[7] = str(inner_list[7]).split('.')[0]
                    sale_order = self.env['sale.order'].search([('name', '=', '#' + str(inner_list[7]))],
                                                               limit=1)

                    if sale_order and sale_order.amount_total <= 0 and not sale_order.invoice_ids:
                        old_date = sale_order.date_order
                        wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=sale_order.ids,
                                                                                open_invoices=True).create({})
                        res = wiz.create_invoices()
                        invoices = sale_order.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                        for invoice in invoices:
                            invoice.invoice_date = old_date
                            invoice.date = old_date
                            invoice.name = 'INV/' + str(old_date.year) + '/' + str(old_date.month) + str(i)
                            i += 1
                            # invoice.invoice_date_due = old_date

                            # invoice._onchange_invoice_date()

                            invoice.action_post()
                            # action_data = invoice.action_register_payment()
                            # wizard = self.env['account.payment.register'].with_context(
                            #     action_data['context']).create({})
                            # wizard.action_create_payments()

                        if (int(i % 20) == 0):
                            _logger.info("Record created___" + str(i) + '  Order___ ' + str(inner_list[7]))
                            sale_order._cr.commit()

                except(Exception) as error:
                    _logger.info('Error occur at ' + str(inner_list[7]) + '  Due to   ' + str(error))
                    print('Error occur at %s' % (str(inner_list[7])))

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
                    sale_order = self.env['sale.order'].search([('name', '=', '#'+str(inner_list[4]).split('.')[0])],limit=1)
                    if not sale_order:
                        partner = self.env['res.partner'].search(
                            [('name', '=', inner_list[5])], limit=1)
                        if not partner:
                            partner = self.env['res.partner'].create({
                                'name': inner_list[5],
                            })
                        sale_order = self.env['sale.order'].create({
                            "name": '#'+str(inner_list[4]).split('.')[0],
                            "partner_id": partner.id,
                            "date_order": datetime.now(),
                            "from_excel": True,
                        })

                        if inner_list[16]:
                            varient = self.env['product.product'].search([('default_code', '=', inner_list[16])],
                                                                         limit=1)
                            # tax_id = [self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', float(inner_list[50]))], limit=1).id] if inner_list[50] != '' else []
                            if varient:
                                sale_order_line = self.env['sale.order.line'].create({
                                    "name": varient.name,
                                    "product_id": varient.id,
                                    "product_uom": varient.uom_id.id,
                                    "price_unit": float(inner_list[18]) if inner_list[18] else 0,
                                    "product_uom_qty": inner_list[17],
                                    'order_id': sale_order.id,
                                    'discount': float(inner_list[20]) if inner_list[20] else 0,
                                    # 'tax_id': tax_id
                                })
                            # else:
                            #     varient = self.env['product.product'].create({
                            #         "name": inner_list[43],
                            #         "default_code": inner_list[44],
                            #         "list_price": float(inner_list[46]) if inner_list[46] else 0,
                            #         "invoice_policy": 'order',
                            #         "product_not_found": True,
                            #     })
                            #     sale_order_line = self.env['sale.order.line'].create({
                            #         "name": varient.name,
                            #         "product_id": varient.id,
                            #         "product_uom": varient.uom_id.id,
                            #         "price_unit": float(inner_list[46]) if inner_list[46] else 0,
                            #         "product_uom_qty": inner_list[45],
                            #         'order_id': sale_order.id,
                            #         'discount': float(inner_list[48]) if inner_list[48] else 0,
                            #         'tax_id': tax_id
                            #     })
                        else:
                            # tax_id = [self.env['account.tax'].search(
                            #     [('type_tax_use', '=', 'sale'), ('amount', '=', float(inner_list[50]))],
                            #     limit=1).id] if inner_list[50] != '' else []
                            shipment = self.env.ref("excel_report.shipping_product_for_excel")
                            sale_order_line = self.env['sale.order.line'].create({
                                "name": "shippment",
                                "product_id": shipment.id,
                                "product_uom": shipment.uom_id.id,
                                "product_uom_qty": inner_list[17],
                                "price_unit": float(inner_list[18]) if inner_list[18] else 0,
                                'order_id': sale_order.id,
                                'discount': float(inner_list[20]) if inner_list[20] else 0,
                                # 'tax_id': tax_id,
                            })
                    else:
                        if inner_list[16]:
                            varient = self.env['product.product'].search([('default_code', '=', inner_list[16])],
                                                                         limit=1)
                            # tax_id = [self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', float(inner_list[50]))], limit=1).id] if inner_list[50] != '' else []
                            if varient:
                                sale_order_line = self.env['sale.order.line'].create({
                                    "name": varient.name,
                                    "product_id": varient.id,
                                    "product_uom": varient.uom_id.id,
                                    "price_unit": float(inner_list[18]) if inner_list[18] else 0,
                                    "product_uom_qty": inner_list[17],
                                    'order_id': sale_order.id,
                                    'discount': float(inner_list[20]) if inner_list[20] else 0,
                                    # 'tax_id': tax_id
                                })
                            # else:
                            #     varient = self.env['product.product'].create({
                            #         "name": inner_list[43],
                            #         "default_code": inner_list[44],
                            #         "list_price": float(inner_list[46]) if inner_list[46] else 0,
                            #         "invoice_policy": 'order',
                            #         "product_not_found": True,
                            #     })
                            #     sale_order_line = self.env['sale.order.line'].create({
                            #         "name": varient.name,
                            #         "product_id": varient.id,
                            #         "product_uom": varient.uom_id.id,
                            #         "price_unit": float(inner_list[46]) if inner_list[46] else 0,
                            #         "product_uom_qty": inner_list[45],
                            #         'order_id': sale_order.id,
                            #         'discount': float(inner_list[48]) if inner_list[48] else 0,
                            #         'tax_id': tax_id
                            #     })
                        else:
                            # tax_id = [self.env['account.tax'].search(
                            #     [('type_tax_use', '=', 'sale'), ('amount', '=', float(inner_list[50]))],
                            #     limit=1).id] if inner_list[50] !="" else []
                            shipment = self.env.ref("excel_report.shipping_product_for_excel")
                            sale_order_line = self.env['sale.order.line'].create({
                                "name": "shippment",
                                "product_id": shipment.id,
                                "product_uom": shipment.uom_id.id,
                                "product_uom_qty": inner_list[17],
                                "price_unit": float(inner_list[18]) if inner_list[18] else 0,
                                'order_id': sale_order.id,
                                'discount': float(inner_list[20]) if inner_list[20] else 0,
                                # 'tax_id': tax_id,
                            })
                            i += 1
                            if (int(i % 10) == 0):
                                print("Record created_________________" + str(i) + "\n")
                except(Exception) as error:
                    print(('Error occur at ' + str(inner_list[4]) + '  Due to   ' + str(error)))

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
            sheetwt.write(0, 0, 'Invoice ID')
            sheetwt.write(0, 1, 'Invoice Status')
            sheetwt.write(0, 2, 'Payment Status')
            sheetwt.write(0, 3, 'Order ID')
            sheetwt.write(0, 4, 'Order Number')
            sheetwt.write(0, 5, 'Order Company Name')
            sheetwt.write(0, 6, 'Order Tax Treatment')
            sheetwt.write(0, 7, 'Invoice Number')
            sheetwt.write(0, 8, 'Invoice Date')
            sheetwt.write(0, 9, 'Payment Due Date')
            sheetwt.write(0, 10, 'Exchange Rate')
            sheetwt.write(0, 11, 'Invoice Notes')
            sheetwt.write(0, 12, 'Shipping Address')
            sheetwt.write(0, 13, 'Billing Address')
            sheetwt.write(0, 14, 'Freeform Line Item Name')
            sheetwt.write(0, 15, 'Variant Name')
            sheetwt.write(0, 16, 'Variant SKU')
            sheetwt.write(0, 17, 'Invoiced Quantity')
            sheetwt.write(0, 18, 'Item Price')
            sheetwt.write(0, 19, 'Item Discount Amount')
            sheetwt.write(0, 20, 'Item Discount Percentage')
            sheetwt.write(0, 21, 'Item Tax Rate Label')
            sheetwt.write(0, 22, 'Item Tax Rate')
            sheetwt.write(0, 23, 'Payment Term')
            sheetwt.write(0, 24, 'Payment Amount')
            sheetwt.write(0, 25, 'Payment Method')
            sheetwt.write(0, 26, 'Is Payment Active')
            roww = 1
            for inner_list in main_list:
                sale_order = self.env['sale.order'].search([('name', '=', '#'+str(inner_list[4]).split('.')[0])])
                if not sale_order:
                    # # if sale_order.picking_ids and sale_order.picking_ids[0].state == 'done':
                    # #
                    # #     odoo_delivery_status = 'shipped'
                    # # else:
                    # #
                    # #     odoo_delivery_status = 'unshipped'
                    # if sale_order.invoice_ids and sale_order.invoice_ids[0].state == 'posted':
                    #
                    #     odoo_invoice_status = 'paid'
                    # else:
                    #
                    #     odoo_invoice_status = 'unpaid'
                    #
                    # if inner_list[2] != odoo_invoice_status:
                    #     sheetwt.write(roww, 0, inner_list[4])
                    sheetwt.write(roww, 0, inner_list[0])
                    sheetwt.write(roww, 1, inner_list[1])
                    sheetwt.write(roww, 2, inner_list[2])
                    sheetwt.write(roww, 3, inner_list[3])
                    sheetwt.write(roww, 4, inner_list[4])
                    sheetwt.write(roww, 5, inner_list[5])
                    sheetwt.write(roww, 6, inner_list[6])
                    sheetwt.write(roww, 7, inner_list[7])
                    sheetwt.write(roww, 8, str(inner_list[8]))
                    sheetwt.write(roww, 9, str(inner_list[9]))
                    sheetwt.write(roww, 10, inner_list[10])
                    sheetwt.write(roww, 11, inner_list[11])
                    sheetwt.write(roww, 12, inner_list[12])
                    sheetwt.write(roww, 13, inner_list[13])
                    sheetwt.write(roww, 14, inner_list[14])
                    sheetwt.write(roww, 15, inner_list[15])
                    sheetwt.write(roww, 16, inner_list[16])
                    sheetwt.write(roww, 17, inner_list[17])
                    sheetwt.write(roww, 18, inner_list[18])
                    sheetwt.write(roww, 19, inner_list[19])
                    sheetwt.write(roww, 20, inner_list[20])
                    sheetwt.write(roww, 21, inner_list[21])
                    sheetwt.write(roww, 22, inner_list[22])
                    sheetwt.write(roww, 23, inner_list[23])
                    sheetwt.write(roww, 24, inner_list[24])
                    sheetwt.write(roww, 25, inner_list[25])
                    sheetwt.write(roww, 26, inner_list[26])
                    roww +=1
                    i += 1
                    if (int(i % 10) == 0):
                        print("lines created" + str(i))
            workbook.save('/home/hafiz/sale_orders_qb/orders_not_exist/Final_File_SO.xls')

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