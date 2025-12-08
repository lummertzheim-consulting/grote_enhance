# -*- coding: utf-8 -*-

from odoo import fields, models


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    is_visible_portal_user = fields.Boolean(string="Visible to Portal User", copy=False)