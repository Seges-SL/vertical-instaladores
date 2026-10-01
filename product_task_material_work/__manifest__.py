# © 2024 Liyben
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Trabajos y Materiales en producto',
    'version': '17.0.1.0.1',
    'license': 'AGPL-3',
    'category': 'Sales',
    'summary': 'Trabajos y Materiales en producto',
    'description': """


    """,
    'author': 'Seges',
    'depends': ['sale_crm','project_timesheet_time_control','sale_order_invoicing_finished_task','sale_margin','analytic_account_parent_on_sale_crm','project_task_code','project_stock','stock_picking_analytic', 'sale_order_line_layout'],
    'external_dependencies': {"python": ["openpyxl"]},
    'data': [

        'security/security.xml',
        'security/ir.model.access.csv',

        'report/ir_actions_report_sale_templates.xml',
        'report/ir_actions_report_invoice_templates.xml',
        'report/ir_actions_report_task_templates.xml',
        'report/ir_actions_report.xml',

        'data/project_data.xml',
        'data/ir_actions_server_data.xml',
        'data/stock_picking_type_data.xml',

        'wizard/res_config_settings_views.xml',
        'wizard/sale_order_merge_task_wizard_views.xml',

        'views/product_view.xml',
        'views/sale_view.xml',
        'views/project_task.xml',
        'views/crm_lead_view.xml',
        'views/hr_view.xml',
        'views/account_move_view.xml',
        'views/stock_picking_views.xml',
            ],
    'qweb': [],
    'images': [
    ],
    'demo': [
    ],
    'assets': {
        'web.report_assets_common': [
            'product_task_material_work/static/src/css/report.css',
        ],
        'web.report_assets_pdf': [
            'product_task_material_work/static/src/css/report.css',
        ],
    },
    'installable': True,
    'post_init_hook': 'post_init_hook',
}