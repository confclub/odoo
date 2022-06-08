
import json
import logging
import pytz
import time

from datetime import datetime
from dateutil import parser

from odoo import models, fields, api, _


class StockMoveInherit(models.Model):
    _inherit = 'stock.move'


    shopify_refund_id = fields.Char()