# Pendiente: apuntes analíticos duplicados del material de las tareas

Estado: **sin decidir ni aplicar**. Hallazgo 4 de la auditoría de `project_stock` (17.0).

## Problema

En 17.0 hay dos sitios que crean apuntes analíticos (`account.analytic.line`) por el material
que consume una tarea:

1. **`project.task.action_done()`** (`project_stock`, código OCA): valida los albaranes de la tarea y
   después crea un apunte por cada movimiento
   ([project_task.py](../../project_stock/models/project_task.py), método `action_done`;
   [stock_move.py](../../project_stock/models/stock_move.py), método `_prepare_analytic_line_from_task`).
2. **Validación del albarán** (`stock_move_with_account_analytic_line`, propio): al cerrarse cada
   movimiento crea su apunte si se cumplen todas estas condiciones:
   - la categoría del producto tiene valoración «Coste / Beneficio» (`only_analytic`);
   - el albarán tiene distribución analítica;
   - el movimiento está enlazado a una tarea (`task_id`).

   Código: [stock_move.py](../../stock_move_with_account_analytic_line/models/stock_move.py), método `_action_done`.

Como `action_done()` valida el albarán, si se llama se ejecutan **las dos vías** y el coste del
material se imputa dos veces.

**Hoy la duplicación es latente.** Ningún código del repo llama a `action_done()` (solo los tests) y
su botón está dentro del bloque comentado de
[project_task_view.xml](../../project_stock/views/project_task_view.xml). Los usuarios validan los
albaranes desde el botón «Entregas» o desde Inventario, así que hoy solo funciona la vía 2. El
problema aparecería si alguien reactiva ese bloque de botones o llama a `action_done()` desde código
o RPC.

### Cómo reproducirlo

En una base de datos con `project_stock`, `stock_move_with_account_analytic_line` y
`product_task_material_work` instalados:

1. Crear una categoría de producto con valoración «Coste / Beneficio» y un producto almacenable de
   esa categoría, con coste.
2. Crear un pedido con ese material y una distribución analítica, y confirmarlo. La tarea generada
   lleva el material, y los movimientos y la tarea llevan la distribución.
3. Pasar la tarea a una etapa con «Movimientos de stock hechos». Los movimientos se confirman, se
   reservan y se crea el albarán.
4. Llamar a `task.action_done()`, desde un test o un shell de Odoo, porque no tiene botón en la
   interfaz.
5. Resultado: por cada movimiento hay un apunte en `stock_move.analytic_account_line_ids` (vía 2) y
   otro en `task.stock_analytic_line_ids` (vía 1). El coste aparece dos veces en la cuenta analítica.

## Opción A: que los genere `project.task.action_done()`

**Qué cambia para el usuario**
- Los apuntes solo aparecen al pulsar «Hecho» en la tarea. Hay que reactivar ese botón en la vista.
  Si se valida el albarán desde «Entregas», como hoy, no se genera nada.
- Se crean apuntes para **todos** los productos, sea cual sea la valoración de su categoría.
  - Con valoración automática (`real_time`), `stock_analytic` ya lleva la analítica a los asientos
    contables, así que también saldrían duplicados.
- Los apuntes se ven en la propia tarea (`stock_analytic_line_ids`) y se borran al cancelarla
  (`action_cancel`).

**Defectos de esta vía que habría que corregir**
- No reparte la distribución analítica. Con un reparto 50 % / 50 % entre dos cuentas crea un solo
  apunte, en la cuenta de la tarea o del proyecto y por el importe total: solo multiplica el importe
  por la suma de porcentajes.
- Si se llama dos veces, duplica los apuntes.
- Crea apuntes también para movimientos cancelados o con cantidad 0.
- La fecha es la analítica de la tarea o del proyecto, no la del movimiento.

**Archivos que tocaría**
- `project_stock/views/project_task_view.xml`: reactivar el botón «Hecho» y, posiblemente, el resto
  del bloque comentado.
- `project_stock/models/stock_move.py` (`_prepare_analytic_line_from_task`): repartir la
  distribución entre cuentas y crear apuntes solo de movimientos hechos.
- `project_stock/models/project_task.py` (`action_done`): evitar duplicados si se llama más de
  una vez.
- `stock_move_with_account_analytic_line/models/stock_move.py`: no crear apuntes en los movimientos
  con tarea, o dejar el módulo solo para movimientos sin tarea.
- Revisar cómo convive con la analítica de las categorías de valoración automática.

## Opción B: que los genere la validación del albarán (`stock_move_with_account_analytic_line`)

**Qué cambia para el usuario**
- **Nada respecto a hoy.** El apunte aparece al validar el albarán, desde «Entregas» o desde
  Inventario.
- Las validaciones parciales generan apuntes por lo realmente entregado.
- El reparto entre cuentas usa `_perform_analytic_distribution` del core, así que un reparto 50/50
  genera dos apuntes.
- Las devoluciones desde un cliente se registran en positivo.
- Solo genera apuntes para las categorías «Coste / Beneficio». Las de valoración automática reciben
  la analítica por los asientos contables (`stock_analytic`), sin duplicarse.
- La sección de apuntes de la propia tarea (`stock_analytic_line_ids`) queda vacía. Los costes se
  consultan en la cuenta analítica o en el albarán.

**Archivos que tocaría**
- `project_stock/models/project_task.py`:
  - `action_done()` solo validaría los albaranes y dejaría de crear apuntes, con un comentario que
    remita a `stock_move_with_account_analytic_line`. Así no duplica aunque se reactive el botón.
  - En `action_cancel()`, decidir qué pasa con los apuntes del albarán. Hoy borra
    `stock_analytic_line_ids`, que con esta opción estará vacío. Probablemente no hay que hacer
    nada, porque los movimientos hechos no se deshacen.
- `project_stock/tests/test_project_stock.py`: adaptar los tests OCA que esperan apuntes creados
  desde la tarea (`_test_task_analytic_lines_from_task` y los que la usan:
  `test_project_task_analytic_lines_*`, `test_project_task_process_cancel`,
  `test_project_task_process_02`). Deberían comprobar que la tarea ya no crea apuntes.
- `stock_move_with_account_analytic_line/tests/` (nuevo; el módulo no tiene tests). Debería cubrir:
  - categoría «Coste / Beneficio» con un reparto 50/50: dos apuntes;
  - devolución desde un cliente: importe positivo;
  - producto de otra categoría: ningún apunte.

## Cómo funcionaba en 14.0

Con la vía del albarán (opción B):
- En `project_task_material_stock_liyben_mig_mod`, la creación de apuntes desde la tarea estaba
  **desactivada a propósito**: la llamada `# todo_lines.create_analytic_line()` está comentada en el
  `write` de `project.task`.
- El `action_done` de la tarea solo cerraba los movimientos.
- Los apuntes los creaba `stock_move_with_account_analytic_line` 14.0 al validar el albarán, con la
  misma condición de categoría «Coste / Beneficio». En 14.0 además exigía cuenta analítica en el
  albarán y un tipo de operación marcado `stock_move_from_task`.
- La tarea solo corregía el importe de apuntes ya creados (`_update_unit_amount`).

Referencia: `/opt/odoo-src/14.0/vertical-instaladores/project_task_material_stock_liyben_mig_mod/models/project_task.py`
y `/opt/odoo-src/14.0/vertical-instaladores/stock_move_with_account_analytic_line/models/stock_move.py`.

## Recomendación: opción B

- Es como trabajan hoy los usuarios y como funcionaba en 14.0. No cambia nada para ellos ni para la
  continuidad de los datos migrados.
- Reparte bien la distribución analítica entre cuentas, respeta las validaciones parciales y las
  devoluciones, y no se duplica con la analítica que llega por contabilidad en las categorías de
  valoración automática.
- La opción A obliga a corregir varios defectos del código OCA y a cambiar la forma de trabajar.

**Antes de aplicarla**, comprobar en el VPS que todas las categorías de los materiales que se
consumen en tareas tienen la valoración «Coste / Beneficio». Con la opción B, los productos de otra
categoría con valoración manual no generan ningún apunte.
