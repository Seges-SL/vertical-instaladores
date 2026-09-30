# Copyright 2026 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Segunda mitad de la migración directa 14.0 -> 17.0 de
product_task_material_work -- consume aquí lo que pre-migration.py dejó
respaldado bajo nombres "legacy", una vez el ORM ya aplicó el esquema nuevo
del módulo (por eso hace falta post, no se puede hacer todo en pre: la tabla
'merge_tasks' todavía no existe en el pre-migration).
"""
from openupgradelib import openupgrade


def _invert_apply_pricelist(env):
    """'apply_pricelist' existe con el mismo nombre en product.template en
    14.0 y 17.0, así que la columna se arrastra intacta -- pero su valor
    significa lo CONTRARIO:

    - 14.0 True  -> regla de tarifa aplicada sobre el compuesto entero
                    (base = suma de los componentes ya tarificados).
    - 14.0 False -> el precio del compuesto es la suma directa de sus
                    componentes, sin regla sobre el compuesto.
    - 17.0 True  -> tarifa aplicada a cada componente; el compuesto es la
                    suma  (equivale al 14.0 False).
    - 17.0 False -> tarifa aplicada sobre el compuesto; los componentes van
                    a precio de catálogo (equivale, en lo esencial, al
                    14.0 True).

    Por eso el valor se invierte. Solo aplica a productos partida
    (service_tracking de tarea); en el resto 'apply_pricelist' no se
    consulta nunca, así que no se toca -- si no, se voltearía el checkbox
    en miles de productos irrelevantes. NULL cuenta como False (COALESCE).

    Aviso: en la dirección 14.0 True -> 17.0 False se conserva la regla
    sobre el compuesto, pero el desglose de componentes pasa de tarificado
    a precio de catálogo; solo se nota si la tarifa del cliente tiene
    reglas a nivel de los productos componentes. No tiene ninguna relación
    con 'apply_category' de product_task_material_work_category (que en
    17.0 no se fusiona -- ver pre-migration.py). Ver MIGRATION_14_TO_17.md.
    """
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE product_template
        SET apply_pricelist = NOT COALESCE(apply_pricelist, false)
        WHERE service_tracking IN ('task_global_project', 'task_in_project')
        """,
    )


def _fix_merge_tasks(env):
    """14.0 guardaba las fusiones de tareas como jerarquía padre/hijo
    ('merged_parent_id' + su inverso 'merged_child_ids', ambos sobre
    project.task). 17.0 lo sustituye por una relación M2M plana
    ('merge_task_ids', tabla 'merge_tasks'). No es un rename, es un cambio
    de modelo de datos -- hay que poblar la tabla nueva a mano a partir de
    la FK vieja (respaldada en pre-migration antes de que se perdiera).

    Si el módulo 14.0 que declaraba 'merged_parent_id' no estaba instalado,
    el pre-migration no habrá creado la columna legacy y aquí no hay nada
    que hacer.
    """
    legacy_col = openupgrade.get_legacy_name("merged_parent_id")
    if not openupgrade.column_exists(env.cr, "project_task", legacy_col):
        return
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO merge_tasks (task_id, merge_task_id)
        SELECT {legacy_col}, id
        FROM project_task
        WHERE {legacy_col} IS NOT NULL
        """.format(legacy_col=legacy_col),
    )


def _activate_percent_waste_if_used(env):
    """'percent_waste' es el mismo campo, misma tabla (product.template),
    en 14.0 y 17.0 -- el dato sobrevive solo, sin necesidad de nada en este
    script. Pero en 17.0 su uso queda condicionado a un parámetro ligado a
    un grupo de seguridad opcional: si el cliente ya lo usaba en 14.0 y no
    activamos esto, el dato sigue en la BD pero queda invisible/inaplicado
    en la UI tras el corte.

    TODO: verificar contra una instancia 17.0 real el valor exacto que
    espera este ir.config_parameter (¿'True'/'False' como string, o
    depende de la membresía a un res.groups concreto?) antes de dar este
    paso por definitivo -- de momento se deja el valor más plausible según
    el propio código del módulo.
    """
    if env["product.template"].search_count([("percent_waste", ">", 0)]):
        env["ir.config_parameter"].sudo().set_param(
            "product_task_material_work.active_group_percent_waste", "True"
        )


@openupgrade.migrate()
def migrate(env, version):
    _invert_apply_pricelist(env)
    _fix_merge_tasks(env)
    _activate_percent_waste_if_used(env)
