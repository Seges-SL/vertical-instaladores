# vertical-instaladores — contexto para Claude

## Datos del repositorio
- Tipo de repositorio: repositorio común de módulos propios
- Cliente: (no aplica)
- Versión de Odoo: 17.0
- Licencia para módulos nuevos: AGPL-3 (https://www.gnu.org/licenses/agpl-3.0)
- Autor en el manifest: Seges
- Código de referencia (solo lectura, para consultar; no sirve para ejecutar Odoo). Contiene
  todo el código de cada rama (solo faltan traducciones y estáticos); si un módulo no está,
  no existe en esa rama:
  - /opt/odoo-src/17.0
  - /opt/odoo-src/14.0
  - /opt/odoo-src/migracion
  (se crea y actualiza con `./preparar_equipo.sh referencias` desde el kit)

## Dependencias
- Repos compartidos: `third_party` (rama 17.0).
- OCA: lista estándar de la empresa (`referencias.conf` del kit).
- Repos OCA adicionales de este cliente: (ninguno)
  <!-- Si hay alguno, añádelo aquí y también a OCA_EXTRA_17 en referencias.conf del kit. -->

## Convenciones de este repo
- Las especificaciones de módulos se guardan en `docs/specs/<modulo>.md`.
- Cualquier módulo nuevo sigue las skills `odoo-comun` y `odoo-17-conventions`.
- No hagas `git commit` ni `git push`.
- IMPORTANTE: `/opt/odoo-src/17.0/vertical-instaladores` es una copia de referencia de ESTE repo (la versión publicada). No la consultes: trabaja siempre con los archivos locales del repo.
  La copia `/opt/odoo-src/14.0/vertical-instaladores` sí es válida: es el origen de la migración.

## Migración 14.0 → 17.0 (OpenUpgrade)
- Migración en curso. Convenciones: skill `odoo-migracion`. Flujo: `/odoo-migrar <modulo>`.
- Origen (14.0), solo consulta: `/opt/odoo-src/14.0` (core, compartidos y OCA en 14.0).
- Referencias de migración: `/opt/odoo-src/migracion` (OpenUpgrade 15/16/17, openupgradelib y
  Scripts-Odoo `odoo-infra-14`/`odoo-infra-17` con `OPENUPGRADE.md` y `PENDING_OPENUPGRADE.md`).
- Documento vivo: `MIGRATION_14_TO_17.md` en la raíz del repo.

## Pruebas
Dos etapas:

1. **Local, con `odoo-dev`** (entorno Docker del kit). Aquí se instala, se prueba y se depura.
   - Preparar el contexto: `odoo-dev 17 arrancar` desde la raíz de este repo
     (monta este repo, los compartidos y OCA; base de datos `vertical_instaladores_17`).
   - Instalar / actualizar: `odoo-dev 17 instalar <modulo>` · `odoo-dev 17 actualizar <modulo>`
   - Tests: `odoo-dev 17 tests <modulo>` (base de datos de tests nueva cada vez)
   - Log del servidor: `odoo-dev 17 log` · Interfaz: http://localhost:8069
   - Lint de lo cambiado: `python3 ~/.claude/hooks/odoo_lint.py --revisar <modulo>/`
   - No arranques Odoo de ninguna otra forma. Cargar bases de datos (`bd-cargar`) lo decide
     siempre el usuario.
2. **VPS de pruebas del cliente**: validación con datos reales. Al terminar una tarea, entrega
   un plan de prueba: qué módulos actualizar allí y qué casos comprobar en la interfaz.
