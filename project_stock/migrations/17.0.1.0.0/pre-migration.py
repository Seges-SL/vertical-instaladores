# Copyright 2026 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Migración directa 14.0 -> 17.0 de project_stock (vendorizado de OCA/project
Tecnativa). El vertical-instaladores no tenía este módulo en 14.0 -- lo que
tenía era 'project_task_material_stock_liyben_mig_mod' (también vendorizado
de OCA, mismo propósito: enlazar materiales de una tarea con stock.move
reales), que desaparece de addons/custom al cambiar de rama y no vuelve a
aparecer aquí ni en ningún otro módulo del vertical en 17.0.

Dar de baja 'project_task_material_stock_liyben_mig_mod' (y, de paso,
'project_task_material' -- ver el docstring de post-migration.py de este
mismo módulo para por qué hace falta neutralizar también este segundo) en
ir_module_module NO va aquí -- Odoo construye el grafo de módulos a instalar
a partir de esa tabla ANTES de ejecutar ninguna migración, así que si esa
fila sigue en 'installed' sin carpeta en el addons_path (porque
addons/custom ya está en la rama 17.0, que no la trae) el arranque revienta
antes de llegar a este script. Tiene que resolverse con SQL directo desde
fuera de Odoo, en el mismo momento en que addons/custom cambia de rama --
ver scripts/openupgrade/run_final_hop.sh en la raíz de este repo, que
cierra el salto final generado por deploy_openupgrade_step.sh (repo
Scripts-Odoo) cambiando 'addons/custom' a la rama 17.0, neutralizando
ambos módulos (scripts/openupgrade/neutralize_replaced_modules.sh) y
reejecutando la migración de ese salto ya con el código correcto delante.
Vive en este repo y no en Scripts-Odoo porque ese script no re-clona ni
re-cambia de rama 'addons/custom' en ningún salto de su cadena -- lo deja
dicho su propio OPENUPGRADE.md como responsabilidad de este repo, no del
suyo. (Generalizar esto a un hook genérico dentro del propio
deploy_openupgrade_step.sh, reutilizable por cualquier vertical con el
mismo patrón, queda anotado como pendiente en el PENDING_OPENUPGRADE.md de
Scripts-Odoo -- de momento solo existe esta solución concreta para
vertical-instaladores.)

Lo que sí es responsabilidad de este script: 'procurement_group_id' (en
project.task, declarado por el módulo 14.0 de arriba) y 'group_id' (en
project.task, declarado por este mismo project_stock) son el mismo campo
con el mismo propósito -- mismo modelo, mismo tipo (Many2one a
procurement.group), solo cambia el nombre. La columna física sigue
existiendo en la tabla aunque el módulo que la declaró ya no esté
instalable: renombrar una columna no depende de que su módulo de origen
siga teniendo código en el addons_path.
"""
from openupgradelib import openupgrade

_FIELD_RENAMES = [
    ("project.task", "project_task", "procurement_group_id", "group_id"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _FIELD_RENAMES)
