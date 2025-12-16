# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round
from datetime import datetime, timedelta


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.depends('number_of_hours', 'number_of_days', 'leave_type_request_unit', 'request_date_from', 'request_date_to', 'request_unit_hours', 'request_unit_half')
    def _compute_duration_display(self):
        super()._compute_duration_display()
        for leave in self.filtered(lambda l: l.leave_type_request_unit == "hour" and not l.request_unit_hours and not l.request_unit_half):
            date_from = fields.Datetime.from_string(leave.request_date_from).date()
            date_to = fields.Datetime.from_string(leave.request_date_to).date()
            calendar = leave.employee_id.resource_calendar_id

            total_hours = 0.0
            attendance_ids = calendar.attendance_ids.filtered(lambda x:x.day_period != 'lunch')
            if calendar and date_from and date_to:
                for i in range((date_to - date_from).days + 1):
                    day = date_from + timedelta(days=i)
                    weekday = day.weekday()
                    day_hours = sum(
                        att.hour_to - att.hour_from
                        for att in attendance_ids
                        if int(att.dayofweek) == weekday
                    )
                    if weekday in [0, 1, 2, 3, 4]:
                        day_hours = calendar.hours_per_day
                        # day_hours = sum(
                        #     att.hour_to - att.hour_from
                        #     for att in attendance_ids
                        #     if int(att.dayofweek) == 0
                        # )
                    total_hours += day_hours
            duration = total_hours
            unit = _('Tage')
            display = "%g %s" % (float_round(duration, precision_digits=2), unit)
            if leave.leave_type_request_unit == "hour":
                hours, minutes = divmod(abs(duration) * 60, 60)
                minutes = round(minutes)
                if minutes == 60:
                    minutes = 0
                    hours += 1
                duration = '%d:%02d' % (hours, minutes)
                unit = _("Stunden")
                display = f"{duration} {unit}"
            leave.duration_display = display


    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        """
        This method is factored out into a separate method from
        _compute_duration so it can be hooked and called without necessarily
        modifying the fields and triggering more computes of fields that
        depend on number_of_hours or number_of_days.
        """
        result = super(HrLeave, self)._get_durations(check_leave_type=check_leave_type, resource_calendar=resource_calendar)
        if self.filtered(lambda l: not l.request_unit_hours and not l.request_unit_half):
            for leave in self.filtered(lambda l: not l.request_unit_hours and not l.request_unit_half):
                date_from = fields.Datetime.from_string(leave.request_date_from).date()
                date_to = fields.Datetime.from_string(leave.request_date_to).date()
                calendar = leave.employee_id.resource_calendar_id

                total_hours = 0.0
                attendance_ids = calendar.attendance_ids.filtered(lambda x:x.day_period != 'lunch')
                if calendar and date_from and date_to:
                    for i in range((date_to - date_from).days + 1):
                        day = date_from + timedelta(days=i)
                        weekday = day.weekday()
                        day_hours = sum(
                            att.hour_to - att.hour_from
                            for att in attendance_ids
                            if int(att.dayofweek) == weekday
                        )
                        if weekday in [0, 1, 2, 3, 4]:
                            day_hours = calendar.hours_per_day
                            # day_hours = sum(
                            #     att.hour_to - att.hour_from
                            #     for att in attendance_ids
                            #     if int(att.dayofweek) == 0
                            # )
                        total_hours += day_hours
                duration = total_hours
                result[leave.id] = (result[leave.id][0], duration)
            return result
        return result