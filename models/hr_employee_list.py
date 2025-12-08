# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
from odoo.addons.grote_enhance.utils.common import get_calendar_week, get_current_week_date_range


class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    def read(self, fields=None, load='_classic_read'):
        """ Override to explicitely call check_access(), that is not called
            by the ORM. It instead directly fetches ir.rules and apply them. """
        if self.env.context.get('from_utilization', False):
            self.action_update_planned_capacity()
        return super(HrEmployee, self).read(fields=fields, load=load)

    def action_update_planned_capacity(self):
        for rec in self:
            today = date.today()
            # planned_capacity_min_one
            # Add the number of weeks (week * 7 days)
            target_date = today + timedelta(weeks=-1)
            total_leaves = rec._get_on_actual_leave_public(weeks=-1)
            # Get ISO week number from the target date
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves
            rec.planned_capacity_min_one = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_current
            total_leaves = rec._get_on_actual_leave_public(weeks=0)
            target_date = today + timedelta(weeks=0)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_current = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_pluse_1
            total_leaves = rec._get_on_actual_leave_public(weeks=1)
            target_date = today + timedelta(weeks=1)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_1 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_pluse_2
            total_leaves = rec._get_on_actual_leave_public(weeks=2)
            target_date = today + timedelta(weeks=2)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_2 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)


            # planned_capacity_pluse_3
            total_leaves = rec._get_on_actual_leave_public(weeks=3)
            target_date = today + timedelta(weeks=3)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_3 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_pluse_4
            total_leaves = rec._get_on_actual_leave_public(weeks=4)
            target_date = today + timedelta(weeks=4)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_4 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_pluse_5
            total_leaves = rec._get_on_actual_leave_public(weeks=5)
            target_date = today + timedelta(weeks=5)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_5 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_pluse_6
            total_leaves = rec._get_on_actual_leave_public(weeks=6)
            target_date = today + timedelta(weeks=6)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_6 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_pluse_7
            total_leaves = rec._get_on_actual_leave_public(weeks=7)
            target_date = today + timedelta(weeks=7)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_7 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_pluse_8
            total_leaves = rec._get_on_actual_leave_public(weeks=8)
            target_date = today + timedelta(weeks=8)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_8 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_pluse_9
            total_leaves = rec._get_on_actual_leave_public(weeks=9)
            target_date = today + timedelta(weeks=9)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_9 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)

            # planned_capacity_pluse_10
            total_leaves = rec._get_on_actual_leave_public(weeks=10)
            target_date = today + timedelta(weeks=10)
            iso_week = target_date.isocalendar().week
            task_capacity_ids = self.env['task.employee.capacity'].search([('tag_id.employee_id', '=', rec.id),
                                                                           ('task_id.stage_id.name', '!=', 'Abgeschlossen'),
                                                                           ('task_id.kw', '=', iso_week)])
            planned_working_time_week = sum(task_capacity_ids.mapped('hours')) + total_leaves

            rec.planned_capacity_pluse_10 = (
                planned_working_time_week / rec.target_work_hours_week if rec.target_work_hours_week else 1)


    planned_capacity_min_one = fields.Float(string='geplante Auslastung -1')
    planned_capacity_current = fields.Float(string='geplante Auslastung 0')

    planned_capacity_pluse_1 = fields.Float(string='geplante Auslastung 1')
    planned_capacity_pluse_2 = fields.Float(string='geplante Auslastung 2')
    planned_capacity_pluse_3 = fields.Float(string='geplante Auslastung 3')
    planned_capacity_pluse_4 = fields.Float(string='geplante Auslastung 4')
    planned_capacity_pluse_5 = fields.Float(string='geplante Auslastung 5')
    planned_capacity_pluse_6 = fields.Float(string='geplante Auslastung 6')
    planned_capacity_pluse_7 = fields.Float(string='geplante Auslastung 7')
    planned_capacity_pluse_8 = fields.Float(string='geplante Auslastung 8')
    planned_capacity_pluse_9 = fields.Float(string='geplante Auslastung 9')
    planned_capacity_pluse_10 = fields.Float(string='geplante Auslastung 10')


    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == 'list' and view_id and view_id == self.env.ref('grote_enhance.view_employee_utilization_tree').id:
            today = fields.Date.today()
            target_date = today + timedelta(weeks=-1)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_min_one']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=0)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_current']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=1)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_1']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=2)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_2']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=3)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_3']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=4)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_4']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=5)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_5']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=6)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_6']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=7)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_7']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=8)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_8']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=9)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_9']"):
                node.set("string", f"KW{iso_week}")
            target_date = today + timedelta(weeks=10)
            iso_week = target_date.isocalendar().week
            for node in arch.iterfind(".//field[@name='planned_capacity_pluse_10']"):
                node.set("string", f"KW{iso_week}")
        return arch, view
