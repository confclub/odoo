# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ContractAttach(models.Model):
    _name = 'contract.attachment'

    contract_id = fields.Many2one('cap.contract')
    description = fields.Char()
    attachment_ids = fields.Many2many('ir.attachment', '', string='Attachments')
