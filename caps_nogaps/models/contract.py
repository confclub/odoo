# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import math
from datetime import datetime, timedelta
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta

class CapsContract(models.Model):
    _name = 'cap.contract'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(default=lambda self: _('New'))
    # pieces_per_carton = fields.Integer(help='how many pieces of the product are in a whole carton')
    # pieces_per_bag = fields.Integer(help='how many pieces of the product that are in a single bag')
    # pieces_per_daily_pack = fields.Float(help='how many pieces of this product are in a single daily pack')
    # num_daily_packs = fields.Integer(help='how many daily packs of this product are in the order (their deliveries are combined for efficiency)')
    # order_months = fields.Integer(help='how many months this order is for')
    reason = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('start', 'Start'),
        ('end', 'End'),
        ('cancel', 'Cancel')
    ], default='draft')
    customer_id = fields.Many2one("res.partner")
    start_date = fields.Date()
    attachment_ids = fields.One2many('contract.attachment', 'contract_id', string='Attachments')

    product_ids = fields.One2many("contract.product", "contract_id")
    sale_count = fields.Integer(string="Sale Count", compute='_compute_sale_count')
    order_months = fields.Integer(help='how many months this order is for' )
    shipment_price = fields.Float()
    shopify_order_id = fields.Char()
    company_id = fields.Many2one('res.company')

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            # if 'date_order' in vals:
            #     seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('cap.contract', sequence_date=seq_date) or _('New')
        result = super(CapsContract, self).create(vals)
        return result



    def open_sale_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Orders',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.env['sale.order'].search([
                ('contract_id', '=', self.id)]).ids)],
        }
    def _compute_sale_count(self):
        sale = self.env['sale.order'].search([('contract_id', '=', self.id)])
        self.sale_count = len(sale)

    # def action_start_contract(self):
    #
    #     product_pack = self.env.ref('caps_nogaps.product_product_pack')
    #     product_carton = self.env.ref('caps_nogaps.product_product_carton')
    #     c_club_price = self.env['product.pricelist'].search([('id', '=', 13)])
    #
    #     # Configuration
    #     roundToWholeCarton = 0.75
    #     daysPerYear = 365
    #
    #     # Output Values
    #     deliveryCartons1_1 = 0
    #     deliveryPacks1_1 = 0
    #     deliveryCartons1_2 = 0
    #     deliveryPacks1_2 = 0
    #     deliveryCartons2 = 0
    #     deliveryCartons3 = 0
    #     deliveryCartons4 = 0
    #
    #     #################################
    #     # Do the initial calculations
    #     #
    #
    #     # The first period length is the remaining months of this calendar quarter
    #     if self.order_months % 3 == 0:
    #         lengthOfFirstPeriod = 3
    #     else:
    #         lengthOfFirstPeriod = self.order_months % 3
    #     print("lengthOfFirstPeriod:", lengthOfFirstPeriod)
    #
    #     # The number of periods remaining initially is how many delivery periods there are
    #     numPeriodsRemaining = math.ceil(self.order_months / 3)
    #     print("numPeriodsRemaining:", numPeriodsRemaining)
    #
    #     # Days per month
    #     daysPerMonth = daysPerYear / 12.0
    #     print("daysPerMonth:", daysPerMonth)
    #
    #     # Calculate the number of days in the first period
    #     daysInFirstPeriod = lengthOfFirstPeriod * daysPerMonth
    #     print("daysInFirstPeriod:", daysInFirstPeriod)
    #
    #     # Calculate Cartons and Bags to ship
    #     requiredPieces = (daysPerYear / 12.0) * self.pieces_per_daily_pack * self.num_daily_packs * self.order_months
    #     requiredCartons = requiredPieces / self.pieces_per_carton
    #     wholeCartons = int(requiredCartons)
    #     requiredBags = math.ceil(((requiredCartons - wholeCartons) * self.pieces_per_carton) / self.pieces_per_bag)
    #
    #
    #
    #     #create first delivry
    #
    #     # Round up bags to a whole carton if at or above the round-up threshold
    #     roundedUpToWholeCarton = False
    #     if requiredBags / (self.pieces_per_carton / self.pieces_per_bag) >= roundToWholeCarton:
    #         requiredBags = 0
    #         wholeCartons = wholeCartons + 1
    #         roundedUpToWholeCarton = True
    #
    #     # Helper variables for the shipping calculations
    #     daysPerCarton = self.pieces_per_carton / (self.pieces_per_daily_pack * self.num_daily_packs)
    #     if roundedUpToWholeCarton:
    #         daysInPacks = 0
    #     else:
    #         daysInPacks = requiredBags * self.pieces_per_bag / (self.pieces_per_daily_pack * self.num_daily_packs)
    #
    #     print("daysPerCarton:", daysPerCarton)
    #     # print("Required:",requiredCartons)
    #     # print("Sending:")
    #     # print("Cartons:",wholeCartons)
    #     # print("Bags   :",requiredBags)
    #
    #     #################################
    #     # NOW WE CALCULATE THE DELIVERIES
    #     #################################
    #
    #     #################################
    #     # Delivery   : 1.1
    #     # Send       : Now
    #     # Description: Send the customer a whole carton for them to try the product first
    #     #              If total is less than 1 whole carton then send all bags now
    #
    #     # print("wholeCartons:",wholeCartons)
    #
    #     if roundedUpToWholeCarton:
    #         deliveryCartons1_1 = 1
    #         deliveryPacks1_1 = 0
    #         daysInFirstDelivery = daysPerCarton
    #     else:
    #         if (wholeCartons > 0):
    #             deliveryCartons1_1 = 1
    #             deliveryPacks1_1 = 0
    #             daysInFirstDelivery = daysPerCarton
    #         else:
    #             deliveryCartons1_1 = 0
    #             deliveryPacks1_1 = requiredBags
    #             daysInFirstDelivery = daysInPacks
    #
    #     print("")
    #     print("##### DELIVERY 1.1 / NOW #####")
    #     print("Cartons:", deliveryCartons1_1)
    #     print("Packs  :", deliveryPacks1_1)
    #
    #     so = self.env['sale.order'].create({
    #         'partner_id': self.customer_id.id,
    #         'pricelist_id': c_club_price.id,
    #         'date_order': fields.Datetime.now(),
    #         'contract_id': self.id,
    #     })
    #     sol = self.env['sale.order.line'].create({
    #         'product_id': product_carton.id,
    #         'product_uom_qty': deliveryCartons1_1,
    #         'product_uom': 1,
    #         'order_id': so.id,
    #     })
    #     sol2 = self.env['sale.order.line'].create({
    #         'product_id': product_pack.id,
    #         'product_uom_qty': deliveryPacks1_1,
    #         'product_uom': 1,
    #         'order_id': so.id,
    #     })
    #     if so.order_line:
    #         for line in so.order_line:
    #             if line.product_uom_qty == 0:
    #                 line.unlink()
    #
    #     #################################
    #     # Delivery   : 1.2
    #     # Send       : 10 Days after delivery 1.1 has been received by the customer
    #     # Description: Send the customer the balance of their order for the first period
    #
    #     if deliveryCartons1_1 == 1:
    #         if (daysInFirstPeriod - daysPerCarton - daysInPacks) / daysPerCarton > 0:
    #             deliveryCartons1_2 = math.ceil((daysInFirstPeriod - daysPerCarton - daysInPacks) / daysPerCarton)
    #         else:
    #             deliveryCartons1_2 = 0
    #
    #         deliveryPacks1_2 = requiredBags
    #
    #     else:
    #         deliveryCartons1_2 = 0
    #         deliveryPacks1_2 = 0  # shipped in Delivery 1.1
    #
    #     print("##### DELIVERY 1.2 / 10 Days after Delivery 1.1 Received #####")
    #     print("Cartons:", deliveryCartons1_2)
    #     print("Packs  :", deliveryPacks1_2)
    #
    #     so = self.env['sale.order'].create({
    #         'partner_id': self.customer_id.id,
    #         'pricelist_id': c_club_price.id,
    #         'date_order': fields.Datetime.now(),
    #         'contract_id': self.id,
    #     })
    #     sol = self.env['sale.order.line'].create({
    #         'product_id': product_pack.id,
    #         'product_uom_qty': deliveryPacks1_2,
    #         'product_uom': 1,
    #         'order_id': so.id,
    #     })
    #     sol2 = self.env['sale.order.line'].create({
    #         'product_id': product_carton.id,
    #         'product_uom_qty': deliveryCartons1_2,
    #         'product_uom': 1,
    #         'order_id': so.id,
    #     })
    #     if so.order_line:
    #         for line in so.order_line:
    #             if line.product_uom_qty == 0:
    #                 line.unlink()
    #
    #     numPeriodsRemaining = numPeriodsRemaining - 1
    #
    #     #################################
    #     # Delivery   : 2
    #     # Send When  : At start of 2nd quarter for deliveries
    #     #              (either October 1st, January 1st or April 1st), this is
    #     #              usually 3 months later but depends when the deliveries start, e.g.
    #     #              if, say the order starts in the middle of a quarter (e.g. August)
    #     #              then Delivery 2 will be fewer than 3 months after Delivery 1
    #     # Description: Send the customer the stock they need for the second quarter
    #
    #     if numPeriodsRemaining > 0:
    #
    #         endPeriodDays = (3 + lengthOfFirstPeriod) * daysPerMonth
    #
    #         if numPeriodsRemaining > 0:
    #             if (endPeriodDays - daysPerCarton * (
    #                     (deliveryCartons1_1 + deliveryCartons1_2) - daysInPacks) / daysPerCarton) > 0:
    #                 deliveryCartons2 = math.ceil((endPeriodDays - daysPerCarton * (
    #                             deliveryCartons1_1 + deliveryCartons1_2) - daysInPacks) / daysPerCarton)
    #             else:
    #                 deliveryCartons2 = 0
    #         so = self.env['sale.order'].create({
    #             'partner_id': self.customer_id.id,
    #             'pricelist_id': c_club_price.id,
    #             'date_order': fields.Datetime.now(),
    #             'contract_id': self.id,
    #         })
    #         sol2 = self.env['sale.order.line'].create({
    #             'product_id': product_carton.id,
    #             'product_uom_qty': deliveryCartons2,
    #             'product_uom': 1,
    #             'order_id': so.id,
    #         })
    #
    #         numPeriodsRemaining = numPeriodsRemaining - 1
    #
    #         print("##### DELIVERY 2 / 3 Months After Delivery 1 #####")
    #         print("Cartons:", deliveryCartons2)
    #
    #     #################################
    #     # Delivery   : 3
    #     # Send       : At start of 3rd quarter, i.e. 3 months from Delivery 2
    #     # Description: Send the customer the stock they need for the third quarter
    #
    #     if numPeriodsRemaining > 0:
    #
    #         endPeriodDays = (6 + lengthOfFirstPeriod) * daysPerMonth
    #
    #         if numPeriodsRemaining > 0:
    #             if ((endPeriodDays - daysPerCarton * (
    #                     deliveryCartons1_1 + deliveryCartons1_2 + deliveryCartons2) - daysInPacks) / daysPerCarton) > 0:
    #                 deliveryCartons3 = math.ceil((endPeriodDays - daysPerCarton * (
    #                             deliveryCartons1_1 + deliveryCartons1_2 + deliveryCartons2) - daysInPacks) / daysPerCarton)
    #             else:
    #                 deliveryCartons3 = 0
    #
    #         so = self.env['sale.order'].create({
    #             'partner_id': self.customer_id.id,
    #             'pricelist_id': c_club_price.id,
    #             'date_order': fields.Datetime.now(),
    #             'contract_id': self.id,
    #         })
    #         sol2 = self.env['sale.order.line'].create({
    #             'product_id': product_carton.id,
    #             'product_uom_qty': deliveryCartons3,
    #             'product_uom': 1,
    #             'order_id': so.id,
    #         })
    #
    #         numPeriodsRemaining = numPeriodsRemaining - 1
    #
    #         print("##### DELIVERY 3 / 3 Months After Delivery 2 #####")
    #         print("Cartons:", deliveryCartons3)
    #
    #     #################################
    #     # Delivery   : 4
    #     # Send       : At start of 4th quarter, i.e. 3 months from Delivery 3
    #     # Description: Send the customer the stock they need for the fourth quarter
    #
    #     if numPeriodsRemaining > 0:
    #
    #         endPeriodDays = (9 + lengthOfFirstPeriod) * daysPerMonth
    #
    #         if numPeriodsRemaining > 0:
    #             if ((endPeriodDays - daysPerCarton * (
    #                     deliveryCartons1_1 + deliveryCartons1_2 + deliveryCartons2 + deliveryCartons3) - daysInPacks) / daysPerCarton) > 0:
    #                 deliveryCartons4 = math.ceil((endPeriodDays - daysPerCarton * (
    #                             deliveryCartons1_1 + deliveryCartons1_2 + deliveryCartons2 + deliveryCartons3) - daysInPacks) / daysPerCarton)
    #             else:
    #                 deliveryCartons4 = 0
    #
    #         so = self.env['sale.order'].create({
    #             'partner_id': self.customer_id.id,
    #             'pricelist_id': c_club_price.id,
    #             'date_order': fields.Datetime.now(),
    #             'contract_id': self.id,
    #         })
    #         sol2 = self.env['sale.order.line'].create({
    #             'product_id': product_carton.id,
    #             'product_uom_qty': deliveryCartons4,
    #             'product_uom': 1,
    #             'order_id': so.id,
    #         })
    #
    #         numPeriodsRemaining = numPeriodsRemaining - 1
    #
    #         print("##### DELIVERY 4 / 3 Months After Delivery 3 #####")
    #         print("Cartons:", deliveryCartons4)
    #
    #
    #
    #
    #
    #
    #
    #     self.state = "start"

    def action_start_contract(self):
        product_dic = {}
        if self.product_ids:
            for line in self.product_ids:
                # product_carton = self.env.ref('caps_nogaps.product_product_carton')
                # c_club_price = self.env['product.pricelist'].search([('id', '=', 13)])

                # Configuration
                roundToWholeCarton = 0.75
                daysPerYear = 365
                CAPSFundingTotal = line.total_funding
                fundingTotal = self.order_months * CAPSFundingTotal / 12

                # Output Values
                deliveryCartons1_1 = 0
                deliveryPacks1_1 = 0
                deliveryCartons1_2 = 0
                deliveryPacks1_2 = 0
                deliveryCartons2 = 0
                deliveryCartons3 = 0
                deliveryCartons4 = 0

                #################################
                # Do the initial calculations
                #

                # The first period length is the remaining months of this calendar quarter
                if self.order_months % 3 == 0:
                    lengthOfFirstPeriod = 3
                else:
                    lengthOfFirstPeriod = self.order_months % 3
                print("lengthOfFirstPeriod:", lengthOfFirstPeriod)

                # The number of periods remaining initially is how many delivery periods there are
                numPeriodsRemaining = math.ceil(self.order_months / 3)
                print("numPeriodsRemaining:", numPeriodsRemaining)

                # Days per month
                daysPerMonth = daysPerYear / 12.0
                print("daysPerMonth:", daysPerMonth)

                # Calculate the number of days in the first period
                daysInFirstPeriod = lengthOfFirstPeriod * daysPerMonth
                print("daysInFirstPeriod:", daysInFirstPeriod)
                third_delivry_date = self.start_date + timedelta(math.ceil(daysInFirstPeriod))

                # Calculate Cartons and Bags to ship
                requiredPieces = (daysPerYear / 12.0) * line.pieces_per_daily_pack * line.num_daily_packs * self.order_months
                requiredCartons = requiredPieces / line.pieces_per_carton
                wholeCartons = int(requiredCartons)
                requiredBags = math.ceil(((requiredCartons - wholeCartons) * line.pieces_per_carton) / line.pieces_per_bag)



                #create first delivry

                # Round up bags to a whole carton if at or above the round-up threshold
                roundedUpToWholeCarton = False
                if requiredBags / (line.pieces_per_carton / line.pieces_per_bag) >= roundToWholeCarton:
                    requiredBags = 0
                    wholeCartons = wholeCartons + 1
                    roundedUpToWholeCarton = True

                # Helper variables for the shipping calculations
                daysPerCarton = line.pieces_per_carton / (line.pieces_per_daily_pack * line.num_daily_packs)
                if roundedUpToWholeCarton:
                    daysInPacks = 0
                else:
                    daysInPacks = requiredBags * line.pieces_per_bag / (line.pieces_per_daily_pack * line.num_daily_packs)

                print("daysPerCarton:", daysPerCarton)
                # print("Required:",requiredCartons)
                # print("Sending:")
                # print("Cartons:",wholeCartons)
                # print("Bags   :",requiredBags)

                # Calculate the sell price per bag and sell price per carton
                sellPricePerBag = CAPSFundingTotal / (requiredBags + wholeCartons * (line.pieces_per_carton / line.pieces_per_bag))
                sellPricePerCarton = sellPricePerBag * (line.pieces_per_carton / line.pieces_per_bag)
                price_per_pack = sellPricePerBag
                price_per_carton = sellPricePerCarton

                print("Bag Sell Price: ", sellPricePerBag)
                print("Carton Sell Price: ", sellPricePerCarton)

                #################################
                # NOW WE CALCULATE THE DELIVERIES
                #################################

                #################################
                # Delivery   : 1.1
                # Send       : Now
                # Description: Send the customer a whole carton for them to try the product first
                #              If total is less than 1 whole carton then send all bags now

                # print("wholeCartons:",wholeCartons)

                if roundedUpToWholeCarton:
                    deliveryCartons1_1 = 1
                    deliveryPacks1_1 = 0
                    daysInFirstDelivery = daysPerCarton
                else:
                    if (wholeCartons > 0):
                        deliveryCartons1_1 = 1
                        deliveryPacks1_1 = 0
                        daysInFirstDelivery = daysPerCarton
                    else:
                        deliveryCartons1_1 = 0
                        deliveryPacks1_1 = requiredBags
                        daysInFirstDelivery = daysInPacks

                print("")
                print("##### DELIVERY 1.1 / NOW #####")
                print("Cartons:", deliveryCartons1_1)
                print("Packs  :", deliveryPacks1_1)
                if self.start_date in list(product_dic.keys()):
                    product_dic[self.start_date].append([line.product_pack_id.product_id.id, deliveryPacks1_1, sellPricePerBag,line.product_pack_id.product_id.uom_id.id])
                    product_dic[self.start_date].append([line.product_carton_id.id, deliveryCartons1_1, sellPricePerCarton, line.product_carton_id.uom_id.id])
                else:
                    product_dic[self.start_date] = [[line.product_pack_id.product_id.id, deliveryPacks1_1, sellPricePerBag,line.product_pack_id.product_id.uom_id.id], [line.product_carton_id.id,deliveryCartons1_1, sellPricePerCarton, line.product_carton_id.uom_id.id]]

                # so = self.env['sale.order'].create({
                #     'partner_id': self.customer_id.id,
                #     # 'pricelist_id': c_club_price.id,
                #     'date_order': fields.Datetime.now(),
                #     'contract_id': self.id,
                # })
                # sol = self.env['sale.order.line'].create({
                #     'product_id': line.product_carton_id.id,
                #     'product_uom_qty': deliveryCartons1_1,
                #     'product_uom': 1,
                #     'order_id': so.id,
                # })
                # sol2 = self.env['sale.order.line'].create({
                #     'product_id': line.product_pack_id.id,
                #     'product_uom_qty': deliveryPacks1_1,
                #     'product_uom': 1,
                #     'order_id': so.id,
                # })
                # if so.order_line:
                #     for so_line in so.order_line:
                #         if so_line.product_uom_qty == 0:
                #             so_line.unlink()

                #################################
                # Delivery   : 1.2
                # Send       : 10 Days after delivery 1.1 has been received by the customer
                # Description: Send the customer the balance of their order for the first period

                if deliveryCartons1_1 == 1:
                    if (daysInFirstPeriod - daysPerCarton - daysInPacks) / daysPerCarton > 0:
                        deliveryCartons1_2 = math.ceil((daysInFirstPeriod - daysPerCarton - daysInPacks) / daysPerCarton)
                    else:
                        deliveryCartons1_2 = 0

                    deliveryPacks1_2 = requiredBags

                else:
                    deliveryCartons1_2 = 0
                    deliveryPacks1_2 = 0  # shipped in Delivery 1.1

                print("##### DELIVERY 1.2 / 10 Days after Delivery 1.1 Received #####")
                print("Cartons:", deliveryCartons1_2)
                print("Packs  :", deliveryPacks1_2)
                if self.start_date + timedelta(10) in list(product_dic.keys()):
                    product_dic[self.start_date + timedelta(10)].append([line.product_pack_id.product_id.id, deliveryPacks1_2, sellPricePerBag,line.product_pack_id.product_id.uom_id.id])
                    product_dic[self.start_date + timedelta(10)].append([line.product_carton_id.id, deliveryCartons1_2, sellPricePerCarton,line.product_carton_id.uom_id.id])
                else:
                    product_dic[self.start_date + timedelta(10)] = [[line.product_pack_id.product_id.id, deliveryPacks1_2, sellPricePerBag,line.product_pack_id.product_id.uom_id.id], [line.product_carton_id.id, deliveryCartons1_2, sellPricePerCarton,line.product_carton_id.uom_id.id]]

                # so = self.env['sale.order'].create({
                #     'partner_id': self.customer_id.id,
                #     # 'pricelist_id': c_club_price.id,
                #     'date_order': datetime.now() + timedelta(10),
                #     'contract_id': self.id,
                # })
                # sol = self.env['sale.order.line'].create({
                #     'product_id': line.product_carton_id.id,
                #     'product_uom_qty': deliveryCartons1_2,
                #     'product_uom': 1,
                #     'order_id': so.id,
                # })
                # sol2 = self.env['sale.order.line'].create({
                #     'product_id': line.product_pack_id.id,
                #     'product_uom_qty': deliveryPacks1_2,
                #     'product_uom': 1,
                #     'order_id': so.id,
                # })
                # if so.order_line:
                #     for so_line in so.order_line:
                #         if so_line.product_uom_qty == 0:
                #             so_line.unlink()

                numPeriodsRemaining = numPeriodsRemaining - 1

                #################################
                # Delivery   : 2
                # Send When  : At start of 2nd quarter for deliveries
                #              (either October 1st, January 1st or April 1st), this is
                #              usually 3 months later but depends when the deliveries start, e.g.
                #              if, say the order starts in the middle of a quarter (e.g. August)
                #              then Delivery 2 will be fewer than 3 months after Delivery 1
                # Description: Send the customer the stock they need for the second quarter

                if numPeriodsRemaining > 0:

                    endPeriodDays = (3 + lengthOfFirstPeriod) * daysPerMonth

                    if numPeriodsRemaining > 0:
                        if (endPeriodDays - daysPerCarton * (
                                (deliveryCartons1_1 + deliveryCartons1_2) - daysInPacks) / daysPerCarton) > 0:
                            deliveryCartons2 = math.ceil((endPeriodDays - daysPerCarton * (
                                        deliveryCartons1_1 + deliveryCartons1_2) - daysInPacks) / daysPerCarton)
                        else:
                            deliveryCartons2 = 0
                    # so = self.env['sale.order'].create({
                    #     'partner_id': self.customer_id.id,
                    #     # 'pricelist_id': c_club_price.id,
                    #     'date_order':  datetime.now() + timedelta(endPeriodDays),
                    #     'contract_id': self.id,
                    # })
                    # sol2 = self.env['sale.order.line'].create({
                    #     'product_id': line.product_carton_id.id,
                    #     'product_uom_qty': deliveryCartons2,
                    #     'product_uom': 1,
                    #     'order_id': so.id,
                    # })
                    if self.start_date + timedelta(math.ceil(daysInFirstPeriod)) in list(product_dic.keys()):
                        product_dic[self.start_date + timedelta(math.ceil(daysInFirstPeriod))].append([line.product_carton_id.id, deliveryCartons2, sellPricePerCarton,line.product_carton_id.uom_id.id])
                    else:

                        product_dic[self.start_date + timedelta(math.ceil(daysInFirstPeriod))] = [[line.product_carton_id.id, deliveryCartons2, sellPricePerCarton,line.product_carton_id.uom_id.id]]

                    numPeriodsRemaining = numPeriodsRemaining - 1

                    print("##### DELIVERY 2 / 3 Months After Delivery 1 #####")
                    print("Cartons:", deliveryCartons2)

                #################################
                # Delivery   : 3
                # Send       : At start of 3rd quarter, i.e. 3 months from Delivery 2
                # Description: Send the customer the stock they need for the third quarter

                if numPeriodsRemaining > 0:

                    endPeriodDays = (6 + lengthOfFirstPeriod) * daysPerMonth

                    if numPeriodsRemaining > 0:
                        if ((endPeriodDays - daysPerCarton * (
                                deliveryCartons1_1 + deliveryCartons1_2 + deliveryCartons2) - daysInPacks) / daysPerCarton) > 0:
                            deliveryCartons3 = math.ceil((endPeriodDays - daysPerCarton * (
                                        deliveryCartons1_1 + deliveryCartons1_2 + deliveryCartons2) - daysInPacks) / daysPerCarton)
                        else:
                            deliveryCartons3 = 0

                    # so = self.env['sale.order'].create({
                    #     'partner_id': self.customer_id.id,
                    #     # 'pricelist_id': c_club_price.id,
                    #     'date_order': datetime.now() + timedelta(endPeriodDays),
                    #     'contract_id': self.id,
                    # })
                    # sol2 = self.env['sale.order.line'].create({
                    #     'product_id': line.product_carton_id.id,
                    #     'product_uom_qty': deliveryCartons3,
                    #     'product_uom': 1,
                    #     'order_id': so.id,
                    # })
                    # endPeriodDays = 6 * int(daysPerMonth)
                    next_order_date = third_delivry_date + relativedelta(months=3)
                    if next_order_date.day > 1:
                        next_order_date = next_order_date.replace(day=1)
                    if next_order_date in list(product_dic.keys()):
                        product_dic[next_order_date].append([line.product_carton_id.id,deliveryCartons3, sellPricePerCarton,line.product_carton_id.uom_id.id])
                    else:
                        product_dic[next_order_date] = [[line.product_carton_id.id,deliveryCartons3, sellPricePerCarton,line.product_carton_id.uom_id.id]]

                    numPeriodsRemaining = numPeriodsRemaining - 1

                    print("##### DELIVERY 3 / 3 Months After Delivery 2 #####")
                    print("Cartons:", deliveryCartons3)

                #################################
                # Delivery   : 4
                # Send       : At start of 4th quarter, i.e. 3 months from Delivery 3
                # Description: Send the customer the stock they need for the fourth quarter

                if numPeriodsRemaining > 0:

                    endPeriodDays = (9 + lengthOfFirstPeriod) * daysPerMonth

                    if numPeriodsRemaining > 0:
                        if ((endPeriodDays - daysPerCarton * (
                                deliveryCartons1_1 + deliveryCartons1_2 + deliveryCartons2 + deliveryCartons3) - daysInPacks) / daysPerCarton) > 0:
                            deliveryCartons4 = math.ceil((endPeriodDays - daysPerCarton * (
                                        deliveryCartons1_1 + deliveryCartons1_2 + deliveryCartons2 + deliveryCartons3) - daysInPacks) / daysPerCarton)
                        else:
                            deliveryCartons4 = 0

                    # so = self.env['sale.order'].create({
                    #     'partner_id': self.customer_id.id,
                    #     # 'pricelist_id': c_club_price.id,
                    #     'date_order': datetime.now() + timedelta(endPeriodDays),
                    #     'contract_id': self.id,
                    # })
                    # sol2 = self.env['sale.order.line'].create({
                    #     'product_id': line.product_carton_id.id,
                    #     'product_uom_qty': deliveryCartons4,
                    #     'product_uom': 1,
                    #     'order_id': so.id,
                    # })
                    # endPeriodDays = 9 * int(daysPerMonth)
                    next_order_date = third_delivry_date + relativedelta(months=6)
                    if next_order_date.day > 1:
                        next_order_date = next_order_date.replace(day=1)
                    if next_order_date in list(product_dic.keys()):
                        product_dic[next_order_date].append([line.product_carton_id.id,deliveryCartons4, sellPricePerCarton,line.product_carton_id.uom_id.id])
                    else:
                        product_dic[next_order_date] = [[line.product_carton_id.id,deliveryCartons4, sellPricePerCarton,line.product_carton_id.uom_id.id]]

                    numPeriodsRemaining = numPeriodsRemaining - 1

                    print("##### DELIVERY 4 / 3 Months After Delivery 3 #####")
                    print("Cartons:", deliveryCartons4)
            shipment_pro = self.env['product.product'].search([('default_code', '=', 'shopifyshippingproduct')])
            for key in product_dic:
                so = self.env['sale.order'].create({
                    'partner_id': self.customer_id.id,
                    'date_order': key,
                    'contract_id': self.id,
                    'company_id': self.company_id.id,
                })
                if key == self.start_date:
                    sol = self.env['sale.order.line'].create({
                        'product_id': shipment_pro.id,
                        'product_uom_qty': 1,
                        'price_unit': self.shipment_price,
                        'product_uom': shipment_pro.uom_id.id,
                        'order_id': so.id,
                        'company_id': self.company_id.id,
                    })
                    # sol._onchange_qty()
                for line in product_dic[key]:
                    if line[1]:
                        sol = self.env['sale.order.line'].create({
                                'product_id': line[0],
                                'product_uom_qty': line[1],
                                'price_unit': line[2],
                                'product_uom': line[3],
                                'order_id': so.id,
                        })
                #     # sol._onchange_qty()
                # if so.order_line:
                #     for so_line in so.order_line:
                #         if so_line.product_uom_qty == 0:
                #             so_line.unlink()
        self.state = "start"

    # def _compute_order_months(self):
    #     for line in self:
    #          months = relativedelta.relativedelta(line.end_date, line.start_date).months
    #
    #          line.order_months = months

    # def action_modify_contract(self):
    #
    #     self.state = "modified"