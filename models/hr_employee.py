# -*- coding: utf-8 -*-

from odoo import fields, models, api
import lxml.etree as ET
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta, time
from odoo.tools import float_round
from odoo.addons.grote_enhance.utils.common import get_calendar_week, get_current_week_date_range, get_week_dates


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.depends_context('append_type_to_tax_name')
    def _compute_get_current_week(self):
        for rec in self:
            today = date.today()
            iso_week = today.isocalendar().week
            rec.kw = str(iso_week)

    @api.depends('kw')
    def _compute_on_working_time(self):
        for rec in self:
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', rec.kw)])
            rec.planned_working_time_week = sum(task_capacity_ids.mapped('hours'))

    def _compute_on_planned_capacity(self):
        for rec in self:
            rec.planned_capacity = (rec.planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

    @api.depends('kw')
    def _compute_on_absence_week(self):
        for rec in self:
            total_hours = 0.0
            calendar = rec.resource_calendar_id

            if not calendar or not rec.resource_id:
                rec.absence_week = 0.0
                continue

            week_start, week_end = get_current_week_date_range(new_iso_week=int(rec.kw))
            week_start_dt = datetime.combine(week_start, datetime.min.time())
            week_end_dt = datetime.combine(week_end, datetime.max.time())

            # Get leaves approved and overlapping with this week
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', rec.id),
                ('state', '=', 'validate'),
                ('date_to', '>=', week_start_dt),
                ('date_from', '<=', week_end_dt),
            ])

            for leave in leaves:
                # Clip to week boundaries
                leave_start = max(leave.date_from, week_start_dt)
                leave_end = min(leave.date_to, week_end_dt)

                # Get actual working hours in this time window
                work_data = calendar.get_work_hours_count(
                    leave_start,
                    leave_end,
                    compute_leaves=False
                )
                # remaining_days = leave_start - leave_end
                leave_hours = work_data
                total_hours += leave_hours

            rec.absence_week = round(total_hours, 2)

    @api.depends('kw')
    def _compute_on_actual_working_hours_week(self):
        for rec in self:
            task_timesheet_ids = self.env['account.analytic.line'].search([('employee_id', '=', rec.id),
                                                                           ('task_id', '!=', False),
                                                                           ('task_id.stage_id', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', rec.kw)])
            rec.actual_working_hours_week = sum(task_timesheet_ids.mapped('unit_amount'))

    def _compute_on_actual_working_capacity(self):
        for rec in self:
            rec.actual_working_capacity = (rec.actual_working_hours_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)


    def _get_on_actual_leave_public(self, weeks=0):
        # for rec in self:
        today = fields.Date.today()
            
        today_date = today + timedelta(weeks=weeks)

        # Get ISO week (1–7, Monday–Sunday)
        iso_weekday = today_date.isoweekday()

        # Get first and last date of that ISO week
        week_start = today_date - timedelta(days=iso_weekday - 1)  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        calendar = self.resource_calendar_id
        # 1️⃣ Public holidays from resource.calendar.leaves
        public_holidays = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id),
            ('resource_id', '=', False),
            ('date_from', '<=', datetime.combine(week_end, time.max)),
            ('date_to', '>=', datetime.combine(week_start, time.min)),
        ])

        # Total hours from public holidays
        public_holiday_hours = 0.0
        for holiday in public_holidays:
            public_holiday_hours += calendar.get_work_hours_count(
                holiday.date_from, holiday.date_to, compute_leaves=False
            )
        
        # 2️⃣ Employee personal leaves (hr.leave)
        employee_leaves = self.env['hr.leave'].search([
            ('employee_id', '=', self.id),
            ('state', '=', 'validate'),
            ('request_date_from', '<=', week_end),
            ('request_date_to', '>=', week_start),
        ])

        employee_leave_hours = sum(employee_leaves.mapped('number_of_hours'))

        # ✅ Combined total leave + public holiday hours
        total_leave_hours = public_holiday_hours + employee_leave_hours

        return total_leave_hours



    kw = fields.Selection(string='KW', selection=get_calendar_week(), compute='_compute_get_current_week', store=True, readonly=False)
    target_work_hours_week = fields.Float(related='resource_calendar_id.full_time_required_hours', string='Soll-Arbeitszeit / Woche', store=True)
    # target_work_hours_week = fields.Float(string='Soll-Arbeitszeit / Woche')
    planned_working_time_week = fields.Float(string='geplante-Arbeitszeit / Woche', compute='_compute_on_working_time')
    planned_capacity = fields.Float(string='geplante Auslastung', compute='_compute_on_planned_capacity')
    absence_week = fields.Float(string='Abwesenheit / Woche', compute='_compute_on_absence_week')
    actual_working_hours_week = fields.Float(string='Ist-Arbeitszeit / Woche', compute='_compute_on_actual_working_hours_week')
    actual_working_capacity = fields.Float(string='tatsächliche Auslastung', compute='_compute_on_actual_working_capacity')


    def action_update_next_week(self, week=1):
        today = date.today()
        # Add the number of weeks (week * 7 days)
        target_date = today + timedelta(weeks=week)
        # Get ISO week number from the target date
        iso_week = target_date.isocalendar().week
        self.kw = str(iso_week)


    def _get_soll_project_hours(self, week_name, year):
        self.ensure_one()  # assume single employee/record
        week_start, week_end = get_week_dates(week_name, year)
        calendar = self.resource_calendar_id

        # 1️⃣ Public holidays from resource.calendar.leaves
        public_holidays = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id),
            ('resource_id', '=', False),
            ('date_from', '<=', datetime.combine(week_end, time.max)),
            ('date_to', '>=', datetime.combine(week_start, time.min)),
        ])

        # Total hours from public holidays
        public_holiday_hours = 0.0
        for holiday in public_holidays:
            public_holiday_hours += calendar.get_work_hours_count(
                holiday.date_from, holiday.date_to, compute_leaves=False
            )

        # 2️⃣ Employee personal leaves (hr.leave)
        employee_leaves = self.env['hr.leave'].search([
                ('employee_id', '=', self.id), 
                ('state', '=', 'validate'), 
                ('request_date_from', '<=', week_end), 
                ('request_date_to', '>=', week_start)]) 
        employee_leave_hours = sum(employee_leaves.mapped('number_of_hours'))

        # ✅ Combined total leave + public holiday hours
        total_leave_hours = public_holiday_hours + employee_leave_hours

        return total_leave_hours

    