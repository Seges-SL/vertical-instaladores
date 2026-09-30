# Copyright 2026 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Tests de los scripts de la migración directa 14.0 -> 17.0 de este módulo
(migrations/17.0.1.0.1/*-migration.py). Mismo enfoque que
project_stock/tests/test_migration_17_0_1_0_0.py: se cargan por ruta de
fichero (nombres con guion, no importables con un 'import' normal) y se
ejercitan sus funciones contra datos fabricados a mano para simular lo que
un pre-migration.py real deja para que post-migration.py lo consuma.

No todo es honestamente testeable así -- se deja fuera, con el mismo
criterio ya aplicado al rename de pre-migration.py de project_stock:
- openupgrade.update_module_names (fusión de módulos): delegado entero a
  openupgradelib, no a lógica de este repo -- en vez de eso se verifica
  por saneamiento de datos que _MERGED_MODULES está bien formado.
- openupgrade.rename_fields ('sign_by' -> 'signed_by'): opera sobre el
  esquema anterior a que este módulo aplique el suyo propio.

Lo que SÍ se cubre, porque es lógica propia (no de openupgradelib):
- El forzado a 'to install' de los módulos extraídos de este mismo módulo.
- _backup_legacy_columns no revienta cuando las columnas 14.0 a respaldar
  no existen (módulo de origen no instalado).
- _invert_apply_pricelist: inversión acotada a productos partida.
- _fix_merge_tasks: poblado de la tabla M2M nueva desde la FK legacy.
- _activate_percent_waste_if_used: activación condicional del parámetro.

Se salta entero (no falla) si 'openupgradelib' no está instalado -- solo
está presente en el entorno real de migración OpenUpgrade, nunca en una
ejecución normal de los tests del módulo.
"""
import importlib.util
import os
import unittest

from odoo.tests.common import TransactionCase

try:
    import openupgradelib  # noqa: F401
except ImportError:
    openupgradelib = None


def _load_migration_script(filename):
    """Carga por ruta de fichero un script de migrations/17.0.1.0.1/ (sus
    nombres con guion no son importables con un 'import' normal)."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "migrations",
        "17.0.1.0.1",
        filename,
    )
    module_name = "ptmw_test_" + filename.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(
    openupgradelib,
    "openupgradelib no está instalado (solo disponible en el entorno real "
    "de migración OpenUpgrade)",
)
class TestMigration17011(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pre_migration = _load_migration_script("pre-migration.py")
        cls.post_migration = _load_migration_script("post-migration.py")
        # Columna "legacy" que en una migración real deja pre-migration.py
        # (rename_columns con new=None -> get_legacy_name()) para que
        # _fix_merge_tasks la consuma. Aquí no hay pre-migration.py real
        # que la cree, así que se fabrica a mano con el mismo nombre que
        # get_legacy_name('merged_parent_id') produce para 17.0.
        cls.env.cr.execute(
            "ALTER TABLE project_task "
            "ADD COLUMN IF NOT EXISTS openupgrade_legacy_17_0_merged_parent_id integer"
        )

    # -- pre-migration.py --------------------------------------------------

    def test_merged_modules_target_this_module(self):
        """_MERGED_MODULES bien formado: todas las entradas se fusionan
        hacia 'product_task_material_work', sin nombres repetidos ni un
        módulo fusionándose consigo mismo. No ejercita
        openupgrade.update_module_names en sí -- esa es responsabilidad de
        openupgradelib -- solo la lista de datos que le pasamos."""
        merged = self.pre_migration._MERGED_MODULES
        self.assertTrue(merged)
        old_names = [old for old, _new in merged]
        self.assertEqual(
            len(old_names), len(set(old_names)), "nombre repetido en _MERGED_MODULES"
        )
        for old, new in merged:
            self.assertEqual(new, "product_task_material_work")
            self.assertNotEqual(old, new)

    def test_category_module_not_merged(self):
        """product_task_material_work_category NO se fusiona aquí: en 17.0
        se queda como módulo propio pendiente de reimplementar y se
        neutraliza aparte (neutralize_replaced_modules.sh)."""
        merged_old_names = {old for old, _new in self.pre_migration._MERGED_MODULES}
        self.assertNotIn("product_task_material_work_category", merged_old_names)

    def test_new_dependent_modules_no_overlap_with_merged(self):
        """Un módulo no puede estar a la vez fusionado (desaparece) y
        forzado a instalar (nuevo) -- serían instrucciones contradictorias
        para la misma fila de ir_module_module."""
        merged_old_names = {old for old, _new in self.pre_migration._MERGED_MODULES}
        new_modules = self.pre_migration._NEW_DEPENDENT_MODULES
        self.assertEqual(
            len(new_modules),
            len(set(new_modules)),
            "nombre repetido en _NEW_DEPENDENT_MODULES",
        )
        self.assertFalse(merged_old_names & set(new_modules))

    def test_force_install_new_dependent_modules(self):
        modules = self.pre_migration._NEW_DEPENDENT_MODULES
        self.env.cr.execute(
            "UPDATE ir_module_module SET state = 'uninstalled' WHERE name IN %s",
            (modules,),
        )

        self.pre_migration._force_install_new_dependent_modules(self.env.cr)

        self.env.cr.execute(
            "SELECT name, state FROM ir_module_module WHERE name IN %s", (modules,)
        )
        states_by_name = dict(self.env.cr.fetchall())
        for name in modules:
            self.assertIn(
                name,
                states_by_name,
                "%s no tiene fila en ir_module_module en este entorno de "
                "test -- ¿su carpeta está en el addons_path?" % name,
            )
            self.assertEqual(states_by_name[name], "to install")

    def test_backup_legacy_columns_skips_missing(self):
        """Si el módulo 14.0 que declaraba una columna a respaldar no
        estaba instalado, la columna original no existe y
        _backup_legacy_columns no debe reventar -- simplemente no renombra
        nada. En un 17.0 normal ni 'merged_parent_id' ni 'apply_category'
        existen ya en sus tablas."""
        self.pre_migration._backup_legacy_columns(self.env.cr)  # no debe lanzar

    # -- post-migration.py ----------------------------------------------

    def test_invert_apply_pricelist(self):
        partida_true = self.env["product.template"].create(
            {"name": "Partida apply_pricelist True", "type": "service"}
        )
        partida_false = self.env["product.template"].create(
            {"name": "Partida apply_pricelist False", "type": "service"}
        )
        partida_null = self.env["product.template"].create(
            {"name": "Partida apply_pricelist NULL", "type": "service"}
        )
        non_partida = self.env["product.template"].create(
            {"name": "No partida apply_pricelist True", "type": "service"}
        )
        self.env.cr.execute(
            "UPDATE product_template SET service_tracking = 'task_in_project', "
            "apply_pricelist = true WHERE id = %s",
            (partida_true.id,),
        )
        self.env.cr.execute(
            "UPDATE product_template SET service_tracking = 'task_global_project', "
            "apply_pricelist = false WHERE id = %s",
            (partida_false.id,),
        )
        self.env.cr.execute(
            "UPDATE product_template SET service_tracking = 'task_in_project', "
            "apply_pricelist = NULL WHERE id = %s",
            (partida_null.id,),
        )
        self.env.cr.execute(
            "UPDATE product_template SET service_tracking = 'no', "
            "apply_pricelist = true WHERE id = %s",
            (non_partida.id,),
        )

        self.post_migration._invert_apply_pricelist(self.env)

        for rec in (partida_true, partida_false, partida_null, non_partida):
            rec.invalidate_recordset()
        self.assertFalse(partida_true.apply_pricelist)  # True -> False
        self.assertTrue(partida_false.apply_pricelist)  # False -> True
        self.assertTrue(partida_null.apply_pricelist)  # NULL (=False) -> True
        self.assertTrue(non_partida.apply_pricelist)  # no partida -> sin tocar

    def test_fix_merge_tasks(self):
        project = self.env["project.project"].create({"name": "Test project migration"})
        parent = self.env["project.task"].create(
            {"name": "Parent task", "project_id": project.id}
        )
        child = self.env["project.task"].create(
            {"name": "Child task", "project_id": project.id}
        )
        other = self.env["project.task"].create(
            {"name": "Standalone task", "project_id": project.id}
        )
        self.env.cr.execute(
            "UPDATE project_task "
            "SET openupgrade_legacy_17_0_merged_parent_id = %s WHERE id = %s",
            (parent.id, child.id),
        )

        self.post_migration._fix_merge_tasks(self.env)

        parent.invalidate_recordset()
        self.assertIn(child, parent.merge_task_ids)
        self.assertNotIn(other, parent.merge_task_ids)

    def test_activate_percent_waste_if_used(self):
        # Nota: esto solo verifica el CONTRATO actual de la función (deja
        # el parámetro en la cadena "True"), no que ese sea el valor que de
        # verdad espera el resto del módulo para activar el grupo -- eso
        # sigue siendo el TODO sin cerrar documentado en el propio
        # post-migration.py y en MIGRATION_14_TO_17.md.
        param_key = "product_task_material_work.active_group_percent_waste"
        self.env["ir.config_parameter"].sudo().search([("key", "=", param_key)]).unlink()
        self.env["product.template"].create({"name": "No waste", "percent_waste": 0.0})

        self.post_migration._activate_percent_waste_if_used(self.env)
        self.assertFalse(
            self.env["ir.config_parameter"].sudo().get_param(param_key),
            "no debería activarse si ningún producto usaba percent_waste",
        )

        self.env["product.template"].create({"name": "With waste", "percent_waste": 5.0})
        self.post_migration._activate_percent_waste_if_used(self.env)
        self.assertEqual(
            self.env["ir.config_parameter"].sudo().get_param(param_key), "True"
        )
