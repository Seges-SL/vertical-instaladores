# Copyright 2026 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Migración directa 14.0 -> 17.0 (sin escalones intermedios: el repo
vertical-instaladores solo tiene rama en 14.0 y 17.0, así que esta es la
única transición de versión que va a ver este módulo).

Módulos que se fusionan aquí porque su funcionalidad quedó absorbida en
product_task_material_work y su código ya no existe como módulo aparte en
17.0: merge_pt, product_price_with_waste,
print_options_to_false_account_move_line,
sale_order_invoicing_finished_fix_translation,
sale_order_invoicing_finished_merge_task.

product_task_material_work_category NO se fusiona aquí. En 14.0 era un
módulo aparte (dependía de product_task_material_work, no al revés) que
añadía la tarifa a nivel de la CATEGORÍA del compuesto + coste vía
supplierinfo -- funcionalidad que 17.0 no reimplementa. Se decide dejarlo
como módulo propio también en 17.0, pendiente de reimplementar. Mientras
ese módulo 17.0 no exista, su fila en ir_module_module (si estaba
instalada en 14.0) se fuerza a 'uninstalled' por SQL antes del arranque
-- ver scripts/openupgrade/neutralize_replaced_modules.sh. Su campo
'apply_category' se respalda aquí (si la columna existe) por si el módulo
futuro necesita reconstruir la configuración; este script NO lo consume.
El comportamiento de 'apply_pricelist' del propio product_task_material_work
sí cambia entre 14.0 y 17.0 y se corrige en el post-migration
(_invert_apply_pricelist), sin relación con 'apply_category'.

Módulos nuevos, extraídos de este mismo módulo en 17.0, que hay que forzar a
instalar en la misma pasada de -u all: si no, en el instante en que
product_task_material_work deja de declarar sus campos (por ejemplo
'by_administration') y todavía no se ha instalado el módulo que los declara
ahora, esos campos quedarían sin ningún módulo que los reclame y Odoo
borraría la columna al limpiar huérfanos. Ver
odoo/modules/loading.py:load_marked_modules -- relee ir_module_module.state
en bucle hasta que no aparece nada nuevo, así que no hace falta pasar -i por
línea de comandos, basta con dejar el estado en 'to install' aquí.
"""
from openupgradelib import openupgrade

_MERGED_MODULES = [
    ("merge_pt", "product_task_material_work"),
    ("product_price_with_waste", "product_task_material_work"),
    ("print_options_to_false_account_move_line", "product_task_material_work"),
    ("sale_order_invoicing_finished_fix_translation", "product_task_material_work"),
    ("sale_order_invoicing_finished_merge_task", "product_task_material_work"),
]

_NEW_DEPENDENT_MODULES = (
    "crm_lead_to_project_task",
    "project_task_to_sale_order",
    "project_task_by_administration",
    "resume_material_and_work",
    "comparisons_sale_order",
)

# Rename real (mismo campo, mismo propósito -- rename_fields, no
# rename_columns: además del ALTER TABLE, actualiza ir_model_fields.name,
# traducciones y ir_property por si algún filtro/exportación guardado
# referencia 'sign_by' por nombre. Ver openupgradelib.rename_fields():
# "call this method whenever you are NOT performing a pure SQL column
# renaming for other purposes".
_FIELD_RENAMES = [
    ("project.task", "project_task", "sign_by", "signed_by"),
]

# Respaldo bajo nombre "legacy" (get_legacy_name(), al pasar new=None) de
# columnas a punto de quedar huérfanas. Cada una se comprueba con
# column_exists porque el módulo 14.0 que la declaraba puede no haber
# estado instalado en la BD de origen:
#  - 'merged_parent_id' (project_task): jerarquía padre/hijo de tareas
#    fusionadas; 17.0 lo sustituye por la tabla M2M 'merge_tasks' (creada
#    por este mismo módulo, todavía inexistente en el pre-migration). Se
#    respalda para poblar esa tabla en el post-migration (_fix_merge_tasks).
#  - 'apply_category' (product_template): de product_task_material_work_category,
#    que NO se fusiona aquí (ver docstring de arriba). Se respalda por si el
#    módulo 17.0 futuro lo necesita; este script no lo consume.
_LEGACY_COLUMN_BACKUPS = {
    "project_task": ["merged_parent_id"],
    "product_template": ["apply_category"],
}


def _merge_absorbed_modules(cr):
    """Fusiona en 'product_task_material_work' los módulos 14.0 cuya
    funcionalidad quedó absorbida en éste (ver _MERGED_MODULES). Va antes
    que nada: cambia qué módulos existen/están instalados, y el resto de
    este script asume que ya está resuelto."""
    openupgrade.update_module_names(cr, _MERGED_MODULES, merge_modules=True)


def _force_install_new_dependent_modules(cr):
    """Fuerza a 'to install' los módulos nuevos extraídos de este mismo
    módulo en 17.0 (ver _NEW_DEPENDENT_MODULES), para que se instalen en
    esta misma pasada de -u all."""
    openupgrade.logged_query(
        cr,
        """
        UPDATE ir_module_module SET state = 'to install'
        WHERE name IN %s AND state != 'to install'
        """,
        (_NEW_DEPENDENT_MODULES,),
    )


def _backup_legacy_columns(cr):
    """Renombra a nombre "legacy" solo las columnas de _LEGACY_COLUMN_BACKUPS
    que existan de verdad -- si el módulo 14.0 que las declaraba no estaba
    instalado, la columna no está y rename_columns reventaría."""
    spec = {}
    for table, columns in _LEGACY_COLUMN_BACKUPS.items():
        present = [c for c in columns if openupgrade.column_exists(cr, table, c)]
        if present:
            spec[table] = [(c, None) for c in present]
    if spec:
        openupgrade.rename_columns(cr, spec)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    # 1. Fusionar los módulos absorbidos ANTES que nada.
    _merge_absorbed_modules(cr)

    # 2. Forzar la instalación de los módulos nuevos en esta misma pasada.
    _force_install_new_dependent_modules(cr)

    # 3. Rename real de campo (con todos sus efectos secundarios).
    openupgrade.rename_fields(env, _FIELD_RENAMES)

    # 4. Respaldo de columnas a punto de quedar huérfanas.
    _backup_legacy_columns(cr)
