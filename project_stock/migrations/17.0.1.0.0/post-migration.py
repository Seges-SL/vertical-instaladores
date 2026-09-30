# Copyright 2026 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Segunda mitad de la migración directa 14.0 -> 17.0 de project_stock.

En 14.0, cada material consumido por una tarea era una fila de
'project.task.material' (tabla project_task_material, declarada por el
módulo 14.0 'project_task_material_stock_liyben_mig_mod'), con su propio
'stock_move_id' apuntando al movimiento de stock real ya creado y su
'task_id' apuntando a la tarea.

En 17.0, project_stock no tiene modelo intermedio: el propio 'stock.move'
enlaza directo con la tarea vía 'raw_material_task_id'. (OJO: no confundir
con 'product.task.material' -- con 'd' -- que es un modelo NUEVO y sin
relación de product_task_material_work, la receta/BOM de materiales de un
producto compuesto, no las líneas de material ya consumidas por una tarea
concreta. Son tablas distintas, 'project_task_material' vs
'product_task_material', ninguna se pisa ni se borra por la otra).

Va en post, no en pre: la columna 'raw_material_task_id' no existe hasta
que el propio project_stock aplica su esquema nuevo.

La tabla 'project_task_material' (14.0) no se borra en ningún momento del
proceso -- ningún módulo de esta cadena de migración desinstala
'project_task_material_stock_liyben_mig_mod' de verdad (solo se le fuerza
el estado en ir_module_module para que Odoo no intente cargar su código,
ver pre-migration.py de este mismo módulo) -- así que sigue disponible
íntegra vía SQL crudo en este punto, y seguirá estándolo después del corte
por si hay que volver a consultarla.

Decisión de negocio (confirmada con el usuario): las filas de
project_task_material SIN stock_move_id -- material apuntado en la tarea
que en 14.0 nunca llegó a convertirse en un movimiento de stock real --
NO se dan por perdidas. Se les crea su 'stock.move' equivalente aquí, en
estado 'draft', para que el usuario las revise y confirme ya en 17.0 desde
la propia tarea (ver _create_draft_moves_for_pending_materials).

OJO módulo 'project_task_material' (el OCA base, con 'stock_move_id' como
único puente hacia stock -- no confundir con
'project_task_material_stock_liyben_mig_mod', que es quien monta el
puente): a diferencia de este último, si que existe también en 17.0
(mismo repo OCA/project, rama 17.0) y por tanto SU código sí está
disponible en el addons_path de destino. Sin neutralizarlo aparte, Odoo lo
trataría como un módulo instalado más a migrar/actualizar con normalidad
-- quedando activo en 17.0 en paralelo a project_stock, que ya cubre lo
mismo (el enlace directo 'stock.move.raw_material_task_id') sin el modelo
intermedio. Igual que con project_task_material_stock_liyben_mig_mod, la
baja de su fila en ir_module_module tiene que forzarse por SQL directo
desde fuera de Odoo, antes de que arranque y construya el grafo de
módulos -- ver scripts/openupgrade/run_final_hop.sh en la raíz de este
repo (usa neutralize_replaced_modules.sh, que fuerza ambas filas a la
vez, como parte del cierre del salto final -- ver pre-migration.py de
este mismo módulo para el porqué de que viva en este repo). Mientras esa
baja no esté hecha, el modelo 'project.task.material' seguirá registrado
con normalidad en el ORM; este script usa SQL crudo contra la tabla en
vez de env['project.task.material'] precisamente para no depender de que
el módulo siga instalado en el momento en que esto se ejecute.
"""
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _backfill_raw_material_task_id(env):
    """Traslada el enlace tarea<->stock.move ya existente en 14.0 (a
    través de la fila de project.task.material que lo mediaba) al enlace
    directo de 17.0. Solo cubre las filas que YA tenían un stock.move real
    creado (stock_move_id no nulo) -- ver
    _create_draft_moves_for_pending_materials para las que no.
    """
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE stock_move sm
        SET raw_material_task_id = ptm.task_id
        FROM project_task_material ptm
        WHERE ptm.stock_move_id = sm.id
          AND ptm.task_id IS NOT NULL
        """,
    )


def _create_draft_moves_for_pending_materials(env):
    """Para cada fila de 'project_task_material' que en 14.0 se quedó sin
    stock_move_id (material apuntado en la tarea pero nunca consumido de
    verdad -- el 'todo_lines' de project_task_material_stock_liyben_mig_mod),
    crea aquí su 'stock.move' equivalente en 17.0, en estado 'draft'.

    Los valores se rellenan replicando exactamente lo que hacen
    'project.task.default_get()' y el resto de este módulo cuando un
    usuario añade una línea de material desde la propia tarea (ver
    project_task.py y stock_move.py): mismo almacén/ubicación origen y
    destino, mismo tipo de operación, mismo grupo de aprovisionamiento (se
    crea uno para la tarea si todavía no tiene ninguno) -- así el
    resultado es indistinguible de un movimiento creado a mano, listo para
    que el usuario lo revise y confirme ya en 17.0.

    Solo cubre filas con task_id: las que además no tienen tarea son
    huérfanas de origen (no debieron poder guardarse así en 14.0) y no hay
    a qué enlazar el stock.move nuevo -- se listan aparte por log, sin
    crear nada para ellas.

    Idempotente: tras crear cada stock.move se rellena el stock_move_id de
    la fila vieja correspondiente, así que una reejecución de este script
    no vuelve a duplicar nada (la propia consulta ya las excluye).
    """
    env.cr.execute(
        """
        SELECT id, task_id, product_id, product_uom_id, quantity
        FROM project_task_material
        WHERE stock_move_id IS NULL
        ORDER BY id
        """
    )
    rows = env.cr.dictfetchall()
    if not rows:
        return

    orphan_rows = [row for row in rows if not row["task_id"]]
    pending_rows = [row for row in rows if row["task_id"]]

    if orphan_rows:
        _logger.warning(
            "project_stock: %s fila(s) de project_task_material sin "
            "stock_move_id NI task_id -- no se les puede crear un "
            "stock.move (no hay tarea a la que enlazarlo). IDs: %s",
            len(orphan_rows),
            [row["id"] for row in orphan_rows],
        )

    task_ids = {row["task_id"] for row in pending_rows}
    tasks_by_id = {task.id: task for task in env["project.task"].browse(task_ids)}
    # Grupos de aprovisionamiento ya creados en esta misma pasada, para no
    # crear uno nuevo por cada línea de material de una tarea que todavía
    # no tuviera -- mismo criterio que 'default_get'.
    groups_created = {}

    created = 0
    for row in pending_rows:
        task = tasks_by_id.get(row["task_id"])
        if not task or not task.exists():
            _logger.warning(
                "project_stock: project_task_material.id=%s apunta a una "
                "task_id=%s que ya no existe -- no se crea stock.move.",
                row["id"],
                row["task_id"],
            )
            continue
        if not row["product_id"]:
            _logger.warning(
                "project_stock: project_task_material.id=%s no tiene "
                "product_id -- no se crea stock.move.",
                row["id"],
            )
            continue

        group = task.group_id or groups_created.get(task.id)
        if not group:
            group = env["procurement.group"].create(
                task._prepare_procurement_group_vals()
            )
            task.group_id = group.id
            groups_created[task.id] = group

        product = env["product.product"].browse(row["product_id"])
        move_vals = {
            "raw_material_task_id": task.id,
            "task_id": task.id,
            "group_id": group.id,
            "product_id": product.id,
            "name": task.name,
            "product_uom_qty": row["quantity"] or 0.0,
            "product_uom": row["product_uom_id"] or product.uom_id.id,
            "location_id": (
                task.location_id.id or task.project_id.location_id.id
            ),
            "location_dest_id": (
                task.location_dest_id.id or task.project_id.location_dest_id.id
            ),
            "picking_type_id": (
                task.picking_type_id.id or task.project_id.picking_type_id.id
            ),
            "company_id": task.company_id.id,
            "state": "draft",
        }
        move = env["stock.move"].sudo().create(move_vals)
        openupgrade.logged_query(
            env.cr,
            "UPDATE project_task_material SET stock_move_id = %s WHERE id = %s",
            (move.id, row["id"]),
        )
        created += 1

    _logger.info(
        "project_stock: %s stock.move en borrador creado(s) a partir de "
        "filas de project_task_material sin stock_move_id.",
        created,
    )


@openupgrade.migrate()
def migrate(env, version):
    _backfill_raw_material_task_id(env)
    _create_draft_moves_for_pending_materials(env)
