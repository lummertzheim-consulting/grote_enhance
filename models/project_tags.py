# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ProjectTags(models.Model):
    _inherit = 'project.tags'


    employee_id = fields.Many2one('hr.employee', string='Mitarbeiter')





