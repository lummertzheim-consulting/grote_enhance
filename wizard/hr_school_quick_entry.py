# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta


class HrSchoolQuickEntryLine(models.TransientModel):
    _name = 'hr.school.quick.entry.line'
    _description = 'Berufsschul-Schnelleintrag Zeile'

    wizard_id = fields.Many2one('hr.school.quick.entry', string='Wizard', required=True, ondelete='cascade')
    selected = fields.Boolean(string='Auswählen', default=True)
    date = fields.Date(string='Datum', required=True)
    day_name = fields.Char(string='Wochentag', compute='_compute_day_name')

    @api.depends('date')
    def _compute_day_name(self):
        day_names = {
            0: 'Montag',
            1: 'Dienstag',
            2: 'Mittwoch',
            3: 'Donnerstag',
            4: 'Freitag',
            5: 'Samstag',
            6: 'Sonntag',
        }
        for line in self:
            if line.date:
                line.day_name = day_names.get(line.date.weekday(), '')
            else:
                line.day_name = ''


class HrSchoolQuickEntry(models.TransientModel):
    _name = 'hr.school.quick.entry'
    _description = 'Berufsschul-Schnelleintragung'

    employee_ids = fields.Many2many(
        'hr.employee',
        string='Auszubildende',
        required=True,
        domain="[('is_apprentice', '=', True)]"
    )
    date_from = fields.Date(string='Von', required=True)
    date_to = fields.Date(string='Bis', required=True)
    school_dates = fields.One2many(
        'hr.school.quick.entry.line',
        'wizard_id',
        string='Schultage'
    )

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        """Generiert die Schultage zwischen den Daten"""
        if not self.date_from or not self.date_to:
            return

        self.school_dates = [(5, 0, 0)]  # Clear existing
        current_date = self.date_from
        lines = []
        while current_date <= self.date_to:
            # Nur Wochentage (Mo-Fr)
            if current_date.weekday() < 5:
                lines.append((0, 0, {
                    'date': current_date,
                    'selected': True,
                }))
            current_date += timedelta(days=1)
        self.school_dates = lines

    def action_create_school_leaves(self):
        """Erstellt Abwesenheiten für die ausgewählten Tage und Mitarbeiter"""
        self.ensure_one()

        # Berufsschul-Abwesenheitstyp finden
        leave_type = self.env['hr.leave.type'].search([
            '|',
            ('name', 'ilike', 'berufsschule'),
            ('name', 'ilike', 'schule'),
        ], limit=1)

        if not leave_type:
            leave_type = self.env['hr.leave.type'].search([
                ('is_school', '=', True)
            ], limit=1)

        if not leave_type:
            raise models.ValidationError(
                "Kein Abwesenheitstyp für Berufsschule gefunden. "
                "Bitte erstellen Sie einen Abwesenheitstyp mit 'is_school = True'."
            )

        created_leaves = self.env['hr.leave']

        for employee in self.employee_ids:
            for line in self.school_dates.filtered('selected'):
                # Prüfen ob bereits eine Abwesenheit existiert
                existing = self.env['hr.leave'].search([
                    ('employee_id', '=', employee.id),
                    ('date_from', '<=', line.date),
                    ('date_to', '>=', line.date),
                    ('state', 'not in', ['cancel', 'refuse']),
                ], limit=1)

                if existing:
                    continue

                leave = self.env['hr.leave'].create({
                    'employee_id': employee.id,
                    'holiday_status_id': leave_type.id,
                    'date_from': line.date,
                    'date_to': line.date,
                    'number_of_days': 1,
                    'request_date_from': line.date,
                    'request_date_to': line.date,
                })
                created_leaves |= leave

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Berufsschul-Abwesenheiten',
                'message': f'{len(created_leaves)} Abwesenheiten wurden erstellt.',
                'type': 'success',
                'sticky': False,
            }
        }
