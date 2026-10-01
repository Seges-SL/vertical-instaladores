# © 2024 Liyben
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from . import models
from . import wizard


def post_init_hook(env):
    # Los pedidos existentes al instalar se calcularon sin el tipo de
    # operación del módulo (aún no cargado): se completan ahora.
    env['sale.order']._recompute_empty_stock_options()
