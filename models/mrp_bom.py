# -*- coding: utf-8 -*-

from odoo import fields, models


class MrpBomInherit(models.Model):
    _inherit = "mrp.bom"

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')


class MrpBomLineInherit(models.Model):
    _inherit = "mrp.bom.line"

    description = fields.Text(string='Description')