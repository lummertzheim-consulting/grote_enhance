# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class HrEmployeeCapacity(models.Model):
    """Erweiterung für Arbeitszeitkonto und Kapazitätsplanung"""
    _inherit = 'hr.employee'

    # Verknüpfung zum Arbeitszeitmodell aus ors_customer_import
    work_time_model_id = fields.Many2one(
        'ors.work.time.model',
        string='Arbeitszeitmodell',
        help='Arbeitszeitmodell aus dem ORS Import Modul'
    )

    # Betriebsbereich - wird aus work_time_model_id übernommen oder manuell gesetzt
    department_type = fields.Selection(
        selection='_get_department_type_selection',
        string='Betriebsbereich',
        compute='_compute_department_type',
        store=True,
        readonly=False
    )

    @api.model
    def _get_department_type_selection(self):
        """Holt die Arbeitszeitmodelle aus ors_customer_import als Selection"""
        try:
            # Prüfe ob das Modell existiert
            if 'ors.work.time.model' in self.env:
                models = self.env['ors.work.time.model'].search([('active', '=', True)])
                if models:
                    return [(m.code, m.name) for m in models]
        except Exception as e:
            _logger.warning("Konnte Arbeitszeitmodelle nicht laden: %s", e)
        
        # Fallback wenn ors_customer_import nicht installiert ist
        return [
            ('maschinenbau', 'Maschinenbau (39 Std/Woche)'),
            ('kleingeraete', 'Kleingeräte (38,75 Std/Woche)'),
        ]

    @api.depends('work_time_model_id', 'work_time_model_id.code')
    def _compute_department_type(self):
        """Setzt department_type basierend auf work_time_model_id"""
        for employee in self:
            if employee.work_time_model_id:
                employee.department_type = employee.work_time_model_id.code
            elif not employee.department_type:
                employee.department_type = 'kleingeraete'

    # Arbeitszeitkonto
    overtime_balance = fields.Float(
        string='Überstunden-Saldo',
        compute='_compute_overtime_balance',
        store=True,
        help='Differenz zwischen Ist- und Soll-Arbeitszeit'
    )
    daily_target_hours = fields.Float(
        string='Tägliche Soll-Stunden',
        compute='_compute_from_work_time_model',
        store=True,
        readonly=False,
        default=7.75,
        help='Standard: 7,75 Stunden (7:45) für Kapazitätsplanung'
    )
    actual_daily_hours = fields.Float(
        string='Tatsächliche Tagesarbeitszeit',
        compute='_compute_from_work_time_model',
        store=True,
        readonly=False,
        default=8.5,
        help='Maschinenbau: 8,5 Std. (Mo-Do), Freitag 5 Std.'
    )
    weekly_overtime_generated = fields.Float(
        string='Wöchentliche Überstunden',
        compute='_compute_weekly_overtime',
        store=True,
        help='Automatische Überstunden durch Arbeitszeitmodell (z.B. 0,25 Std. bei 39 Std./Woche)'
    )

    @api.depends('work_time_model_id', 'work_time_model_id.daily_target_hours',
                 'work_time_model_id.monday_hours')
    def _compute_from_work_time_model(self):
        """Übernimmt Werte vom Arbeitszeitmodell"""
        for employee in self:
            if employee.work_time_model_id:
                employee.daily_target_hours = employee.work_time_model_id.daily_target_hours
                # Für actual_daily_hours nehmen wir den Montags-Wert als Referenz
                employee.actual_daily_hours = employee.work_time_model_id.monday_hours
            else:
                if not employee.daily_target_hours:
                    employee.daily_target_hours = 7.75
                if not employee.actual_daily_hours:
                    employee.actual_daily_hours = 8.5

    # Urlaubskonto
    vacation_days_total = fields.Float(
        string='Urlaubstage Gesamt (Jahr)',
        default=30.0
    )
    vacation_days_taken = fields.Float(
        string='Urlaubstage genommen',
        compute='_compute_vacation_days'
    )
    vacation_days_remaining = fields.Float(
        string='Urlaubstage verbleibend',
        compute='_compute_vacation_days'
    )

    # Erfolgsliste / Leistungskonto
    assigned_hours_total = fields.Float(
        string='Zugewiesene Stunden (Gesamt)',
        compute='_compute_work_performance',
        help='Summe aller zugewiesenen Aufgabenstunden'
    )
    completed_hours_total = fields.Float(
        string='Abgearbeitete Stunden (Gesamt)',
        compute='_compute_work_performance',
        help='Summe aller erfassten Zeitbuchungen'
    )
    completion_rate = fields.Float(
        string='Erfüllungsquote (%)',
        compute='_compute_work_performance',
        help='Verhältnis abgearbeitete zu zugewiesene Stunden'
    )

    # Ist Auszubildender (für Berufsschul-Schnelleintragung)
    is_apprentice = fields.Boolean(
        string='Ist Auszubildender',
        default=False
    )

    @api.depends('work_time_model_id', 'work_time_model_id.weekly_overtime_generated',
                 'department_type', 'target_work_hours_week')
    def _compute_weekly_overtime(self):
        """Berechnet wöchentliche Überstunden aus Arbeitszeitmodell"""
        for employee in self:
            if employee.work_time_model_id:
                employee.weekly_overtime_generated = employee.work_time_model_id.weekly_overtime_generated
            elif employee.department_type == 'maschinenbau':
                # 39 Std. Arbeitszeit, aber 38,75 Std. Soll = 0,25 Std. Überstunden/Woche
                employee.weekly_overtime_generated = 0.25
            else:
                employee.weekly_overtime_generated = 0.0

    @api.depends('attendance_ids', 'attendance_ids.worked_hours')
    def _compute_overtime_balance(self):
        """Berechnet Überstunden-Saldo aus Zeiterfassung"""
        for employee in self:
            # Alle Anwesenheiten des Jahres
            year_start = date(date.today().year, 1, 1)
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', datetime.combine(year_start, datetime.min.time())),
            ])
            total_worked = sum(attendances.mapped('worked_hours'))

            # Soll-Stunden berechnen (Arbeitstage * tägliche Soll-Stunden)
            expected_hours = employee._get_expected_hours_year()

            employee.overtime_balance = total_worked - expected_hours

    def _get_expected_hours_year(self):
        """Berechnet die Soll-Stunden für das aktuelle Jahr"""
        self.ensure_one()
        year_start = date(date.today().year, 1, 1)
        today = date.today()

        if not self.resource_calendar_id:
            return 0.0

        # Arbeitstage im Zeitraum berechnen - kompatibel mit Odoo 19
        import pytz
        tz = pytz.timezone(self.resource_calendar_id.tz or 'UTC')
        from_datetime = tz.localize(datetime.combine(year_start, datetime.min.time()))
        to_datetime = tz.localize(datetime.combine(today, datetime.max.time()))
        
        # Berechne Arbeitsstunden über die Intervalle
        intervals = self.resource_calendar_id._work_intervals_batch(
            from_datetime, 
            to_datetime,
            resources=self.resource_id,
            tz=tz
        )
        
        total_work_hours = 0.0
        resource_intervals = intervals.get(self.resource_id.id, [])
        for start, end, meta in resource_intervals:
            total_work_hours += (end - start).total_seconds() / 3600.0
        
        return total_work_hours

    def _compute_vacation_days(self):
        """Berechnet genommene und verbleibende Urlaubstage"""
        for employee in self:
            year_start = date(date.today().year, 1, 1)
            year_end = date(date.today().year, 12, 31)

            # Urlaub-Abwesenheitstypen finden
            vacation_types = self.env['hr.leave.type'].search([
                '|',
                ('name', 'ilike', 'urlaub'),
                ('name', 'ilike', 'vacation'),
            ])

            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', 'in', vacation_types.ids),
                ('state', '=', 'validate'),
                ('request_date_from', '>=', year_start),
                ('request_date_from', '<=', year_end),
            ])

            employee.vacation_days_taken = sum(leaves.mapped('number_of_days'))
            employee.vacation_days_remaining = (
                employee.vacation_days_total - employee.vacation_days_taken
            )

    def _compute_work_performance(self):
        """Berechnet Erfolgsliste / Leistungskennzahlen"""
        for employee in self:
            # Zugewiesene Stunden aus Aufgaben
            task_capacities = self.env['task.employee.capacity'].search([
                ('tag_id.employee_id', '=', employee.id),
            ])
            employee.assigned_hours_total = sum(task_capacities.mapped('hours'))

            # Abgearbeitete Stunden aus Zeiterfassung
            timesheets = self.env['account.analytic.line'].search([
                ('employee_id', '=', employee.id),
                ('task_id', '!=', False),
            ])
            employee.completed_hours_total = sum(timesheets.mapped('unit_amount'))

            # Erfüllungsquote berechnen
            if employee.assigned_hours_total > 0:
                employee.completion_rate = (
                    employee.completed_hours_total / employee.assigned_hours_total * 100
                )
            else:
                employee.completion_rate = 0.0

    def action_manual_leave_entry(self):
        """Öffnet Wizard für manuelle Urlaubseintragung durch Vorgesetzten"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Urlaub manuell eintragen'),
            'res_model': 'hr.leave',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
                'default_request_date_from': fields.Date.today(),
                'default_request_date_to': fields.Date.today(),
            },
        }


class HrLeaveTypeCapacity(models.Model):
    """Erweiterung der Abwesenheitstypen für Kapazitätsplanung"""
    _inherit = 'hr.leave.type'

    is_school = fields.Boolean(
        string='Ist Berufsschule',
        default=False,
        help='Für Schnelleintragung von Berufsschultagen'
    )
    capacity_hours = fields.Float(
        string='Kapazitätsabzug (Std.)',
        default=7.75,
        help='Stunden die pro Tag von der Kapazität abgezogen werden'
    )
    deduct_from_overtime = fields.Boolean(
        string='Von Überstunden abziehen',
        default=False,
        help='Halbe Tage werden von Überstunden abgezogen'
    )


class HrLeaveCapacity(models.Model):
    """Erweiterung für Abwesenheiten mit Grote-spezifischen Regeln"""
    _inherit = 'hr.leave'

    is_half_day = fields.Boolean(
        string='Halber Tag',
        compute='_compute_is_half_day',
        store=True
    )
    deducted_from_overtime = fields.Float(
        string='Von Überstunden abgezogen',
        default=0.0
    )
    overtime_added = fields.Float(
        string='Als Überstunden gutgeschrieben',
        default=0.0,
        help='Rest nach Urlaubsabzug wenn keine Überstunden vorhanden'
    )

    @api.depends('number_of_days')
    def _compute_is_half_day(self):
        for leave in self:
            leave.is_half_day = 0 < leave.number_of_days < 1.0

    @api.constrains('number_of_days', 'holiday_status_id')
    def _check_no_half_day_vacation(self):
        """
        Grote-Regel: Keine halben Urlaubstage erlaubt.
        Halbe Abwesenheiten werden von Überstunden abgezogen.
        """
        for leave in self:
            # Prüfen ob es ein Urlaubs-Typ ist
            is_vacation = (
                'urlaub' in (leave.holiday_status_id.name or '').lower() or
                'vacation' in (leave.holiday_status_id.name or '').lower()
            )

            if is_vacation and leave.number_of_days % 1 != 0:
                raise ValidationError(_(
                    'Halbe Urlaubstage sind nicht erlaubt.\n'
                    'Halbe Abwesenheiten werden von Überstunden abgezogen.\n'
                    'Wenn keine Überstunden vorhanden sind, wird ein ganzer '
                    'Urlaubstag abgezogen und der Rest als Überstunden gutgeschrieben.'
                ))

    def _handle_half_day_overtime(self):
        """
        Behandelt halbe Tage durch Überstundenabzug.
        Regel: Wenn keine Überstunden da, dann 1 Tag Urlaub abziehen
        und Rest als Überstunden eintragen.
        """
        for leave in self:
            if not leave.is_half_day:
                continue

            if not leave.holiday_status_id.deduct_from_overtime:
                continue

            employee = leave.employee_id
            hours_needed = leave.number_of_days * 7.75  # Halber Tag = 3,875 Std.

            if employee.overtime_balance >= hours_needed:
                # Komplett von Überstunden abziehen
                leave.deducted_from_overtime = hours_needed
            else:
                # Nicht genug Überstunden: 1 Tag Urlaub, Rest als Überstunden
                leave.overtime_added = 7.75 - hours_needed


class HrSchoolQuickEntry(models.TransientModel):
    """Wizard für schnelle Berufsschul-Eintragung"""
    _name = 'hr.school.quick.entry'
    _description = 'Berufsschul-Schnelleintragung'

    employee_ids = fields.Many2many(
        'hr.employee',
        string='Auszubildende',
        domain=[('is_apprentice', '=', True)]
    )
    date_from = fields.Date(
        string='Von',
        required=True,
        default=fields.Date.today
    )
    date_to = fields.Date(
        string='Bis',
        required=True,
        default=fields.Date.today
    )
    school_dates = fields.Many2many(
        'hr.school.date.line',
        string='Schultage',
        compute='_compute_school_dates',
        store=True,
        readonly=False
    )

    @api.depends('date_from', 'date_to')
    def _compute_school_dates(self):
        """Generiert Datumsliste zwischen Von und Bis"""
        for wizard in self:
            if not wizard.date_from or not wizard.date_to:
                wizard.school_dates = [(5, 0, 0)]
                continue

            dates = []
            current = wizard.date_from
            while current <= wizard.date_to:
                # Nur Werktage (Mo-Fr)
                if current.weekday() < 5:
                    dates.append((0, 0, {
                        'date': current,
                        'selected': True,
                    }))
                current += timedelta(days=1)
            wizard.school_dates = [(5, 0, 0)] + dates

    def action_create_school_leaves(self):
        """Erstellt Abwesenheiten für ausgewählte Schultage"""
        school_leave_type = self.env['hr.leave.type'].search([
            ('is_school', '=', True)
        ], limit=1)

        if not school_leave_type:
            raise ValidationError(_(
                'Kein Abwesenheitstyp für Berufsschule gefunden.\n'
                'Bitte erstellen Sie einen Abwesenheitstyp mit aktivierter '
                'Option "Ist Berufsschule".'
            ))

        created_leaves = self.env['hr.leave']
        selected_dates = self.school_dates.filtered('selected')

        for employee in self.employee_ids:
            for date_line in selected_dates:
                leave = self.env['hr.leave'].create({
                    'employee_id': employee.id,
                    'holiday_status_id': school_leave_type.id,
                    'request_date_from': date_line.date,
                    'request_date_to': date_line.date,
                })
                created_leaves |= leave

        return {
            'type': 'ir.actions.act_window',
            'name': _('Erstellte Berufsschul-Abwesenheiten'),
            'res_model': 'hr.leave',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_leaves.ids)],
            'target': 'current',
        }


class HrSchoolDateLine(models.TransientModel):
    """Hilfsmodell für Schultag-Auswahl"""
    _name = 'hr.school.date.line'
    _description = 'Schultag Zeile'

    date = fields.Date(string='Datum', required=True)
    selected = fields.Boolean(string='Auswählen', default=True)
    day_name = fields.Char(string='Wochentag', compute='_compute_day_name')

    @api.depends('date')
    def _compute_day_name(self):
        days = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
        for line in self:
            if line.date:
                line.day_name = days[line.date.weekday()]
            else:
                line.day_name = ''
