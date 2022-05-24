# -*- coding: utf-8 -*-

import threading
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ContractWizard(models.TransientModel):
    _name = 'cap.contract.wizard'

    reason = fields.Text()
    contract_id = fields.Many2one('cap.contract')




    def Reason_contract_cancel(self):
        self.contract_id.reason = self.reason
        self.contract_id.state = "cancel"


