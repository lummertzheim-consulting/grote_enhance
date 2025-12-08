# -*- coding: utf-8 -*-
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    is_internal_portal_user = fields.Boolean(string="Internal Portal User", default=False)
