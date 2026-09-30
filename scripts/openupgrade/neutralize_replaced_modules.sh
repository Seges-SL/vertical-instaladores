#!/bin/bash
# --------------------------------------------------------------------------------
# NEUTRALIZACIÓN DE MÓDULOS 14.0 QUE NO TIENEN CÓDIGO EN LA RAMA 17.0
#
# La migración directa 14.0 -> 17.0 de este repo deja varios módulos que
# estaban instalados en 14.0 sin carpeta en el addons_path de 17.0. Si su
# fila en ir_module_module sigue en 'installed' cuando Odoo arranca contra
# la BD ya migrada, el arranque REVIENTA (Odoo construye el grafo de
# módulos a partir de esa tabla ANTES de ejecutar ninguna migración, y no
# puede cargar un módulo instalado sin código). Este script fuerza esas
# filas a 'uninstalled' por SQL directo, SIN pasar por el uninstall real
# de Odoo (que arrastraría un unlink en cascada). Solo toca el registro
# del módulo: las tablas y sus datos quedan intactos.
#
# Módulos neutralizados:
#
#   - project_task_material_stock_liyben_mig_mod (vendorizado, propio del
#     vertical): "enlazar materiales de una tarea con stock.move reales".
#     Sustituido en 17.0 por project_stock (enlace directo
#     'stock.move.raw_material_task_id'). Ver project_stock/migrations/
#     17.0.1.0.0/*-migration.py.
#
#   - project_task_material (OCA, repo OCA/project): a diferencia del
#     anterior, SÍ existe también en la rama 17.0 de OCA/project -- su
#     código está en el addons_path, así que no revienta el arranque, pero
#     sin neutralizarlo Odoo lo dejaría activo EN PARALELO a project_stock,
#     duplicando la misma funcionalidad. La tabla física
#     'project_task_material' se conserva: project_stock la lee por SQL en
#     su propio post-migration.
#
#   - product_task_material_work_category (propio del vertical): en 14.0
#     añadía la tarifa a nivel de la CATEGORÍA del compuesto + coste vía
#     supplierinfo. product_task_material_work 17.0 NO reimplementa eso y
#     NO lo fusiona (ver product_task_material_work/migrations/17.0.1.0.1/
#     pre-migration.py). Neutralización INTERINA: la feature no existe en
#     17.0 hasta que se cree el módulo propio 17.0. Su campo
#     'apply_category' queda respaldado por el pre-migration de
#     product_task_material_work (si la columna existía).
#
# CUÁNDO EJECUTARLO (crítico): justo después de restaurar el volcado de BD
# en el entorno cuyo addons/custom YA sirve la rama 17.0 de
# vertical-instaladores, y SIEMPRE antes de que Odoo arranque contra esa
# base de datos (antes de cualquier 'odoo -u all', incluida la propia
# migración OpenUpgrade). Si Odoo llega a arrancar antes con alguna de
# estas filas todavía en 'installed', el arranque revienta y ya no hay
# manera de llegar a ejecutar este script sobre esa base de datos sin
# restaurar el volcado de nuevo.
#
# OJO: 'deploy_openupgrade_step.sh' (repo Scripts-Odoo) NO re-clona ni
# re-cambia de rama 'addons/custom' en ningún salto de su cadena -- lo deja
# dicho explícitamente OPENUPGRADE.md de ese repo, como responsabilidad del
# propio repo del vertical. Lo llama scripts/openupgrade/run_final_hop.sh,
# que cambia addons/custom a la rama 17.0 y luego invoca este script antes
# del -u all.
#
# Uso:
#   ./scripts/openupgrade/neutralize_replaced_modules.sh <contenedor_bd> <nombre_bd> [usuario_bd=odoo]
#
# Ejemplo:
#   ./scripts/openupgrade/neutralize_replaced_modules.sh upgrade_cliente_v17_db upgrade.cliente.com_v17.0
# --------------------------------------------------------------------------------

MODULES_TO_NEUTRALIZE=(
    "project_task_material_stock_liyben_mig_mod"
    "project_task_material"
    "product_task_material_work_category"
)

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Uso: $0 <contenedor_postgres> <nombre_bd> [usuario_postgres=odoo]"
    exit 1
fi

DB_CONTAINER="$1"
DB_NAME="$2"
DB_USER="${3:-odoo}"

IN_CLAUSE=$(printf "'%s'," "${MODULES_TO_NEUTRALIZE[@]}")
IN_CLAUSE="${IN_CLAUSE%,}"

echo "========================================================"
echo "🔒 NEUTRALIZACIÓN DE MÓDULOS 14.0 SIN CÓDIGO EN 17.0"
echo "   Contenedor: $DB_CONTAINER"
echo "   Base de datos: $DB_NAME"
echo "   Módulos: ${MODULES_TO_NEUTRALIZE[*]}"
echo "========================================================"

echo ">> Estado ANTES:"
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT name, state FROM ir_module_module WHERE name IN ($IN_CLAUSE) ORDER BY name;"

echo ">> Forzando 'uninstalled' (SQL directo, sin tocar tablas de datos)..."
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -c \
    "UPDATE ir_module_module SET state = 'uninstalled' WHERE name IN ($IN_CLAUSE);"

echo ">> Estado DESPUÉS:"
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT name, state FROM ir_module_module WHERE name IN ($IN_CLAUSE) ORDER BY name;"

echo "========================================================"
echo "✅ Neutralización completada. Las tablas de datos de estos módulos"
echo "   siguen intactas -- solo se ha tocado el registro del módulo."
echo "========================================================"
