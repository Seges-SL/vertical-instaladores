#!/bin/bash
# --------------------------------------------------------------------------------
# CIERRE DEL SALTO FINAL (v16.0 -> v17.0) PARA vertical-instaladores
#
# 'deploy_openupgrade_step.sh' (repo Scripts-Odoo) genera el salto final
# v17.0 con 'addons/custom' arrastrado tal cual desde la producción de
# origen (rama 14.0) -- NO lo re-clona ni le cambia de rama en ningún
# salto de su cadena (ver OPENUPGRADE.md de ese repo, sección "Sobre
# vertical-instaladores": es responsabilidad de este repo, no del suyo).
# Eso significa que, tal cual sale de deploy_openupgrade_step.sh, el
# salto v17.0 arranca su '-u all' con el addons/custom de la rama 14.0:
# sin los módulos nuevos del vertical (project_stock, etc.) y con los
# módulos 14.0 sin código en 17.0 todavía 'installed' -- justo lo
# contrario de lo que se quiere.
#
# Este script cierra ese hueco para el salto YA GENERADO por
# deploy_openupgrade_step.sh (asume que ese script ya construyó la imagen
# Docker y levantó el contenedor de BD de este salto -- no vuelve a hacer
# nada de eso, solo reutiliza lo que ya existe):
#   1. Cambia 'addons/custom' de ESTE salto a la rama 17.0 real.
#   2. Neutraliza los módulos 14.0 sin código en 17.0
#      (neutralize_replaced_modules.sh) ANTES de volver a tocar Odoo --
#      con su fila todavía 'installed' sin código, Odoo revienta al
#      arrancar.
#   3. Reejecuta el '-u all' de este salto. Volver a lanzarlo sobre una BD
#      que ya pasó por él una vez es la operación normal y segura de
#      OpenUpgrade (los módulos ya al día no hacen nada); la diferencia es
#      que esta vez el addons_path ya tiene el código 17.0 del vertical,
#      así que sus pre/post-migration.py corren por primera vez.
#
# Uso:
#   ./scripts/openupgrade/run_final_hop.sh <directorio_del_salto_v17.0> [ruta_del_checkout_del_vertical_dentro_del_salto=addons/custom/vertical-instaladores]
#
# Ejemplo:
#   ./scripts/openupgrade/run_final_hop.sh /opt/odoo_upgrade/upgrade_cliente_com_v17.0
# --------------------------------------------------------------------------------

HOP_DIR="$1"
CUSTOM_REPO_RELPATH="${2:-addons/custom/vertical-instaladores}"

if [ -z "$HOP_DIR" ]; then
    echo "Uso: $0 <directorio_del_salto_v17.0> [ruta_del_checkout_del_vertical_dentro_del_salto]"
    exit 1
fi

if [ ! -f "$HOP_DIR/docker-compose.yml" ]; then
    echo "❌ No parece un directorio de salto de deploy_openupgrade_step.sh (falta docker-compose.yml): $HOP_DIR"
    exit 1
fi

CUSTOM_DIR="$HOP_DIR/$CUSTOM_REPO_RELPATH"
if [ ! -d "$CUSTOM_DIR/.git" ]; then
    echo "❌ No se encuentra un checkout git de vertical-instaladores en: $CUSTOM_DIR"
    echo "   Si en tu servidor 'addons/custom' tiene otra estructura, pasa la ruta"
    echo "   correcta como segundo parámetro."
    exit 1
fi

DB_CONTAINER=$(grep "container_name:.*_db" "$HOP_DIR/docker-compose.yml" | head -1 | awk '{print $2}')
DB_NAME=$(grep -oP '^db_name\s*=\s*\K.*' "$HOP_DIR/config/odoo.conf" | tr -d ' \r')

if [ -z "$DB_CONTAINER" ] || [ -z "$DB_NAME" ]; then
    echo "❌ No se pudo detectar el contenedor de BD (docker-compose.yml) o el nombre"
    echo "   de la BD (config/odoo.conf, clave db_name) en: $HOP_DIR"
    exit 1
fi

if ! docker exec "$DB_CONTAINER" pg_isready -U odoo > /dev/null 2>&1; then
    echo "❌ El contenedor de BD '$DB_CONTAINER' no responde. ¿Está levantado"
    echo "   ('docker compose up -d $DB_CONTAINER' dentro de $HOP_DIR)?"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================================"
echo "🏁 CIERRE DEL SALTO FINAL PARA vertical-instaladores"
echo "   Salto:      $HOP_DIR"
echo "   Checkout:   $CUSTOM_DIR"
echo "   Contenedor: $DB_CONTAINER"
echo "   Base datos: $DB_NAME"
echo "========================================================"

echo ">> 1/3 Cambiando '$CUSTOM_REPO_RELPATH' a la rama 17.0..."
if ! git -C "$CUSTOM_DIR" fetch origin 17.0 --quiet; then
    echo "❌ No se pudo hacer fetch de la rama 17.0 en $CUSTOM_DIR"
    exit 1
fi
if ! git -C "$CUSTOM_DIR" checkout 17.0 --quiet; then
    echo "❌ No se pudo hacer checkout de la rama 17.0 en $CUSTOM_DIR"
    exit 1
fi

echo ">> 2/3 Neutralizando módulos 14.0 sin código en 17.0..."
if ! "$SCRIPT_DIR/neutralize_replaced_modules.sh" "$DB_CONTAINER" "$DB_NAME"; then
    echo "❌ La neutralización ha fallado -- no se continúa con la migración."
    exit 1
fi

echo ">> 3/3 Reejecutando la migración de este salto (ahora con el código 17.0 del vertical presente)..."
if ! (cd "$HOP_DIR" && docker compose run --rm web odoo -u all -d "$DB_NAME" --stop-after-init --logfile=/dev/stdout --log-level=info); then
    echo "❌ La reejecución de '-u all' ha fallado. Revisa el log de arriba."
    exit 1
fi

echo "========================================================"
echo "✅ Salto final cerrado: addons/custom en rama 17.0, módulos 14.0"
echo "   sin código en 17.0 neutralizados, migraciones del vertical corridas."
echo "   Si el stack de revisión de este salto ya estaba levantado"
echo "   ('docker compose up -d'), reinícialo para que recoja las vistas"
echo "   y menús nuevos:"
echo "     cd $HOP_DIR && docker compose restart web"
echo "========================================================"
