# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.osv import expression  # noqa: PLE0401
from odoo.tools import format_list
from odoo.tools.translate import _
from odoo.addons.hr_timesheet.models.hr_timesheet import AccountAnalyticLine as AccountAnalyticLineExt
from datetime import datetime
from babel.dates import format_date

def _check_can_write(self, values):
    # If it's a basic user then check if the timesheet is his own.
    if self.env.user.has_group('base.group_portal'):
        for analytic_line in self:
            if analytic_line.employee_id.user_id != self.env.user:
                raise AccessError(_("You cannot access timesheets that are not yours."))
    elif (
            not (self.env.user.has_group('hr_timesheet.group_hr_timesheet_approver') or self.env.user.has_group
                ('base.group_portal') or self.env.su)
            and any(analytic_line.user_id != self.env.user for analytic_line in self)
    ):
        raise AccessError(_("You cannot access timesheets that are not yours."))


AccountAnalyticLineExt._check_can_write = _check_can_write


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    week_name = fields.Char(string="Week", compute="_compute_date_groups", store=True, index=True)
    month_name = fields.Char(string="Month", compute="_compute_date_groups", store=True, index=True)
    year = fields.Integer(string="Year", compute="_compute_date_groups", store=True, index=True)

    @api.depends('date')
    def _compute_date_groups(self):
        for task in self:
            if task.date:
                date = fields.Datetime.from_string(task.date).date()
                year, week, _ = date.isocalendar()
                task.year = year
                task.week_name = f"KW{week}" 
                task.month_name = format_date(task.date, "LLLL yyyy", locale="de_DE")                
            else:
                task.week_name = False
                task.month_name = False
                task.year = False

    @api.model
    def default_get(self, field_list):
        result = super(AccountAnalyticLine, self).default_get(field_list)
        if self.env.user.has_group('base.group_portal'):
            result['employee_id'] = self.env['hr.employee'].search([('work_email', '=', self.env.user.login)], limit=1).id
        return result


    def _timesheet_get_portal_domain(self):
        """ Only the timesheets with a product invoiced on delivered quantity are concerned.
            since in ordered quantity, the timesheet quantity is not invoiced,
            thus there is no meaning of showing invoice with ordered quantity.
        """
        domain = super()._timesheet_get_portal_domain()
        if self.env.user.has_group('base.group_portal'):
            return expression.AND([domain, [('employee_id.user_id', '=', self.env.user.id)]])
        return domain