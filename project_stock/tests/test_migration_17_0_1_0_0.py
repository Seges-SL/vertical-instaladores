# Copyright 2026 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Tests de los scripts de la migración directa 14.0 -> 17.0 de este módulo
(migrations/17.0.1.0.0/*-migration.py).

Estos scripts no son parte del código normal del módulo -- Odoo/OpenUpgrade
los ejecuta aparte, una sola vez, durante la propia migración -- así que no
se cargan solos con el resto de tests. Aquí se importan por ruta de fichero
(sus nombres llevan guion, 'pre-migration.py'/'post-migration.py', así que
no se pueden importar con un 'import' normal) y se llama directamente a sus
funciones internas contra una tabla 'project_task_material' construida a
mano por SQL, simulando los datos que la migración real se encuentra en la
base de datos de un cliente al llegar desde 14.0.

Solo se cubre post-migration.py: el rename de pre-migration.py
('procurement_group_id' -> 'group_id') opera sobre la COLUMNA física de
project_task en el esquema previo a que project_stock aplique el suyo -- en
un test normal el módulo ya está cargado con el esquema de 17.0 (columna
'group_id', sin 'procurement_group_id'), así que no hay forma honesta de
ejercitarlo aquí sin fabricar un esquema falso; ese rename se verifica de
verdad en el ensayo real de la migración (ver OPENUPGRADE.md, Fase 1/2 en
Scripts-Odoo), no con un test unitario.

Se salta entero (no falla) cuando 'openupgradelib' no está instalado: solo
está presente en el entorno real de migración OpenUpgrade
('openupgrade_framework' como server_wide_module,
'requirements-openupgrade.txt' -- ver deploy_openupgrade_step.sh en
Scripts-Odoo), nunca en una ejecución normal de los tests del módulo.
"""
import importlib.util
import os
import unittest

from .common import TestProjectStockBase

try:
    import openupgradelib  # noqa: F401
except ImportError:
    openupgradelib = None


def _load_migration_script(filename):
    """Carga por ruta de fichero un script de migrations/17.0.1.0.0/ (sus
    nombres con guion no son importables con un 'import' normal)."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "migrations",
        "17.0.1.0.0",
        filename,
    )
    module_name = "project_stock_test_" + filename.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(
    openupgradelib,
    "openupgradelib no está instalado (solo disponible en el entorno real "
    "de migración OpenUpgrade)",
)
class TestMigration17010(TestProjectStockBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_migration = _load_migration_script("post-migration.py")
        # Tabla vieja de 14.0: aquí no la trae ningún módulo instalado (ni
        # project_task_material_stock_liyben_mig_mod ni el OCA
        # project_task_material están en el addons_path de este repo), así
        # que se fabrica a mano con las columnas que post-migration.py
        # necesita leer/escribir.
        cls.env.cr.execute(
            """
            CREATE TABLE IF NOT EXISTS project_task_material (
                id serial PRIMARY KEY,
                task_id integer,
                product_id integer,
                product_uom_id integer,
                quantity numeric,
                stock_move_id integer
            )
            """
        )

    def _create_bare_task(self, name="Test task migration"):
        """Tarea con los defaults de ubicación/tipo de operación del
        proyecto de test, pero sin ninguna línea de material -- equivalente
        a una tarea recién migrada, antes de que post-migration.py toque
        nada."""
        return (
            self.env["project.task"]
            .with_context(**self._prepare_context_task())
            .create({"name": name})
        )

    def _insert_project_task_material(
        self, task_id, product_id, quantity, product_uom_id=None, stock_move_id=None
    ):
        self.env.cr.execute(
            """
            INSERT INTO project_task_material
                (task_id, product_id, product_uom_id, quantity, stock_move_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (task_id, product_id, product_uom_id, quantity, stock_move_id),
        )
        return self.env.cr.fetchone()[0]

    def test_backfill_raw_material_task_id(self):
        """Filas CON stock_move_id: el enlace pasa de la fila vieja al
        propio stock.move."""
        task = self._create_bare_task()
        move = self.env["stock.move"].create(
            {
                "name": "Legacy move",
                "product_id": self.product_a.id,
                "product_uom_qty": 2,
                "product_uom": self.product_a.uom_id.id,
                "location_id": self.location.id,
                "location_dest_id": self.location_dest.id,
            }
        )
        # Estado anterior al backfill: en 14.0 el enlace con la tarea vivía
        # solo en project_task_material, no en el propio stock.move.
        self.assertFalse(move.raw_material_task_id)
        self._insert_project_task_material(
            task_id=task.id,
            product_id=self.product_a.id,
            quantity=2,
            product_uom_id=self.product_a.uom_id.id,
            stock_move_id=move.id,
        )

        self.post_migration._backfill_raw_material_task_id(self.env)

        move.invalidate_recordset()
        self.assertEqual(move.raw_material_task_id, task)

    def test_create_draft_moves_for_pending_materials(self):
        """Filas SIN stock_move_id: se crea un stock.move en borrador
        equivalente, con los mismos defaults que usaría la propia tarea."""
        task = self._create_bare_task()
        ptm_id = self._insert_project_task_material(
            task_id=task.id, product_id=self.product_b.id, quantity=4
        )

        self.post_migration._create_draft_moves_for_pending_materials(self.env)

        move = self.env["stock.move"].search(
            [
                ("raw_material_task_id", "=", task.id),
                ("product_id", "=", self.product_b.id),
            ]
        )
        self.assertEqual(len(move), 1)
        self.assertEqual(move.state, "draft")
        self.assertEqual(move.task_id, task)
        self.assertEqual(move.product_uom_qty, 4)
        # product_uom_id no se pasó (None) -- debe caer al uom del producto.
        self.assertEqual(move.product_uom, self.product_b.uom_id)
        self.assertEqual(move.location_id, self.location)
        self.assertEqual(move.location_dest_id, self.location_dest)
        self.assertEqual(move.picking_type_id, self.picking_type)
        self.assertTrue(move.group_id)
        self.assertEqual(task.group_id, move.group_id)

        # Idempotencia, parte 1: la fila vieja queda enlazada al nuevo
        # movimiento.
        self.env.cr.execute(
            "SELECT stock_move_id FROM project_task_material WHERE id = %s",
            (ptm_id,),
        )
        self.assertEqual(self.env.cr.fetchone()[0], move.id)

        # Idempotencia, parte 2: una segunda pasada no duplica nada (la
        # propia consulta ya excluye la fila, que ya tiene stock_move_id).
        self.post_migration._create_draft_moves_for_pending_materials(self.env)
        self.assertEqual(
            self.env["stock.move"].search_count(
                [
                    ("raw_material_task_id", "=", task.id),
                    ("product_id", "=", self.product_b.id),
                ]
            ),
            1,
        )

    def test_create_draft_moves_reuses_existing_group(self):
        """Si la tarea ya tenía grupo de aprovisionamiento, se reutiliza en
        vez de crear uno nuevo (mismo criterio que default_get)."""
        task = self._create_bare_task()
        group = self.env["procurement.group"].create({"name": "Existing group"})
        task.group_id = group.id
        self._insert_project_task_material(
            task_id=task.id, product_id=self.product_a.id, quantity=1
        )

        self.post_migration._create_draft_moves_for_pending_materials(self.env)

        move = self.env["stock.move"].search(
            [("raw_material_task_id", "=", task.id)]
        )
        self.assertEqual(move.group_id, group)

    def test_create_draft_moves_skips_orphan_rows(self):
        """Filas sin task_id: no hay a qué tarea enlazar el stock.move, no
        se crea nada (y no debe reventar)."""
        self._insert_project_task_material(
            task_id=None, product_id=self.product_a.id, quantity=1
        )
        move_count_before = self.env["stock.move"].search_count([])

        self.post_migration._create_draft_moves_for_pending_materials(self.env)

        self.assertEqual(
            self.env["stock.move"].search_count([]), move_count_before
        )

    def test_create_draft_moves_skips_rows_without_product(self):
        """Filas sin product_id: dato incompleto, se salta sin reventar."""
        task = self._create_bare_task()
        self._insert_project_task_material(
            task_id=task.id, product_id=None, quantity=1
        )

        self.post_migration._create_draft_moves_for_pending_materials(self.env)

        self.assertFalse(
            self.env["stock.move"].search([("raw_material_task_id", "=", task.id)])
        )
