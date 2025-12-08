# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
from odoo.addons.grote_enhance.utils.common import get_calendar_week
from odoo.addons.project.models.project_task import PROJECT_TASK_WRITABLE_FIELDS
from odoo.osv import expression


PROJECT_TASK_WRITABLE_FIELDS.add('timesheet_ids')

def get_iso_year_and_week_offset(start_date, offset_weeks):
    target_date = start_date + timedelta(weeks=offset_weeks)
    iso_year, iso_week, _ = target_date.isocalendar()
    return str(iso_week), iso_year


class ProjectTask(models.Model):
    _inherit = 'project.task'


    kw = fields.Selection(string='KW', selection=get_calendar_week())
    task_employee_capacity = fields.One2many('task.employee.capacity', 'task_id', string='Task Employee Capacity')

    def update_tag_in_capacity(self):
        for tag_id in self.tag_ids:
            task_employee_capacity_id = self.env['task.employee.capacity'].search([('task_id', '=', self.id), ('tag_id', '=', tag_id.id)])
            if not task_employee_capacity_id:
                task_employee_capacity_id = self.env['task.employee.capacity'].create({
                    'task_id': self.id,
                    'tag_id': tag_id.id,
                })
        remove_capacity_ids = self.env['task.employee.capacity'].search([('task_id', '=', self.id), ('tag_id', 'not in', self.tag_ids.ids)])
        remove_capacity_ids.sudo().unlink()
        self.update_hrs_in_capacity()
        

    def update_hrs_in_capacity(self):
        if self.tag_ids:
            task_employee_not_zero_capacity_ids = self.env['task.employee.capacity'].search(
                [('task_id', '=', self.id), ('tag_id', 'in', self.tag_ids.ids), ('hours', '!=', 0)])
            total_hours = sum(task_employee_not_zero_capacity_ids.mapped('hours'))
            task_employee_zero_capacity_ids = self.env['task.employee.capacity'].search(
                [('task_id', '=', self.id), ('tag_id', 'in', self.tag_ids.ids), ('hours', '=', 0)])
            if total_hours < self.allocated_hours and task_employee_zero_capacity_ids:
                remaining_hrs = self.allocated_hours - total_hours
                per_line_remaining_hrs = remaining_hrs / len(task_employee_zero_capacity_ids) or 1
                task_employee_zero_capacity_ids.write({'hours': per_line_remaining_hrs})


    @api.model_create_multi
    def create(self, vals_list):
        result = super(ProjectTask, self).create(vals_list)
        for res in result:
            if res.tag_ids:
                res.update_tag_in_capacity()
            if res.task_employee_capacity:
                    res.kw = res.task_employee_capacity[0].kw
        return result

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        if 'tag_ids' in vals:
            for task in self:
                task.update_tag_in_capacity()
                for capa in task.task_employee_capacity:
                    capa.action_check_with_kw()
        if 'task_employee_capacity' in vals or 'tag_ids' in vals:
            for task in self:
                if task.task_employee_capacity:
                    task.kw = task.task_employee_capacity[0].kw
        return res



class TaskEmployeeCapacity(models.Model):
    _name = 'task.employee.capacity'
    _description = 'Task Employee Capacity'

    def write(self, vals):
        res = super(TaskEmployeeCapacity, self).write(vals)
        if 'hours' in vals:
            for task in self:
                task.task_id.update_hrs_in_capacity()
        return res

    task_id = fields.Many2one('project.task', string='Task', ondelete='cascade')
    tag_id = fields.Many2one('project.tags', string='Kapazität')
    hours = fields.Float(string='Hours')
    kw = fields.Selection(string='KW', selection=get_calendar_week())

    def action_check_with_kw(self):
        remaining_capacity = self.hours or 40.0  # fallback to 40 hrs/week
        week_offset = 0
        today = date.today()
        available_weeks = []
        if self.tag_id.employee_id:
            while remaining_capacity > 0:  # avoid infinite loop
                kw, year = get_iso_year_and_week_offset(today, week_offset)
                task_capacity_ids = self.search([
                    ('tag_id.employee_id', '=', self.tag_id.employee_id.id),
                    ('task_id.stage_id', '!=', 'Abgeschlossen'),
                    # ('task_id', '!=', self.task_id.id),
                    ('task_id.kw', '=', kw)
                ])
                planned_working_time_week = sum(task_capacity_ids.mapped('hours'))
                planned_working_time_week = self.tag_id.employee_id.target_work_hours_week - planned_working_time_week
                remaining_capacity -= planned_working_time_week
                if remaining_capacity != 0.0:
                    available_weeks.append((year, kw, remaining_capacity))
                week_offset += 1
        if available_weeks:
           self.kw = available_weeks[-1][1]
