# Pendiente para la migración 14.0 → 17.0: correcciones de `project_stock` y `product_task_material_work`

Estas correcciones se hicieron en la rama `17.0` mientras la migración estaba aparcada. Cuando se
retome la rama `17.0-migracion` hay que hacer dos cosas:

1. Añadir la llamada pendiente en el script de migración (sección siguiente).
2. Incorporar a `MIGRATION_14_TO_17.md` la nota de la sección «Texto para MIGRATION_14_TO_17.md».
   Cuando esté incorporada, borrar este archivo.

## Cambio pendiente en `product_task_material_work/migrations/17.0.1.0.1/post-migration.py`

En `migrate(env, version)`, añadir:

```python
    # Pedidos de 14.0: picking_type_id/location_id/location_dest_id se calcularon
    # al crear las columnas, antes de cargar stock_picking_type_task_material.
    env["sale.order"]._recompute_empty_stock_options()
```

Por qué hace falta:

- Esos tres campos de `sale.order` son nuevos en 17.0. Odoo los calcula al crear las columnas,
  antes de cargar el XML que define el tipo de operación, así que los pedidos de 14.0 quedan vacíos.
- En una instalación nueva los rellena el `post_init_hook`, pero ese hook no se ejecuta al actualizar.
- Sin esta llamada, confirmar un presupuesto migrado falla: crea `stock.move` sin ubicaciones,
  que son campos obligatorios.

El método `_recompute_empty_stock_options()` ya está en `product_task_material_work/models/sale_order.py`
(rama `17.0`). Hay que traerlo a `17.0-migracion` junto con el resto de cambios.

Comprobación tras migrar; debe dar 0:

```sql
SELECT count(*) FROM sale_order
WHERE picking_type_id IS NULL AND location_id IS NULL AND location_dest_id IS NULL;
```

Conviene cubrir la llamada en el test de migración del módulo
(`product_task_material_work/tests/test_migration_17_0_1_0_1.py`): crear un pedido con los tres campos
vacíos, ejecutar la función y comprobar que quedan rellenos.

## Texto para MIGRATION_14_TO_17.md

### `project_stock`: dependencia de `stock_analytic` y correcciones de 17.0

- `project_stock` declara ahora `stock_analytic` en `depends`. Su código escribe
  `stock.move.analytic_distribution`, un campo que añade `stock_analytic` (OCA
  `account-analytic`). En 14.0, `project_task_material_stock_liyben_mig_mod` ya
  dependía de `stock_analytic` y `stock_picking_analytic`, pero la dependencia
  se perdió al pasar a 17.0. En los clientes ya estaba instalado de forma
  indirecta (`product_task_material_work` → `stock_picking_analytic` →
  `stock_analytic`), así que la migración no instala ningún módulo nuevo.
- `stock_move_with_account_analytic_line` declara ahora `project_stock` en
  `depends`, porque usa `stock.move.task_id`.
- Pasar una tarea a una etapa con `done_stock_moves` ya no da error si tiene
  movimientos reservados («It is not possible to change this with reserved
  movements in tasks.»). Tampoco da AccessError a un usuario de proyecto sin
  grupo de stock, porque las operaciones de stock se hacen con `sudo()`.
- Pasar varias tareas a la vez a una etapa con `done_stock_moves` ya no falla
  con «Expected singleton»: cada tarea recibe su propio grupo de
  aprovisionamiento («Task-ID: <id>»). El grupo solo se cambia en movimientos
  que aún no están en un albarán.

### `product_task_material_work`: tipo de operación y ubicaciones de `sale.order`

- `sale.order.picking_type_id`, `location_id` y `location_dest_id` son nuevos en
  17.0: son campos calculados y almacenados (`precompute`) que toman su valor
  por defecto del tipo de operación
  `product_task_material_work.stock_picking_type_task_material`. Al crear las
  columnas, Odoo los calcula para los pedidos existentes antes de cargar el XML
  que define ese tipo, lo que rompía tanto la instalación nueva como el `-u` de
  la migración («External ID not found»).
- Corrección: el cálculo ya no falla si el tipo aún no existe (deja los campos
  vacíos), y `sale.order._recompute_empty_stock_options()` rellena después los
  pedidos que tienen los tres campos vacíos.
  - Instalación nueva: lo llama el `post_init_hook` del módulo.
  - Migración 14 → 17: el hook no se ejecuta al actualizar, así que lo llama
    `product_task_material_work/migrations/17.0.1.0.1/post-migration.py`.
- Es necesario: si un pedido queda sin ubicaciones, al confirmarlo se crean
  `stock.move` sin `location_id`/`location_dest_id`, que son obligatorios.
- Comprobación tras migrar: ningún pedido debe quedar con los tres campos
  vacíos (`SELECT count(*) FROM sale_order WHERE picking_type_id IS NULL AND
  location_id IS NULL AND location_dest_id IS NULL;` → 0).
- Con varias compañías, todos los pedidos reciben el tipo de operación del
  almacén principal. Si hace falta otro por compañía, definirlo con `ir.default`.

### Pendiente

- Decidir una única vía para los apuntes analíticos de material:
  `project.task.action_done()` o la validación del albarán
  (`stock_move_with_account_analytic_line`). Con las dos activas se duplican.
