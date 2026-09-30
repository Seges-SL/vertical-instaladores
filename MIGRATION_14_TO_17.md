# Migración 14.0 → 17.0

Referencia única de todo lo que la migración directa 14.0 → 17.0 de
`vertical-instaladores` cambia respecto a la versión 14, y de las
herramientas que lo ejecutan. Es un documento vivo: se actualiza según se
van escribiendo más scripts de migración para el resto de módulos del
vertical (ver [§8](#8-pendiente--limitaciones-conocidas)).

Para el procedimiento genérico de migración con OpenUpgrade (fases, scripts
de despliegue, manifiesto de commits, corte a producción) ver
`OPENUPGRADE.md` y `PENDING_OPENUPGRADE.md` del repo `Scripts-Odoo` — este
documento cubre solo lo específico de `vertical-instaladores`: qué cambia
en sus propios módulos y qué hay que hacer, aparte de la cadena genérica,
para que ese cambio se aplique bien.

## Índice

1. [Alcance y por qué es una migración directa](#1-alcance-y-por-qué-es-una-migración-directa)
2. [Mapa de módulos 14.0 → 17.0](#2-mapa-de-módulos-140--170)
3. [`project_stock`](#3-project_stock-nuevo-en-170)
4. [`product_task_material_work`](#4-product_task_material_work)
5. [Neutralización de módulos sustituidos](#5-neutralización-de-módulos-sustituidos)
6. [Runbook completo](#6-runbook-completo-140--170)
7. [Tests](#7-tests)
8. [Pendiente / limitaciones conocidas](#8-pendiente--limitaciones-conocidas)

---

## 1. Alcance y por qué es una migración directa

`vertical-instaladores` solo tiene rama en `14.0` y `17.0` — no ha existido
nunca en `15.0`/`16.0`, así que no tiene sentido (ni es posible) escribir
migraciones para esos escalones intermedios. La cadena de OpenUpgrade sigue
pasando por ellos igualmente (v14→v15→v16→v17, porque así lo exige
OpenUpgrade para el núcleo/OCA), pero durante esos saltos intermedios
`addons/custom` viaja **sin cambios**, todavía en su contenido de la rama
`14.0` — `deploy_openupgrade_step.sh` no lo re-clona ni le cambia de rama en
ningún salto (documentado en `OPENUPGRADE.md` de `Scripts-Odoo`). Los
scripts de este repo, por tanto, solo se ejecutan una vez, de verdad, en el
momento en que `addons/custom` pasa a servir la rama `17.0` — ver
[§5](#5-neutralización-de-módulos-sustituidos) y [§6](#6-runbook-completo-140--170)
para cuándo es exactamente ese momento hoy.

## 2. Mapa de módulos 14.0 → 17.0

| Módulo en 14.0 | Qué pasa en 17.0 | Gestionado por |
|---|---|---|
| `project_task_material_stock_liyben_mig_mod` (vendorizado) | Desaparece; su código no vuelve a existir en ningún módulo del vertical en 17.0 | Neutralización — [§5](#5-neutralización-de-módulos-sustituidos) |
| `project_task_material` (OCA, `OCA/project`) | Sigue existiendo como módulo OCA en la rama 17.0 de ese repo, pero se fuerza a no instalarse — sustituido por `project_stock` | Neutralización — [§5](#5-neutralización-de-módulos-sustituidos) |
| *(no existía)* | `project_stock` (OCA `OCA/project`, vendorizado con cambios propios) — enlace directo `stock.move.raw_material_task_id`, sin modelo intermedio | [`project_stock/migrations/17.0.1.0.0/`](project_stock/migrations/17.0.1.0.0/) — [§3](#3-project_stock-nuevo-en-170) |
| `merge_pt` | Fusionado dentro de `product_task_material_work` | [`product_task_material_work/migrations/17.0.1.0.1/`](product_task_material_work/migrations/17.0.1.0.1/) — [§4](#4-product_task_material_work) |
| `product_price_with_waste` | Fusionado dentro de `product_task_material_work` | ídem |
| `print_options_to_false_account_move_line` | Fusionado dentro de `product_task_material_work` | ídem |
| `sale_order_invoicing_finished_fix_translation` | Fusionado dentro de `product_task_material_work` | ídem |
| `sale_order_invoicing_finished_merge_task` | Fusionado dentro de `product_task_material_work` | ídem |
| `product_task_material_work_category` | **No** se fusiona. Su funcionalidad (tarifa a nivel de la categoría del compuesto + coste vía `supplierinfo`) no se reimplementa en 17.0 todavía. Neutralización interina; queda como módulo propio pendiente de reimplementar | Neutralización — [§5](#5-neutralización-de-módulos-sustituidos) · [§8](#8-pendiente--limitaciones-conocidas) |
| *(nuevos, extraídos de `product_task_material_work`)*: `crm_lead_to_project_task`, `project_task_to_sale_order`, `project_task_by_administration`, `resume_material_and_work`, `comparisons_sale_order` | Forzados a `to install` en la misma pasada de `-u all` que fusiona los de arriba | ídem |

## 3. `project_stock` (nuevo en 17.0)

Sustituye a `project_task_material_stock_liyben_mig_mod` (14.0, propio del
vertical) + `project_task_material` (OCA base). En 14.0, cada material
consumido por una tarea era una fila de `project.task.material`
(tabla `project_task_material`) con su propio `stock_move_id` apuntando al
movimiento de stock real. En 17.0 no hay modelo intermedio: el propio
`stock.move` enlaza directo con la tarea vía `raw_material_task_id`.

Scripts: [`project_stock/migrations/17.0.1.0.0/pre-migration.py`](project_stock/migrations/17.0.1.0.0/pre-migration.py) y [`post-migration.py`](project_stock/migrations/17.0.1.0.0/post-migration.py).

### `pre-migration.py`

- **Rename de campo**: `procurement_group_id` (en `project.task`, declarado
  por el módulo 14.0) → `group_id` (en `project.task`, declarado por
  `project_stock`). Mismo modelo, mismo tipo (Many2one a
  `procurement.group`), solo cambia el nombre — `rename_fields`, no
  `rename_columns`, porque es el mismo campo con el mismo propósito.

### `post-migration.py`

Corre en post porque `raw_material_task_id` no existe hasta que
`project_stock` aplica su esquema nuevo.

- **Backfill** (`_backfill_raw_material_task_id`): para las filas de
  `project_task_material` que YA tenían un `stock.move` real
  (`stock_move_id` no nulo), traslada el enlace tarea↔movimiento al propio
  `stock.move.raw_material_task_id`.
- **Creación de `stock.move` en borrador** (`_create_draft_moves_for_pending_materials`):
  decisión de negocio confirmada — las filas de `project_task_material` SIN
  `stock_move_id` (material apuntado en la tarea que en 14.0 nunca llegó a
  consumirse) no se dan por perdidas. Se les crea su `stock.move`
  equivalente en `draft`, replicando los mismos defaults que usaría la
  propia tarea al añadir una línea a mano (ubicaciones, tipo de operación,
  grupo de aprovisionamiento — creando uno si la tarea aún no tiene). Es
  **idempotente**: cada `stock.move` creado se enlaza de vuelta al
  `stock_move_id` de la fila vieja, así que una reejecución no duplica
  nada. Filas huérfanas (sin `task_id`, o sin `product_id`) se saltan con
  un aviso por log, sin crear nada para ellas ni reventar.
- La tabla `project_task_material` **no se borra en ningún momento** — se
  sigue consultando por SQL crudo después del corte por si hace falta
  revisar algo, y por eso este script usa SQL crudo contra ella en vez de
  `env['project.task.material']` (para no depender de que ese modelo siga
  registrado en el ORM — ver [§5](#5-neutralización-de-módulos-sustituidos)).

## 4. `product_task_material_work`

Scripts: [`product_task_material_work/migrations/17.0.1.0.1/pre-migration.py`](product_task_material_work/migrations/17.0.1.0.1/pre-migration.py) y [`post-migration.py`](product_task_material_work/migrations/17.0.1.0.1/post-migration.py).

### `pre-migration.py`

1. **Fusión de módulos absorbidos** (`update_module_names` con
   `merge_modules=True`): `merge_pt`, `product_price_with_waste`,
   `print_options_to_false_account_move_line`,
   `sale_order_invoicing_finished_fix_translation`,
   `sale_order_invoicing_finished_merge_task` → todos absorbidos por
   `product_task_material_work`. Va primero porque el resto del script
   asume que ya está resuelto. `product_task_material_work_category`
   **no** está en esta lista: en 14.0 era un módulo aparte que dependía
   de `product_task_material_work` (no al revés), y su funcionalidad de
   categoría no se reimplementa en 17.0 — se neutraliza aparte
   ([§5](#5-neutralización-de-módulos-sustituidos)) y queda pendiente de
   rehacer como módulo propio ([§8](#8-pendiente--limitaciones-conocidas)).
2. **Instalación forzada de módulos nuevos** en la misma pasada de `-u all`:
   `crm_lead_to_project_task`, `project_task_to_sale_order`,
   `project_task_by_administration`, `resume_material_and_work`,
   `comparisons_sale_order` — se marcan `to install` por SQL directo. Es
   necesario porque, en el instante en que `product_task_material_work`
   deja de declarar campos como `by_administration`, si el módulo que los
   declara ahora todavía no está instalado, esos campos se quedan sin
   ningún módulo que los reclame y Odoo borraría la columna al limpiar
   huérfanos (`odoo/modules/loading.py:load_marked_modules` relee
   `ir_module_module.state` en bucle hasta que no aparece nada nuevo, así
   que basta con dejar el estado en `to install` aquí, sin pasar `-i` por
   línea de comandos).
3. **Rename real de campo** (`rename_fields`, con todos sus efectos
   secundarios — `ir_model_fields.name`, traducciones, `ir_property`):
   `sign_by` → `signed_by` en `project.task`.
4. **Respaldo de columnas a punto de quedar huérfanas**
   (`_backup_legacy_columns` → `rename_columns` con `new=None` →
   `get_legacy_name()`), **cada una comprobada con `column_exists`** por si
   el módulo 14.0 que la declaraba no estaba instalado:
   - `project_task.merged_parent_id` → lo consume `_fix_merge_tasks` en el
     post-migration.
   - `product_template.apply_category` → **este script no lo consume**; se
     respalda por si el futuro módulo 17.0 de categoría lo necesita. Si la
     columna no existe (módulo `_category` no instalado en 14.0), el guard
     lo salta. Conservar o descartar este respaldo está pendiente de
     decidir ([§8](#8-pendiente--limitaciones-conocidas)).

### `post-migration.py`

- **`_invert_apply_pricelist`**: `apply_pricelist` existe con el mismo
  nombre en `product.template` en 14.0 y 17.0 (la columna se arrastra
  intacta), pero su valor significa **lo contrario**:

  | 14.0 | Comportamiento | 17.0 equivalente |
  |---|---|---|
  | `apply_pricelist = False` | precio del compuesto = suma directa de componentes (ya tarificados) | `apply_pricelist = True` |
  | `apply_pricelist = True` | regla de tarifa sobre el compuesto entero (base = suma de componentes) | `apply_pricelist = False` |

  Por eso el script **invierte** el valor, acotado a productos partida
  (`service_tracking IN ('task_global_project','task_in_project')`);
  `NULL` cuenta como `False`. No tiene nada que ver con `apply_category`
  de `product_task_material_work_category`. **Avisos**: (1) es un volteo
  masivo — el checkbox que estaba desmarcado queda marcado y viceversa;
  (2) en la dirección `14.0 True → 17.0 False` se conserva la regla sobre
  el compuesto, pero el desglose de componentes pasa de tarificado a
  precio de catálogo — solo se nota si la tarifa del cliente tiene reglas
  a nivel de los productos componentes.
- **`_fix_merge_tasks`**: 14.0 guardaba las fusiones de tareas como
  jerarquía padre/hijo (`merged_parent_id` + su inverso). 17.0 lo sustituye
  por una relación M2M plana (`merge_task_ids`, tabla `merge_tasks`). No es
  un rename, es un cambio de modelo de datos — se puebla la tabla nueva a
  mano a partir de la FK vieja respaldada en el pre-migration.
- **`_activate_percent_waste_if_used`**: `percent_waste` sobrevive tal
  cual (mismo campo, misma tabla) sin necesidad de nada aquí, pero en 17.0
  su uso queda condicionado a un `ir.config_parameter`
  (`product_task_material_work.active_group_percent_waste`) ligado a un
  grupo de seguridad opcional. Si el cliente ya lo usaba en 14.0
  (`product.template` con algún `percent_waste > 0`) y no se activa esto,
  el dato sigue en la BD pero queda invisible/inaplicado en la UI tras el
  corte. **TODO sin cerrar** (ver [§8](#8-pendiente--limitaciones-conocidas)):
  falta verificar contra una instancia 17.0 real el valor exacto que
  espera ese parámetro.

## 5. Neutralización de módulos sustituidos

Tres módulos de 14.0 no pueden neutralizarse desde un script de
pre/post-migración normal: Odoo construye el grafo de módulos a instalar a
partir de `ir_module_module` **antes** de ejecutar ninguna migración, así
que hace falta SQL directo desde fuera de Odoo, y en el momento justo.

- **`project_task_material_stock_liyben_mig_mod`**: su carpeta no existe en
  17.0. Si su fila sigue en `installed` cuando `addons/custom` ya está en
  la rama 17.0, el arranque de Odoo **revienta** antes de llegar a
  cualquier script. Sustituido por `project_stock`.
- **`project_task_material`** (OCA base): su código **sí** existe también
  en la rama 17.0 de `OCA/project` — no revienta nada, pero sin
  neutralizarlo Odoo lo trata como un módulo instalado más a
  migrar/actualizar con normalidad, quedando activo en 17.0 **en
  paralelo** a `project_stock`, duplicando la misma funcionalidad.
- **`product_task_material_work_category`**: propio del vertical, sin
  carpeta en 17.0. Mismo caso de crash que el primero. Neutralización
  **interina**: la funcionalidad de tarifa por categoría no existe en 17.0
  hasta que se reimplemente como módulo propio
  ([§8](#8-pendiente--limitaciones-conocidas)). Su `apply_category` queda
  respaldado por el pre-migration de `product_task_material_work` (si la
  columna existía).

Ninguno se desinstala de verdad (eso arrastraría un `unlink` en cascada —
`project_task_material`, en concreto, tiene una tabla que `project_stock`
necesita conservar intacta). Se fuerza su fila a `uninstalled` por SQL
directo, sin tocar tablas ni datos.

### [`scripts/openupgrade/neutralize_replaced_modules.sh`](scripts/openupgrade/neutralize_replaced_modules.sh)

```bash
./scripts/openupgrade/neutralize_replaced_modules.sh <contenedor_postgres> <nombre_bd> [usuario_bd=odoo]
```

Fuerza por SQL directo (`docker exec ... psql`) el `state` de los tres
módulos de arriba a `uninstalled` en `ir_module_module` (un `UPDATE ...
WHERE name IN (...)`, así que si alguno no estaba instalado simplemente no
afecta a nada). Muestra el estado antes y después.

### [`scripts/openupgrade/run_final_hop.sh`](scripts/openupgrade/run_final_hop.sh)

```bash
./scripts/openupgrade/run_final_hop.sh <directorio_del_salto_v17.0> [ruta_del_checkout_del_vertical=addons/custom/vertical-instaladores]
```

`deploy_openupgrade_step.sh` (repo `Scripts-Odoo`) genera el salto final
v17.0 con `addons/custom` arrastrado sin cambios desde la producción de
origen (rama 14.0) — no lo re-clona ni le cambia de rama en ningún salto de
su cadena (documentado en su propio `OPENUPGRADE.md` como responsabilidad
de este repo, no del suyo). Este script cierra ese hueco para el salto
**ya generado**, reutilizando lo que `deploy_openupgrade_step.sh` ya
construyó (imagen Docker, contenedor de BD) sin reconstruir nada:

1. `git checkout 17.0` sobre el checkout del vertical dentro de **ese
   salto concreto**.
2. Llama a `neutralize_replaced_modules.sh` contra su contenedor/BD
   (autodetectados desde `docker-compose.yml` y `config/odoo.conf` del
   propio salto).
3. Reejecuta el `-u all` de ese salto — ahora con `project_stock` presente
   en el `addons_path` y los módulos viejos neutralizados. Reejecutar
   `-u all` sobre una BD que ya pasó por él una vez es la operación normal
   y segura de OpenUpgrade: los módulos ya al día no hacen nada, y esta
   misma pasada es la que también recoge `product_task_material_work` si
   el salto original (paso 1 de este runbook) no llegó a completarlo bien
   por el mismo motivo (código del vertical ausente/desactualizado en ese
   punto de la cadena).

## 6. Runbook completo (14.0 → 17.0)

1. **Fases 1 y 2** (ensayo + verificación) de `OPENUPGRADE.md` en
   `Scripts-Odoo`, normales, sin ninguna intervención de este repo — el
   salto hasta v17.0 se genera con `addons/custom` todavía en rama 14.0 (es
   lo esperado, ver [§1](#1-alcance-y-por-qué-es-una-migración-directa)).
2. En el directorio del salto final v17.0 que generó `deploy_openupgrade_step.sh`:
   ```bash
   cd /home/soporte/GitHub/vertical-instaladores
   ./scripts/openupgrade/run_final_hop.sh /opt/odoo_upgrade/<safe_name>_v17.0
   ```
3. Si el stack de revisión de ese salto ya estaba levantado
   (`docker compose up -d`), reiniciarlo para que recoja vistas/menús
   nuevos:
   ```bash
   cd /opt/odoo_upgrade/<safe_name>_v17.0 && docker compose restart web
   ```
4. Revisar el log de `run_final_hop.sh` en busca de los avisos de
   `project_stock` (filas de `project_task_material` huérfanas o sin
   producto — ver [§3](#3-project_stock-nuevo-en-170)) y del TODO de
   `percent_waste` (ver [§4](#4-product_task_material_work)).
5. **Fase 3** de `OPENUPGRADE.md` (corte real a producción,
   `promote_openupgrade_to_prod.sh`) sobre el salto ya cerrado por el paso
   2 — sin cambios respecto al procedimiento genérico documentado ahí.

## 7. Tests

[`project_stock/tests/test_migration_17_0_1_0_0.py`](project_stock/tests/test_migration_17_0_1_0_0.py)
carga `post-migration.py` de `project_stock` por ruta de fichero (su
nombre con guion no es importable con un `import` normal) y ejercita sus
funciones contra una tabla `project_task_material` fabricada a mano por
SQL, simulando los datos que la migración real encuentra en 14.0: backfill
de filas con `stock_move_id`, creación de `stock.move` en borrador
(defaults, idempotencia, reutilización de `group_id` existente), y los dos
casos de fila corrupta (sin `task_id`, sin `product_id`).

Se salta entero (no falla) si `openupgradelib` no está instalado — solo
está presente en el entorno real de migración OpenUpgrade
(`openupgrade_framework` como `server_wide_module`,
`requirements-openupgrade.txt`), nunca en una instalación normal del
módulo. Para que corra de verdad:

```bash
docker compose run --rm web odoo -d <nombre_bd> -u project_stock \
    --test-enable --test-tags /project_stock --stop-after-init --log-level=test
```

[`product_task_material_work/tests/test_migration_17_0_1_0_1.py`](product_task_material_work/tests/test_migration_17_0_1_0_1.py)
sigue el mismo patrón. Para que `_force_install_new_dependent_modules` y
`_backup_legacy_columns` (en `pre-migration.py`) fueran ejercitables como
funciones sueltas, se extrajeron de dentro del `migrate()` (`rename_fields`
se queda inline, sin test — mismo motivo que el rename de `project_stock`:
opera sobre el esquema anterior a que el módulo aplique el suyo). Cubre:

- Saneamiento de datos de `_MERGED_MODULES`/`_NEW_DEPENDENT_MODULES`
  (nombres no repetidos, todos fusionándose hacia
  `product_task_material_work`, sin solape entre fusionados y forzados a
  instalar, y que `product_task_material_work_category` **no** está en el
  merge) — no ejercita `openupgrade.update_module_names` en sí, eso es
  responsabilidad de openupgradelib.
- El forzado real a `to install` de los 5 módulos nuevos, con datos reales
  de `ir_module_module`.
- `_backup_legacy_columns` no revienta cuando las columnas 14.0 a respaldar
  no existen (guard con `column_exists`).
- Las tres funciones de `post-migration.py`: `_invert_apply_pricelist`
  (inversión acotada a productos partida, `NULL` = `False`, no-partida sin
  tocar), `_fix_merge_tasks` (poblado del M2M desde
  `openupgrade_legacy_17_0_merged_parent_id`, columna fabricada a mano por
  SQL) y `_activate_percent_waste_if_used`.

Mismas condiciones de salto (`openupgradelib` no instalado) y de ejecución
real que `project_stock`, cambiando `-u project_stock` por
`-u product_task_material_work` y el `--test-tags`.

## 8. Pendiente / limitaciones conocidas

- **TODO sin cerrar en `product_task_material_work/migrations/17.0.1.0.1/post-migration.py`**
  (`_activate_percent_waste_if_used`): verificar contra una instancia 17.0
  real el valor exacto que espera
  `product_task_material_work.active_group_percent_waste` antes de dar
  este paso por definitivo. El test de esta función solo comprueba el
  contrato actual del código (deja el parámetro en la cadena `"True"`), no
  que ese sea el valor correcto.
- **Filas de `project_task_material` huérfanas** (sin `task_id` o sin
  `product_id`): `post-migration.py` de `project_stock` las lista por log
  sin crear nada para ellas — revisar manualmente tras cada corte real si
  aparece alguna.
- **Reimplementar `product_task_material_work_category` en 17.0**
  (pospuesto): en 14.0 era un módulo aparte (dependía de
  `product_task_material_work`, no al revés) que añadía la tarifa a nivel
  de la categoría del compuesto + coste vía `product_pricelist_supplierinfo`.
  17.0 no lo reimplementa y no lo fusiona; se neutraliza de forma interina
  ([§5](#5-neutralización-de-módulos-sustituidos)) → **la funcionalidad de
  categoría no existe en 17.0 hasta que se cree ese módulo propio**. El
  port no es un bump de versión: el `product_task_material_work` de 17.0
  se reescribió de onchange a compute, así que la lógica de
  sustitución-de-categoría / cantidad-del-compuesto / `supplierinfo` hay
  que rehacerla contra la estructura nueva. Al heredar de
  `product_task_material_work` 17.0 **no** tendrá que redeclarar
  `percent_waste`. Su migración deberá reconciliar `apply_category` con el
  `apply_pricelist` ya invertido (p.ej. `apply_pricelist = false` donde
  `apply_category = true`, o que `apply_category` tenga prioridad en el
  código).
- **Datos de `apply_category`**: el pre-migration de
  `product_task_material_work` los respalda (con guard `column_exists`)
  pero no los consume. Pendiente decidir si se conservan para el futuro
  módulo 17.0 o se descartan (el cliente vuelve a marcar los checkboxes
  cuando el módulo regrese).
- **Fusión de módulos y renames sin cobertura de test**: en ninguno de los
  dos módulos (`project_stock`, `product_task_material_work`) se ejercita
  de verdad `update_module_names`/`rename_fields`/`rename_columns` — solo
  la lógica propia de este repo alrededor de ellos. Esas tres funciones de
  openupgradelib se verifican en el ensayo real de la migración (Fases 1/2
  de `OPENUPGRADE.md`), no con tests unitarios.
- **Hook genérico en `deploy_openupgrade_step.sh`** (repo `Scripts-Odoo`):
  generalización de `run_final_hop.sh` a un punto de extensión reutilizable
  por cualquier vertical con el mismo patrón de rama única en origen y
  destino. Anotado en el `PENDING_OPENUPGRADE.md` de ese repo,
  deliberadamente no construido todavía — solo hay un caso real
  (`vertical-instaladores`) y generalizar con un único caso es generalizar
  a ciegas.
- **Resto de modelos propios del vertical sin script de migración
  dedicado**: `product.task.work`/`product.task.material` y afines (ya
  trackeados en `verify_openupgrade_step.sh` de `Scripts-Odoo`) dependen
  hoy solo del ORM estándar de OpenUpgrade, sin ningún
  `migrations/17.0.x.y.z/` propio en sus módulos. Pendiente igual que el
  resto, anotado en `PENDING_OPENUPGRADE.md`.
