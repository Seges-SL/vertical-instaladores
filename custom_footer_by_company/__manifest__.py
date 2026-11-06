# © 2025 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Pie de página personalizado',
    'version': '17.0.2.0.0',
    'summary': """ Pie de página personalizado """,
    'author': 'Seges',
    'website': 'seges.es',
    'category': 'Reporting',
    'depends': ['base', 'web'],
    "data": [
        "template/report_tamplate.xml",
        "views/res_company_views.xml",
        "wizards/base_document_layout.xml",
    ],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
