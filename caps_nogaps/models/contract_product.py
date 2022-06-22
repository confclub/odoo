# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ContractProduct(models.Model):
    _name = 'contract.product'

    contract_id = fields.Many2one('cap.contract')
    product_pack_id = fields.Many2one('cap.no.gap')
    product_carton_id = fields.Many2one('variant.package', string='Carton')
    description = fields.Char()
    pieces_per_carton = fields.Integer( help='how many pieces of the product are in a whole carton')
    pieces_per_bag = fields.Integer(help='how many pieces of the product that are in a single bag')
    pieces_per_daily_pack = fields.Float(help='how many pieces of this product are in a single daily pack')
    num_daily_packs = fields.Integer(default=1, readonly=1, help='how many daily packs of this product are in the order (their deliveries are combined for efficiency)')
    total_funding = fields.Float()


