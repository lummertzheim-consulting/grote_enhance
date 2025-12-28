# -*- coding: utf-8 -*-

{
    'name': 'Grote Enhance',
    'version': '19.0.1.1.0',
    'author': 'Fletscher',
    'category': 'Extra tools',
    'summary': 'Sales Manufacturing and project model changes',
    'description': '''This Module has Sales Manufacturing and project changes.
    
    Erweiterungen:
    - Auslastungsplanung mit Urlaubs- und Abwesenheitsberücksichtigung
    - Arbeitszeitkonto mit Überstunden-Saldo
    - Keine halben Urlaubstage (werden von Überstunden abgezogen)
    - Berufsschul-Schnelleintragung für Auszubildende
    - Anwesenheits-Dashboard
    - Erfolgslisten für Mitarbeiter
    ''',
    'support': 'felix@fletscher.de',
    'website': 'https://www.fletscher.de',
    'depends': ['base', 'web', 'mrp', 'sale_management', 'project', 'hr_timesheet', 'portal', 'documents', 'hr_holidays', 'hr_attendance'],
    "data": [
        "security/ir.model.access.csv",
        "security/ir.model.security.xml",
        "security/security.xml",
        "views/employee_list_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_capacity_views.xml",
        "views/hr_dashboard_views.xml",
        "views/mrp_bom_views.xml",
        "views/portal_template.xml",
        "views/product_template_views.xml",
        "views/project_portal_project_task_template.xml",
        "views/project_sharing_project_task_views.xml",
        "views/project_tags_views.xml",
        "views/project_task_type_views.xml",
        "views/project_task_views.xml",
        "views/project_views.xml",
        "views/res_users_view.xml",
        "views/sale_order_view.xml",
        "wizard/hr_school_quick_entry_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'grote_enhance/static/src/**/*.xml',
        ],
        'portal.assets_chatter': [
            '/grote_enhance/static/src/js/custom_portal_chatter_service.js',
        ],
        'web.assets_frontend': [
            '/grote_enhance/static/src/js/portal.js',
            '/grote_enhance/static/src/js/task_state.js'
        ]
    },
    'installable': True,
    'application': True,
    'images': [],
    'license': 'Other proprietary',
}
