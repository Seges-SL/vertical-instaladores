# © 2025 Sges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Creación de apuntes analiticos desde albaranes',
    'category': "Stock",
    'summary': 'Crea apuntes analiticos para poder controlar los costes / beneficiones de la cuenta analitica sin crear asientos contables.',
    'website': 'https://seges.es/',
    'version': '17.0.1.0.1',
    'license': 'AGPL-3',
    'description': """
        
        """,
    'author': 'Liyben',
    'depends': ['stock_account','stock_picking_analytic','project_stock'],
    "data": [
        "views/product_category_views.xml",
    ],
    'qweb': [],
    'images': [
    ],
    'demo': [
    ],
    'css': [
    ],
    'installable': True,
}
