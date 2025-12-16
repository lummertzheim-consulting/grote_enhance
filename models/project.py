# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.addons.grote_enhance.utils.common import get_calendar_week


class Project(models.Model):
    _inherit = 'project.project'

    kw = fields.Selection(string='KW', selection=get_calendar_week())

    @api.model_create_multi
    def create(self, vals_list):
        result = super(Project, self).create(vals_list)
        users_to_share = self.env['res.users'].sudo().search([('is_internal_portal_user', '=', True)])
        if users_to_share.exists():
            for res in result:
                res._add_followers(users_to_share.mapped('partner_id'))
                res._add_collaborators(users_to_share.mapped('partner_id'), limited_access=True)
                # for collab in res.collaborator_ids:
                #     collab.limited_access = True
        return result
    