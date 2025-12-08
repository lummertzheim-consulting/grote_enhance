import json

from collections import OrderedDict
from operator import itemgetter
from markupsafe import Markup

from odoo import conf, http, fields, _
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.osv.expression import AND, FALSE_DOMAIN
from odoo.tools import date_utils,groupby as groupbyelem

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.project.controllers.portal import ProjectCustomerPortal
from odoo.addons.hr_timesheet.controllers.portal import TimesheetCustomerPortal
from datetime import date
from dateutil.relativedelta import relativedelta


def _prepare_tasks_values(self, page, date_begin, date_end, sortby, search, search_in, groupby, url="/my/tasks", domain=None, su=False, project=False):
    values = self._prepare_portal_layout_values()

    Task = request.env['project.task']

    if not domain:
        domain = []
    if not su and Task.has_access('read'):
        domain = AND([domain, request.env['ir.rule']._compute_domain(Task._name, 'read')])
    Task_sudo = Task.sudo()
    milestone_domain = AND([domain, [('allow_milestones', '=', True)], [('milestone_id', '!=', False)]])
    milestones_allowed = Task_sudo.search_count(milestone_domain, limit=1) == 1
    searchbar_sortings = dict(sorted(self._task_get_searchbar_sortings(milestones_allowed, project).items(),
                                        key=lambda item: item[1]["sequence"]))
    searchbar_inputs = dict(sorted(self._task_get_searchbar_inputs(milestones_allowed, project).items(), key=lambda item: item[1]['sequence']))
    searchbar_groupby = dict(sorted(self._task_get_searchbar_groupby(milestones_allowed, project).items(), key=lambda item: item[1]['sequence']))

    # default sort by value
    if not sortby or (sortby == 'milestone_id' and not milestones_allowed):
        sortby = 'create_date desc'

    # default group by value
    if not groupby or (groupby == 'milestone_id' and not milestones_allowed):
        groupby = 'project_id'

    if request.env.user.has_group('base.group_portal'):
        domain += [('stage_id.is_visible_portal_user', '=', True)]

    if date_begin and date_end:
        domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

    # search reset if needed
    if not milestones_allowed and search_in == 'milestone_id':
        search_in = 'all'
    # search
    if search and search_in:
        domain = AND([domain, self._task_get_search_domain(search_in, search, milestones_allowed, project)])

    # content according to pager and archive selected
    if groupby == 'none':
        group_field = None
    elif groupby == 'priority':
        group_field = 'priority desc'
    else:
        group_field = groupby
    order = '%s, %s' % (group_field, sortby) if group_field else sortby

    def get_grouped_tasks(pager_offset):
        tasks = Task_sudo.search(domain, order=order, limit=self._items_per_page, offset=pager_offset)
        request.session['my_project_tasks_history' if url.startswith('/my/projects') else 'my_tasks_history'] = tasks.ids[:100]

        tasks_project_allow_milestone = tasks.filtered(lambda t: t.allow_milestones)
        tasks_no_milestone = tasks - tasks_project_allow_milestone

        if groupby != 'none':
            if groupby == 'milestone_id':
                grouped_tasks = [Task_sudo.concat(*g) for k, g in groupbyelem(tasks_project_allow_milestone, itemgetter(groupby))]

                if not grouped_tasks:
                    if tasks_no_milestone:
                        grouped_tasks = [tasks_no_milestone]
                else:
                    if grouped_tasks[len(grouped_tasks) - 1][0].milestone_id and tasks_no_milestone:
                        grouped_tasks.append(tasks_no_milestone)
                    else:
                        grouped_tasks[len(grouped_tasks) - 1] |= tasks_no_milestone

            else:
                grouped_tasks = [Task_sudo.concat(*g) for k, g in groupbyelem(tasks, itemgetter(groupby))]
        else:
            grouped_tasks = [tasks] if tasks else []


        task_states = dict(Task_sudo._fields['state']._description_selection(request.env))
        if sortby == 'state':
            if groupby == 'none' and grouped_tasks:
                grouped_tasks[0] = grouped_tasks[0].sorted(lambda tasks: task_states.get(tasks.state))
            else:
                grouped_tasks.sort(key=lambda tasks: task_states.get(tasks[0].state))
        return grouped_tasks

    values.update({
        'date': date_begin,
        'date_end': date_end,
        'grouped_tasks': get_grouped_tasks,
        'allow_milestone': milestones_allowed,
        'multiple_projects': True,
        'page_name': 'task',
        'default_url': url,
        'task_url': 'tasks',
        'pager': {
            "url": url,
            "url_args": {'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'groupby': groupby, 'search_in': search_in, 'search': search},
            "total": Task_sudo.search_count(domain),
            "page": page,
            "step": self._items_per_page
        },
        'searchbar_sortings': searchbar_sortings,
        'searchbar_groupby': searchbar_groupby,
        'searchbar_inputs': searchbar_inputs,
        'search_in': search_in,
        'search': search,
        'sortby': sortby,
        'groupby': groupby,
    })
    return values


ProjectCustomerPortal._prepare_tasks_values = _prepare_tasks_values

@http.route(['/my/timesheets', '/my/timesheets/page/<int:page>'], type='http', auth="user", website=True)
def portal_my_timesheets(self, page=1, sortby=None, filterby=None, search=None,search_in='all', groupby='none', **kw):
    Timesheet = request.env['account.analytic.line']
    domain = Timesheet._timesheet_get_portal_domain()
    Timesheet_sudo = Timesheet.sudo()

    values = self._prepare_portal_layout_values()
    _items_per_page = 100

    # Search bar setup
    searchbar_sortings = self._get_searchbar_sortings()
    searchbar_inputs = dict(sorted(self._get_searchbar_inputs().items(), key=lambda item: item[1]['sequence']))
    searchbar_groupby = dict(sorted(self._get_searchbar_groupby().items(), key=lambda item: item[1]['sequence']))

    # Date filters
    today = fields.Date.today()
    quarter_start, quarter_end = date_utils.get_quarter(today)
    last_quarter_date = date_utils.subtract(quarter_start, weeks=1)
    last_quarter_start, last_quarter_end = date_utils.get_quarter(last_quarter_date)
    last_week = today + relativedelta(weeks=-1)
    last_month = today + relativedelta(months=-1)
    last_year = today + relativedelta(years=-1)

    searchbar_filters = {
        'all': {'label': _('All'), 'domain': []},
        'last_year': {'label': _('Last Year'), 'domain': [
            ('date', '>=', date_utils.start_of(last_year, 'year')),
            ('date', '<=', date_utils.end_of(last_year, 'year'))
        ]},
        'last_quarter': {'label': _('Last Quarter'), 'domain': [
            ('date', '>=', last_quarter_start),
            ('date', '<=', last_quarter_end)
        ]},
        'last_month': {'label': _('Last Month'), 'domain': [
            ('date', '>=', date_utils.start_of(last_month, 'month')),
            ('date', '<=', date_utils.end_of(last_month, 'month'))
        ]},
        'last_week': {'label': _('Last Week'), 'domain': [
            ('date', '>=', date_utils.start_of(last_week, "week")),
            ('date', '<=', date_utils.end_of(last_week, 'week'))
        ]},
        'today': {'label': _('Today'), 'domain': [("date", "=", today)]},
        'week': {'label': _('This Week'), 'domain': [
            ('date', '>=', date_utils.start_of(today, "week")),
            ('date', '<=', date_utils.end_of(today, 'week'))
        ]},
        'month': {'label': _('This Month'), 'domain': [
            ('date', '>=', date_utils.start_of(today, 'month')),
            ('date', '<=', date_utils.end_of(today, 'month'))
        ]},
        'quarter': {'label': _('This Quarter'), 'domain': [
            ('date', '>=', quarter_start),
            ('date', '<=', quarter_end)
        ]},
        'year': {'label': _('This Year'), 'domain': [
            ('date', '>=', date_utils.start_of(today, 'year')),
            ('date', '<=', date_utils.end_of(today, 'year'))
        ]},
    }

    # Defaults
    if not sortby:
        sortby = 'date desc'
    if not filterby:
        filterby = 'all'

    domain = AND([domain, searchbar_filters[filterby]['domain']])

    if search and search_in:
        domain = AND([domain, self._get_search_domain(search_in, search)])

    if parent_task_id := kw.get('parent_task_id'):
        domain = AND([domain, [('parent_task_id', '=', int(parent_task_id))]])

    timesheet_count = Timesheet_sudo.search_count(domain)

    pager = portal_pager(
        url="/my/timesheets",
        url_args={
            'sortby': sortby, 'search_in': search_in,
            'search': search, 'filterby': filterby, 'groupby': groupby
        },
        total=timesheet_count,
        page=page,
        step=_items_per_page
    )

    def get_timesheets():
        field = None if groupby == 'none' else groupby
        orderby = f"{field}, {sortby}" if field else sortby
        timesheets = Timesheet_sudo.search(domain, order=orderby, limit=_items_per_page, offset=pager['offset'])
        if field:
            if groupby == 'date':
                raw_timesheets_group = Timesheet_sudo._read_group(
                    domain, ['date:day'], ['unit_amount:sum', 'id:recordset'], order='date:day desc'
                )
                grouped_timesheets = [(records, unit_amount) for __, unit_amount, records in raw_timesheets_group]

            elif groupby in ['month_name']:
                # Precomputed fields, group directly
                raw_timesheets_group = Timesheet_sudo._read_group(
                    domain, ['date:month'], ['unit_amount:sum', 'id:recordset'], order=f"date:month desc"
                )
                grouped_timesheets = [(records, total) for __, total, records in raw_timesheets_group]

            elif groupby in ['week_name']:
                # Precomputed fields, group directly
                raw_timesheets_group = Timesheet_sudo._read_group(
                    AND([domain, [('year', '=', fields.Date.today().year)]]), [groupby], ['unit_amount:sum', 'id:recordset'], order=f"{groupby} desc"
                )
                grouped_timesheets = [(records, total) for __, total, records in raw_timesheets_group]
            
            elif groupby in ['year']:
                # Precomputed fields, group directly
                raw_timesheets_group = Timesheet_sudo._read_group(
                    domain, [groupby], ['unit_amount:sum', 'id:recordset'], order=f"{groupby} desc"
                )
                grouped_timesheets = [(records, total) for __, total, records in raw_timesheets_group]

            else:
                # Default field-based grouping
                time_data = Timesheet_sudo._read_group(domain, [field], ['unit_amount:sum'])
                mapped_time = {field.id: unit_amount for field, unit_amount in time_data}
                grouped_timesheets = [
                    (Timesheet_sudo.concat(*g), mapped_time.get(k.id, 0)) for k, g in groupbyelem(timesheets, itemgetter(field))
                ]
            return timesheets, grouped_timesheets

        # Default (no groupby)
        grouped_timesheets = [(
            timesheets,
            Timesheet_sudo._read_group(domain, aggregates=['unit_amount:sum'])[0][0]
        )] if timesheets else []
        return timesheets, grouped_timesheets

    timesheets, grouped_timesheets = get_timesheets()

    values.update({
        'timesheets': timesheets,
        'grouped_timesheets': grouped_timesheets,
        'page_name': 'timesheet',
        'default_url': '/my/timesheets',
        'pager': pager,
        'searchbar_sortings': searchbar_sortings,
        'search_in': search_in,
        'search': search,
        'sortby': sortby,
        'groupby': groupby,
        'searchbar_inputs': searchbar_inputs,
        'searchbar_groupby': searchbar_groupby,
        'searchbar_filters': searchbar_filters,
        'filterby': filterby,
        'is_uom_day': request.env['account.analytic.line']._is_timesheet_encode_uom_day(),
    })
    return request.render("hr_timesheet.portal_my_timesheets", values)

TimesheetCustomerPortal.portal_my_timesheets = portal_my_timesheets

class CustomTimesheetCustomerPortal(TimesheetCustomerPortal):

    def _get_searchbar_groupby(self):
        values = super()._get_searchbar_groupby()
        values |= {
            'week_name': {'label': _('Woche'), 'sequence': 120},
            'month_name': {'label': _('Monat'), 'sequence': 130},
            'year': {'label': _('Jahr'), 'sequence': 140},
        }
        return values

class PortalTaskActivity(CustomerPortal):

    @http.route(['/my/task/<int:task_id>/add_activity'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_task_add_activity(self, task_id, **post):
        task = request.env['project.task'].sudo().browse(task_id)
        if not task.exists():
            return request.not_found()

        # allocated_hours = float(post.get('allocated_hours', 0))
        # if task and allocated_hours:
        #     task.sudo().write({'allocated_hours': allocated_hours})
        time_spent = float(post.get('time_spent', 0)) if post.get('time_spent', 0) else 0
        activity_date = date.today().isoformat()
        description = post.get('description', '')

        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.user.id)],
            limit=1
        )
        if time_spent > 0:
            request.env['account.analytic.line'].sudo().create({
                'name': description or task.name,
                'user_id': request.env.user.id,
                'date': activity_date,
                'unit_amount': time_spent,
                'project_id': task.project_id.id,
                'task_id': task.id,
                'employee_id': employee.id if employee else False,
            })

        return request.redirect('/my/tasks')


    @http.route('/portal/task/<int:task_id>/change_state', type='json', auth='user', methods=['POST'], website=True)
    def portal_change_task_state(self, task_id, new_state):
        """Portal endpoint to update a task state"""
        task = request.env['project.task'].sudo().browse(task_id)

        if not task.exists():
            return {'success': False, 'error': 'Task not found'}
        if task.state != new_state:
            # Update task state
            task.sudo().write({'state': new_state})

        return {
            'success': True,
            'message': 'Task state updated',
            'new_state': new_state,
        }
