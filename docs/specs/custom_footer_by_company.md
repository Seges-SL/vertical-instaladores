# Spec: custom_footer_by_company (Odoo 17.0)

> Ampliación de un módulo EXISTENTE. No se renombra el módulo.
> Repo COMPARTIDO `vertical-instaladores` (rama `17.0-informes-cabecera-pie-imagen`):
> cualquier cambio afecta a todos los clientes de la 17 que lo tengan instalado.
> Autor: Seges. Licencia del código nuevo: AGPL-3.

---

## Decisiones CONFIRMADAS por el usuario (2026-11-05) — resuelven la §10

Estas decisiones cierran las preguntas abiertas de la §10 y PREVALECEN sobre las
recomendaciones de esa sección cuando difieran:

1. **Pie / numeración (pregunta 1): CONFIGURABLE con checkbox.** Añadir un
   booleano `custom_report_footer_keep_page_numbers` (string EN, p. ej.
   "Keep page numbers", default `True`) en `res.company` (+ related en el
   asistente). Cuando el pie personalizado sustituye al estándar
   (`custom_report_footer_replace=True`), si el checkbox está activo se reinserta
   la banda de numeración `Page x/y` (solo PDF) bajo el `custom_report_footer`.
   Los datos legales los pone el usuario en su HTML. NO forzar modo replace en la
   migración: default `custom_report_footer_replace=False` ⇒ sin script de
   migración (ver §8).
2. **Layout interno (pregunta 2): SOLO LAYOUTS EXTERNOS.** No se toca
   `web.internal_layout`.
3. **Dónde/permisos (pregunta 3): AMBOS SITIOS**, formulario de compañía +
   asistente de diseño, permisos del core (grupo Ajustes). Sin grupo nuevo.
4. **Altura imagen (pregunta 4): LIMITAR POR CSS en la plantilla.** La imagen va
   a ancho 100% y con `max-height` para que NUNCA se solape con el cuerpo:
   cabecera ≤ `margin_top − header_spacing`, pie ≤ `margin_bottom` (del
   paperformat de la compañía; para `paperformat_euro`: top 40 / spacing 35 ⇒
   ~5 mm útiles de cabecera, bottom 20 mm de pie — **a verificar y afinar en las
   referencias**). NO se toca el paperformat. Documentar en `readme/CONFIGURE`
   el tamaño recomendado en píxeles para A4. Aviso (`onchange`) al subir la
   imagen SOLO si resulta sencillo. **REQUISITO: verificar en
   `/opt/odoo-src/17.0` que wkhtmltopdf respeta ese `max-height` en el
   header/footer; si no lo respetara, documentar el límite real encontrado y
   ajustar la solución.**
5. **Interruptor del encabezado (pregunta 5): CHECKBOX BOOLEANO EXPLÍCITO**
   (`report_header_image_replace`), independiente de la presencia de la imagen.
   El pie mantiene su `custom_report_footer_replace` por compatibilidad.
6. **Pie por imagen (pregunta 5): NO.** Solo pie HTML (el actual). Nada de campo
   de imagen de pie.
7. **readme/ e i18n/ (preguntas 6-7): CREAR AMBOS.**
   - `readme/` con DESCRIPTION/USAGE/CONFIGURE en español + regenerar con
     `odoo-readme custom_footer_by_company`. **ANTES de ejecutar `odoo-readme`,
     comprobar `static/description/` y preguntar al orquestador/usuario si hay
     `index.html` o `icon.png` propios: NO sustituirlos sin permiso.** (Se sabe
     que existe `static/description/icon.png`: conservarlo.)
   - `i18n/es.po`: SOLO con los textos NUEVOS de esta tarea. Los textos
     existentes (p. ej. el `string` español de `custom_report_footer`) NO se
     traducen ni se renombran. Los `string`/`help` NUEVOS van en inglés en el
     código y su traducción al español en `es.po`.
8. **Errata `report_tamplate.xml` (pregunta 8): NO RENOMBRAR.**

---

## 0. Estado ACTUAL del módulo (análisis previo, citado archivo:línea)

Árbol actual (local, no la copia publicada de `/opt/odoo-src`):

```
custom_footer_by_company/
├── __init__.py                     (importa models y wizards)
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── res_company.py
├── template/
│   └── report_tamplate.xml         (NOTA: el nombre tiene una errata "tamplate")
├── views/
│   └── res_company_views.xml
├── wizards/
│   ├── __init__.py
│   ├── base_document_layout.py
│   └── base_document_layout.xml
└── static/description/icon.png
```
No existen carpetas `readme/`, `i18n/`, `security/`, `data/` ni `tests/`.

### Qué hace HOY
- **Manifest** (`__manifest__.py:1-19`): `name` "Pie de página personalizado",
  `version` `17.0.1.0.0`, `depends = ['base', 'web']`, carga en `data`:
  `template/report_tamplate.xml`, `views/res_company_views.xml`,
  `wizards/base_document_layout.xml`. Licencia `AGPL-3`, autor `Seges`.
- **Campo nuevo** (`models/res_company.py:14`): añade a `res.company` el campo
  `custom_report_footer = fields.Html('Pie del report', translate=True,
  sanitize=True)`. Es el único campo del módulo. No tiene `help`, ni texto en
  inglés (la etiqueta está en español), ni `company_dependent` (es un campo
  normal de `res.company`, lo que ya es correcto para multicompañía porque el
  informe resuelve la compañía del documento, ver §6).
- **Configuración en el formulario de compañía**
  (`views/res_company_views.xml:5-16`): hereda `base.view_company_form` y añade,
  tras la página `branches`, una pestaña "Pie de página personalizado" con el
  campo `custom_report_footer` como `widget="html"`.
- **Configuración en el asistente de diseño de documento**
  (`wizards/base_document_layout.py:11-20` y `wizards/base_document_layout.xml`):
  hereda `base.document.layout`, añade el campo `related='company_id.custom_report_footer'`
  (`readonly=False`) y lo pinta en `web.view_base_document_layout` tras
  `report_footer`. Sobrescribe `_compute_preview` SOLO para añadir
  `custom_report_footer` a `@api.depends` (llama a `super()`), de modo que la
  vista previa del asistente se refresca al editar el pie.
- **Sustitución en los informes** (`template/report_tamplate.xml:1-39`): hereda
  las CUATRO plantillas de pie externo del core y, en cada una, **inserta** el
  pie personalizado **DESPUÉS** del `report_footer` estándar:
  - `web.external_layout_standard` → `<div t-field="company.report_footer"> position="after"`.
  - `web.external_layout_bold` → `<span t-field="company.report_footer"> position="after"`.
  - `web.external_layout_boxed` → `<div t-field="company.report_footer"> position="after"`.
  - `web.external_layout_striped` → `<div t-field="company.report_footer"> position="after"`.

### Qué parte del pie sustituye HOY y qué queda del estándar
- **Hoy NO sustituye nada: AÑADE.** El `custom_report_footer` se pinta como un
  bloque extra justo después del `report_footer` de la compañía, dentro del
  mismo `<div class="footer ...">`. Siguen apareciendo: el `report_footer`
  estándar, los datos de compañía (en `bold`), la numeración de páginas
  (`<span class="page"/> / <span class="topage"/>`) y el `display_name` del
  documento. Es decir, el nombre del módulo ("Pie personalizado") describe mal
  lo que hace: es un pie ADICIONAL, no un reemplazo.
- Afecta a los cuatro diseños externos estándar de la 17; no toca el encabezado,
  ni el layout interno, ni la vista previa en PDF descargable (sí la vista
  previa en pantalla del asistente, por el `_compute_preview`/depends).

### Verificado en el core 17 (`/opt/odoo-src/17.0`, solo lectura)
- Plantillas de los diseños externos y su contenido:
  `odoo/addons/web/views/report_templates.xml`:
  - `web.external_layout` (líneas 559-578): API pública que se llama desde los
    informes. Resuelve la compañía (líneas 562-573): usa `company_id` del
    contexto, si no `o.company_id.sudo()` (la compañía del DOCUMENTO), si no
    `res_company`. Luego: `t-if company.external_report_layout_id` →
    `t-call` a la plantilla indicada por `external_report_layout_id.key`; en su
    defecto `web.external_layout_standard` (líneas 575-576). **Confirma el
    requisito multicompañía: el informe usa la compañía del documento, no la del
    usuario.**
  - `web.external_layout_standard` (491-555): header = fila con logo
    (`max-height:45px`) y `report_header` (tagline), línea separadora, y
    `company_address`/`company_details`/VAT. Footer `o_standard_footer` (541-554)
    = `report_footer` + "Page: page/topage" (si pdf) + `display_name` (si
    `display_name_in_footer`).
  - `web.external_layout_bold` (429-489): header = logo + `company_address`.
    Footer `o_clean_footer` (470-488) = 4 columnas: `report_footer`,
    datos de compañía, `report_header`, y número de página (`page`).
  - `web.external_layout_boxed` (367-427): header `o_boxed_header` = logo +
    `report_header` + `company_address`. Footer `o_boxed_footer` (416-426) =
    `report_footer` + "Page: page / topage" + `display_name`.
  - `web.external_layout_striped` (308-365): header `o_background_header` =
    `report_header` (float-end) + logo + `company_address`. Footer
    `o_background_footer` (349-364) = `report_footer` + "Page: page of topage" +
    `display_name`.
  - Los cuatro tienen un ÚNICO `<div>` de nivel superior con clase `header`
    (los cuatro con `t-att-style="report_header_style"`) y un ÚNICO `<div>` de
    nivel superior con clase `footer` (`o_standard_footer` / `o_clean_footer` /
    `o_boxed_footer` / `o_background_footer`). Entre header y footer está el
    `<div class="article ...">` con `t-out="0"` (el cuerpo).
- **Cómo wkhtmltopdf separa header/footer**:
  `odoo/odoo/addons/base/models/ir_actions_report.py:337-429` (`_prepare_html`).
  wkhtmltopdf recoge TODOS los nodos con clase `header` (líneas 374-378) y los
  mueve a `#minimal_layout_report_headers`, y los `footer` (380-384) a
  `#minimal_layout_report_footers`; el resto es el cuerpo. El header se dibuja en
  el margen superior reservado y el footer en el inferior (`--header-html` /
  `--footer-html`, líneas 477-488). **Consecuencia de diseño (clave para esta
  spec):** basta con aportar un nodo `<div class="header">`/`<div class="footer">`
  alternativo con la imagen y ocultar el estándar con un `t-if`; no hace falta
  reescribir el contenido interno de cada layout.
- **Resolución del diseño de la compañía**:
  `res.company.external_report_layout_id` (`ir.ui.view`) en
  `odoo/odoo/addons/base/models/res_company.py:69`. `web.external_layout` usa su
  `.key` para hacer el `t-call` (report_templates.xml:575).
- **Campos del pie/encabezado en `res.company`**
  (`res_company.py:41-43,68-75`): `report_header` (Html, "Company Tagline",
  translate), `report_footer` (Html, translate), `company_details` (Html,
  translate), `paperformat_id` (M2o report.paperformat, default `paperformat_euro`),
  `external_report_layout_id` (M2o ir.ui.view), `layout_background`
  (Selection Blank/Geometric/Custom), `layout_background_image` (Binary).
- **Asistente de diseño** `base.document.layout`
  (`odoo/addons/web/models/base_document_layout.py`): campos `related` a la
  compañía; `preview` (Html, `sanitize=False`) computado en `_compute_preview`
  (líneas 123-144) renderizando `web.report_invoice_wizard_preview` con
  `company = wizard` (el propio wizard hace de "company"). Vista:
  `odoo/addons/web/views/base_document_layout_views.xml` (`web.view_base_document_layout`),
  campos `report_header`, `company_details`, `report_footer`, `paperformat_id`…
  La vista previa del asistente **t-call `web.external_layout`**
  (`report_templates.xml:110-112`), así que SÍ refleja las plantillas heredadas
  — con los matices del CSS de preview (ver §6 y §10).
- **Márgenes / formato de papel**:
  `odoo/odoo/addons/base/models/report_paperformat.py`: `margin_top` (default 40
  mm, línea 173), `margin_bottom` (20 mm, 174), `header_spacing` (35, 184),
  `dpi` (90, 186). El header se dibuja en los `margin_top` mm reservados; el
  footer en los `margin_bottom` mm. Si la imagen es más alta que ese margen,
  wkhtmltopdf la recorta o la solapa con el cuerpo (ver §10 / pregunta 4).
- **Otros módulos que heredan estos bloques**: en la lista OCA/third_party de
  referencia de la 17 (`/opt/odoo-src/17.0/oca`), `report_layout_config`
  (reporting-engine) añade otro diseño y hereda el asistente, pero NO toca
  header/footer por imagen (ver §2). No se detecta en core/OCA ningún módulo que
  sustituya header/footer por imagen por compañía.
- **Migración 14→17**: el módulo NO existe en
  `/opt/odoo-src/14.0/vertical-instaladores` (verificado: no hay carpeta) y NO
  existe `MIGRATION_14_TO_17.md` en la raíz del repo. Es un módulo nativo de la
  17. **Esta ampliación no afecta a la migración 14→17 en curso.**

---

## 1. Objetivo y reglas de negocio
1. Añadir, POR COMPAÑÍA, la opción de sustituir TODO el ENCABEZADO de los
   informes externos por una imagen.
2. Revisar el pie personalizado actual para que sustituya TODO el pie (no solo
   añada un bloque tras el `report_footer`).
3. Ambas sustituciones deben funcionar con los CUATRO diseños de documento
   externos de la 17 (standard, bold, boxed, striped), sea cual sea el elegido
   por la compañía en Ajustes → Diseño de documento.

Reglas:
- **Opción DESACTIVADA ⇒ informe idéntico al estándar de Odoo** para ese
  diseño. La sustitución solo actúa cuando la opción está activa.
- **Compatibilidad hacia atrás**: las compañías que ya usan
  `custom_report_footer` deben seguir funcionando tras actualizar. El campo NO
  se renombra ni se elimina. El cambio de comportamiento del pie (de "añadir" a
  "sustituir") se controla con un interruptor explícito, de modo que el valor
  visual actual pueda preservarse en la actualización (ver §5, §8 y pregunta 1).
- **Multicompañía**: cada informe usa la configuración de la compañía del
  documento (`o.company_id`), garantizado por `web.external_layout` (verificado,
  §0). Los campos nuevos viven en `res.company`.
- **Sin dependencias implícitas**: `depends` sigue siendo `['base', 'web']`
  (único origen de los campos y plantillas que se tocan). No se usa nada de
  otros módulos.
- Textos nuevos del código en inglés (con su `i18n/es.po` si se decide crear la
  carpeta, ver §7 y pregunta de i18n).
- Tocar solo lo que cambia esta tarea.

---

## 2. Soluciones existentes evaluadas (OCA / core / repo común) y conclusión
Revisado `/opt/odoo-src/17.0/oca/reporting-engine` (lista completa) y el core:
- `report_layout_config` (reporting-engine): añade un diseño global extra y
  opciones al asistente; **no** sustituye header/footer por imagen por compañía.
- `report_qweb_pdf_watermark`: marca de agua sobre el PDF; no es un encabezado.
- `report_substitute`, `report_qweb_element_page_visibility`,
  `report_qweb_parameter`: manipulan informes concretos, no el layout externo.
- Core: `base.document.layout` permite logo, tagline, colores y fondo, pero NO
  reemplazar el encabezado/pie completo por una imagen.

**Conclusión**: no hay módulo OCA/core/repo-común que cubra el requisito. Se
amplía el módulo propio existente `custom_footer_by_company`, que ya está
instalado en clientes y ya hereda los cuatro layouts.

---

## 3. Manifest
- `version`: `17.0.1.0.0` → **`17.0.2.0.0`** (feature nueva + script de
  migración de datos, ver §8).
- `depends`: se mantiene `['base', 'web']` (suficiente y exacto).
- `data`: se mantiene el orden actual; añadir, si se decide (preguntas abiertas),
  `security/ir.model.access.csv` NO procede (no hay modelos nuevos). Orden final
  propuesto de `data`:
  1. `template/report_tamplate.xml` (plantillas QWeb heredadas)
  2. `views/res_company_views.xml`
  3. `wizards/base_document_layout.xml`
- `license`: `AGPL-3`. `author`: `Seges`. `category`: `Reporting`.
- Recomendación menor (NO obligatoria, es cambio de forma): corregir la errata
  del archivo `report_tamplate.xml` → `report_templates.xml` queda como
  **pregunta abierta** porque implica tocar el `data` del manifest y cualquier
  `ref` externa; por defecto NO se renombra.

---

## 4. Modelos y campos

| modelo | herencia | campo | tipo | parámetros | propósito |
|---|---|---|---|---|---|
| res.company | `_inherit` | `custom_report_footer` | Html | **existente, NO se toca su definición** (translate=True, sanitize=True) | Pie personalizado (contenido HTML). |
| res.company | `_inherit` | `custom_report_footer_replace` | Boolean | `string="Replace standard footer"`, `default=False`, `help` en inglés | Interruptor: si está activo, el pie personalizado SUSTITUYE todo el pie estándar; si no, se mantiene el comportamiento legacy (añadir tras `report_footer`). Default False preserva el comportamiento actual en instalaciones existentes. (Ver pregunta 1.) |
| res.company | `_inherit` | `report_header_image` | Binary | `attachment=True`, `string="Report Header Image"`, `help` en inglés | Imagen que sustituye TODO el encabezado externo cuando está definida y el interruptor está activo. |
| res.company | `_inherit` | `report_header_image_replace` | Boolean | `default=False`, `string="Replace standard header with image"`, `help` en inglés | Interruptor del encabezado por imagen. La sustitución solo actúa si está activo Y hay `report_header_image`. Permite conservar la imagen pero desactivar la sustitución. (Ver pregunta 5: si se prefiere usar solo la presencia de la imagen como interruptor.) |
| base.document.layout | `_inherit` (TransientModel) | `custom_report_footer` | Html | **existente**, `related='company_id.custom_report_footer'`, `readonly=False` | Edición desde el asistente (ya existe). |
| base.document.layout | `_inherit` | `custom_report_footer_replace` | Boolean | `related='company_id.custom_report_footer_replace'`, `readonly=False` | Edición desde el asistente. |
| base.document.layout | `_inherit` | `report_header_image` | Binary | `related='company_id.report_header_image'`, `readonly=False` | Edición y previsualización desde el asistente. |
| base.document.layout | `_inherit` | `report_header_image_replace` | Boolean | `related='company_id.report_header_image_replace'`, `readonly=False` | Edición desde el asistente. |

Notas:
- Todos los campos nuevos van en `res.company` (NO `company_dependent`): el
  informe ya resuelve la compañía del documento, igual que los campos core
  `report_footer`/`report_header`.
- `report_header_image` como `Binary(attachment=True)`: el QWeb la pinta con
  `image_data_uri(company.report_header_image)` (patrón del logo en los layouts,
  `report_templates.xml:314,372,434,495`).

---

## 5. Métodos
- `base.document.layout._compute_preview` (sobrescritura **existente**,
  `wizards/base_document_layout.py:16-20`): ampliar el `@api.depends` para
  incluir los campos nuevos que deben refrescar la vista previa:
  `custom_report_footer` (ya está), `custom_report_footer_replace`,
  `report_header_image`, `report_header_image_replace`. Sigue siendo un `super()`
  sin lógica propia (solo añade dependencias). Firma: `def _compute_preview(self)`
  con `@api.depends(...)`.
- No se necesitan `_compute_*` de negocio, ni constraints, ni CRUD override. La
  lógica de sustitución es puramente declarativa en QWeb (`t-if`), que es lo que
  garantiza "desactivado = idéntico al estándar".
- (Opcional, pregunta 4) Si se decide avisar sobre el tamaño de imagen frente al
  `margin_top`/`margin_bottom`, un `@api.onchange('report_header_image')` en el
  wizard que muestre un `warning`. Recomendado solo como aviso, sin bloquear.

---

## 6. Vistas / Plantillas QWeb

### 6.1 Plantillas de informe (`template/report_tamplate.xml`)
Herencias verificadas (XML ID del core existentes, §0):
`web.external_layout_standard`, `web.external_layout_bold`,
`web.external_layout_boxed`, `web.external_layout_striped`.

Patrón de diseño (apoyado en cómo wkhtmltopdf separa `.header`/`.footer`, §0):
**no se reescribe el contenido interno de cada layout**; se añade un nodo
alternativo y se condiciona el estándar.

**Encabezado por imagen** (en cada uno de los 4 layouts):
- `xpath` al `<div>` de nivel superior con clase `header`
  (los 4 llevan `t-att-style="report_header_style"`; p. ej.
  `//div[@t-att-style='report_header_style']`), `position="attributes"`: añadir
  `t-if="not (company.report_header_image_replace and company.report_header_image)"`
  para que el encabezado estándar SOLO se renderice cuando la sustitución no
  aplica.
- Añadir, con `position="before"` respecto a ese mismo `<div>`, un nodo
  alternativo:
  ```
  <div t-attf-class="header o_company_#{company.id}_layout"
       t-if="company.report_header_image_replace and company.report_header_image">
      <img t-att-src="image_data_uri(company.report_header_image)"
           class="w-100" alt="Header"/>
  </div>
  ```
  (clase `header` obligatoria para que wkhtmltopdf lo extraiga al margen
  superior; `o_company_#{id}_layout` para heredar la fuente/estilos de compañía).

**Pie (sustituir TODO el pie)** (en cada uno de los 4 layouts):
- `xpath` al `<div>` de nivel superior con clase `footer`
  (`o_standard_footer` / `o_clean_footer` / `o_boxed_footer` /
  `o_background_footer`; p. ej.
  `//div[contains(@t-attf-class,'o_standard_footer')]`), `position="attributes"`:
  añadir `t-if="not (company.custom_report_footer_replace and
  not is_html_empty(company.custom_report_footer))"`.
- Añadir, `position="before"` respecto a ese `<div>`, un nodo alternativo:
  ```
  <div t-attf-class="footer o_company_#{company.id}_layout"
       t-if="company.custom_report_footer_replace and not is_html_empty(company.custom_report_footer)">
      <div t-field="company.custom_report_footer"/>
      <!-- numeración de páginas / datos legales: ver pregunta 1 -->
  </div>
  ```
- **Comportamiento legacy (interruptor desactivado)**: se mantiene el bloque
  actual `<div t-field="company.report_footer" position="after"> <div
  t-field="company.custom_report_footer"/> </div>` **pero** guardándolo con
  `t-if="not company.custom_report_footer_replace"` en el div insertado, para que
  el "añadir" solo ocurra en modo legacy. Así:
  - `custom_report_footer_replace = False` (default, instalaciones existentes):
    comportamiento idéntico al actual (pie estándar + bloque añadido).
  - `custom_report_footer_replace = True`: el pie estándar desaparece y solo se
    ve el pie personalizado.
- `is_html_empty` ya se usa en el core de layouts/preview; confirmar que está en
  el contexto de render de informes (en `_compute_preview` se pasa
  explícitamente, `base_document_layout.py:141`; en el informe real verificar y,
  si no, condicionar solo por el booleano). **Riesgo a validar en pruebas**
  (ver §10).

Observación sobre `external_layout_bold`: la herencia ACTUAL del pie usa un
`<span t-field="company.report_footer" position="after">` (el pie "bold" tiene el
`report_footer` dentro de un `<span>` en una columna). El `xpath` al `<div>`
footer de nivel superior (`o_clean_footer`) sí es válido también en bold y es el
punto correcto para el reemplazo total. Mantener la rama legacy de bold tal cual.

### 6.2 Formulario de compañía (`views/res_company_views.xml`)
- Hereda `base.view_company_form` (existente). En la pestaña existente
  "Pie de página personalizado" (`name="custom_footer"`), añadir:
  - `custom_report_footer_replace` (checkbox).
  - El `custom_report_footer` ya está.
- Añadir una pestaña/bloque para el encabezado por imagen (misma pestaña u otra,
  ver pregunta 3): `report_header_image_replace` (checkbox) y
  `report_header_image` (`widget="image"`), este último visible/recomendado
  cuando el checkbox esté activo (`invisible="not report_header_image_replace"`
  — recordar incluir el campo booleano en la vista para que la expresión valide,
  regla de la 17).

### 6.3 Asistente de diseño de documento (`wizards/base_document_layout.xml`)
- Hereda `web.view_base_document_layout` (existente). Tras el campo
  `custom_report_footer` (ya añadido), insertar `custom_report_footer_replace`,
  `report_header_image_replace` y `report_header_image` (`widget="image"`).
- La vista previa del asistente usa `web.report_invoice_wizard_preview` →
  `web.external_layout`, por lo que mostrará las sustituciones. **Matices
  (documentar, §10):** el CSS de preview (`report_preview_layout`,
  `report_templates.xml:52-85`) posiciona los footers en absoluto y la preview
  es HTML, no PDF: la numeración de páginas no aparece en la preview y la altura
  de la imagen puede verse distinta del PDF. La preview es orientativa.

---

## 7. Seguridad
- **No hay modelos nuevos** → no se añade `ir.model.access.csv` ni record rules
  nuevas. Los campos se agregan a `res.company` (editable solo por el grupo de
  Ajustes, `base.group_system`/`base.group_erp_manager`, control del core) y a
  `base.document.layout` (el asistente de diseño de documento, accesible a
  Ajustes).
- Multicompañía: `res.company` ya tiene su record rule multicompañía del core;
  los campos nuevos quedan cubiertos. El informe usa `o.company_id` (verificado,
  §0), no la compañía del usuario.
- Quién puede modificarlo: lo gestiona el core (acceso a `res.company` / al
  asistente). Si se quisiera restringir más finamente, es pregunta abierta
  (pregunta 3).

---

## 8. Datos y migración
- No hay secuencias, crons ni datos por defecto.
- **Script de migración** `migrations/17.0.2.0.0/post-migration.py` (módulo,
  seguir skill `odoo-comun`/estructura OCA; NO es migración 14→17 de
  OpenUpgrade, es migración de versión del propio módulo):
  - Objetivo: preservar el aspecto actual de las compañías que YA usan
    `custom_report_footer`. Decisión por defecto recomendada (ver pregunta 1):
    dejar `custom_report_footer_replace = False` en todas (es el default del
    campo, así que **podría no hacer falta script**). Solo se necesita script si
    se decide que, al actualizar, las compañías con pie personalizado pasen
    automáticamente a modo "replace" (cambio visible) — en ese caso el script
    pondría `custom_report_footer_replace = True` donde
    `custom_report_footer` no esté vacío.
  - Recomendación: **no forzar** el cambio en la actualización; que cada cliente
    active el interruptor cuando quiera. Con eso, el default `False` basta y el
    `migrations/` puede omitirse. Se deja escrito aquí para que el usuario
    decida (pregunta 1).
- Subida de versión del manifest a `17.0.2.0.0` (obligatoria por los campos
  nuevos).

---

## 9. Tests previstos (`tests/`, nuevo)
`@tagged("post_install", "-at_install")`, `TransactionCase`. Como el módulo no
tiene `tests/` hoy, se crea `tests/__init__.py` + `tests/test_report_layout.py`.
Casos (renderizar con `env['ir.ui.view']._render_template('web.external_layout', ...)`
o el informe de preview `web.preview_externalreport`, fijando
`company.external_report_layout_id` a cada uno de los 4 diseños):

1. **Desactivado = estándar**: sin activar interruptores, para cada uno de los 4
   layouts, el HTML renderizado contiene el header estándar (logo/`report_header`)
   y el footer estándar (`report_footer`, numeración) y NO contiene la imagen ni
   un header/footer alternativo.
2. **Encabezado por imagen activo**: con `report_header_image_replace=True` y una
   imagen, para los 4 layouts: el HTML contiene el `<img>` del header y NO el
   header estándar (comprobar ausencia del logo/tagline estándar).
3. **Encabezado: imagen presente pero interruptor OFF** ⇒ estándar (no sustituye).
4. **Pie replace activo**: con `custom_report_footer_replace=True` y
   `custom_report_footer` no vacío, para los 4 layouts: el pie personalizado
   aparece y el `report_footer` estándar NO; comprobar también qué pasa con la
   numeración de páginas según la decisión de la pregunta 1.
5. **Pie legacy (append)**: `custom_report_footer_replace=False` con
   `custom_report_footer` ⇒ aparecen AMBOS (comportamiento actual intacto).
6. **Multicompañía**: dos compañías con config distinta; renderizar un documento
   de cada una y comprobar que cada informe usa la config de SU compañía.
7. (Si aplica) `base.document.layout._compute_preview` no rompe al activar los
   campos nuevos (la preview se genera sin excepción).

---

## 10. Riesgos y preguntas abiertas

### Riesgos técnicos
- **`is_html_empty` en el contexto del informe real**: se usa para no activar el
  reemplazo con un pie "vacío" (`<p><br></p>`). Confirmado disponible en la
  preview del asistente; hay que **verificar en el informe PDF real**. Si no
  estuviera, condicionar solo por el booleano `custom_report_footer_replace`.
- **Altura de la imagen vs. márgenes** (`margin_top` 40 mm / `margin_bottom`
  20 mm / `header_spacing` 35, dpi 90): una imagen más alta que el margen se
  recorta o se solapa con el cuerpo. No hay autoajuste nativo. Ver pregunta 4.
- **`xpath` por `t-attf-class`/`t-att-style`**: los selectores propuestos
  dependen de atributos literales de las plantillas del core; si Odoo cambia esas
  plantillas en un parche menor, la herencia podría fallar al cargar. Mitiga:
  usar selectores lo más estables posible (`t-att-style="report_header_style"`
  para header; `contains(@t-attf-class,'o_*_footer')` para footer) y cubrir con
  el test de carga/instalación.
- **Vista previa del asistente ≠ PDF**: es HTML con CSS propio; la imagen y la
  ausencia de numeración pueden verse distintas del PDF. Documentar que la
  preview es orientativa.
- **Repo compartido**: al activar por defecto el modo "append" (default False),
  ningún cliente ve cambios tras actualizar salvo que active los interruptores.
  Esto protege a los clientes existentes.

### Preguntas abiertas / Decisiones a confirmar

1. **Numeración de páginas y datos legales del pie al sustituir por el pie
   personalizado (y, en su caso, por imagen).** Al reemplazar todo el pie
   desaparecen "Page x/y" y el `display_name`/datos legales que hoy pinta el
   layout estándar.
   - *Recomendación*: mantener la numeración de páginas como banda independiente
     DENTRO del pie alternativo (reinsertar el bloque
     `<div t-if="report_type=='pdf'">Page <span class="page"/> / <span
     class="topage"/></div>` debajo del `custom_report_footer`), y dejar que el
     usuario meta sus datos legales en el propio HTML. Así "sustituir todo el
     pie" no implica perder la paginación, que casi siempre se quiere conservar.
   - *Alternativas*: (a) perder la numeración por completo (pie 100% libre);
     (b) hacer configurable con un checkbox "Keep page numbers".
   - Afecta también a si el **script de migración** fuerza o no el modo replace
     (§8): recomendación = no forzar, default `False`.

2. **¿La sustitución aplica también al diseño INTERNO (`web.internal_layout`)?**
   El layout interno (`report_templates.xml:580-616`) tiene su propio header con
   fecha/compañía/paginación y no tiene `report_footer`.
   - *Recomendación*: NO. Limitar la ampliación a los layouts EXTERNOS (es lo que
     ven los clientes). El interno es para informes técnicos internos.
   - *Alternativa*: extender también al interno si algún cliente imprime informes
     internos de cara al exterior (no es el caso conocido).

3. **¿Dónde se configura y quién puede modificarlo?**
   - *Recomendación*: en AMBOS sitios, como ya hace el módulo: formulario de
     compañía (pestaña existente) y asistente de diseño de documento
     (coherente con `report_footer`/`report_header` del core). Permisos: los del
     core (grupo Ajustes). Sin grupo nuevo.
   - *Alternativa*: solo en el asistente de diseño (menos superficie), o crear un
     grupo específico "Report branding" si se quiere separar de Ajustes general.

4. **Altura de la imagen frente a los márgenes del formato de papel.**
   - *Recomendación*: documentar tamaño recomendado (p. ej. ancho completo del
     área útil; alto ≤ `margin_top`-`header_spacing` para el header y
     ≤ `margin_bottom` para el pie, a 90 dpi) en `readme/CONFIGURE.md` (si se crea
     readme) + un `@api.onchange` que AVISE (warning no bloqueante) si procede.
     No tocar automáticamente el `paperformat` de la compañía (efecto global
     peligroso en repo compartido).
   - *Alternativas*: (a) ajustar automáticamente `margin_top`/`margin_bottom` al
     subir imagen (rechazado: afecta a todos los informes de la compañía);
     (b) no hacer nada y dejarlo a criterio del usuario.

5. **Modelo del interruptor y formato/dimensionado de la imagen.**
   - ¿Interruptor booleano explícito (`*_replace`) o usar solo la PRESENCIA de la
     imagen como on/off? *Recomendación*: booleano explícito para el encabezado
     (permite conservar la imagen y desactivar sin borrarla) y booleano para el
     pie (preserva compatibilidad: default False = comportamiento actual).
   - ¿Ofrecer también **pie por imagen** (simetría con el encabezado), además del
     pie HTML? *Recomendación*: de momento NO; el pie ya es HTML y cubre el caso.
     Dejarlo para `ROADMAP` si se pide.
   - Formato/escala de la imagen: *recomendación* `class="w-100"` (ancho
     completo, alto automático) y PNG/JPG; documentar. ¿Se quiere `height` fijo o
     control de alineación? A confirmar.
   - ¿Qué mostrar en pantalla (backend/portal HTML) vs. PDF? *Recomendación*:
     mismo comportamiento (la imagen va en el `.header`/`.footer`, válido en
     ambos); confirmar que en informes HTML (no PDF) el resultado es aceptable.

6. **i18n**: el módulo NO tiene carpeta `i18n/` hoy, y además la etiqueta
   existente (`custom_report_footer` = "Pie del report") y las vistas están en
   español. Los textos NUEVOS de código deben ir en inglés (convención).
   - *Pregunta*: ¿se crea `i18n/es.po` con las traducciones (y se homogeneízan a
     inglés los `string`/`help`, dejando el español en el `.po`)? No se decide
     aquí; por defecto NO se crea la carpeta salvo que el usuario lo pida.

7. **readme/**: el módulo NO tiene `readme/` hoy.
   - *Pregunta*: ¿se crea la estructura `readme/` (DESCRIPTION/USAGE/CONFIGURE) y
     se regenera con `odoo-readme custom_footer_by_company`? Por defecto NO se
     crea salvo petición del usuario.

8. **Errata del nombre de archivo** `template/report_tamplate.xml`.
   - *Pregunta*: ¿renombrar a `report_templates.xml` (requiere actualizar el
     `data` del manifest)? Por defecto NO se renombra (tocar solo lo necesario).

---

### Hallazgo (implementación): wkhtmltopdf y `max-height` (decisión 4)
Verificado con `wkhtmltopdf 0.12.6.1 (patched qt)` de la imagen `odoo-dev:17`, con los mismos
argumentos que `_build_wkhtmltopdf_args` (`--margin-top 40 --header-spacing 15 --dpi 90`):
- CORRECCIÓN: la medición inicial (franja de ~5 mm = `margin_top - header_spacing`) era errónea porque
  se hizo sin el CSS del informe. Con el CSS real, la banda útil de cabecera es ≈ `margin_top` (la
  cabecera estándar ocupa ~36 mm con el formato euro). Por decisión del usuario, el tope de la imagen
  se fija en `margin_top - 3` (37 mm con euro): espacio equivalente al de la cabecera estándar sin
  solaparse con el cuerpo.
- QtWebKit NO soporta `object-fit`: `width:100%` + `max-height` DEFORMA la imagen. Solución aplicada:
  `max-width:100%; max-height:<margin_top - 3>mm` (sin `width`), que conserva la proporción,
  centra (`text-align:center`) y no amplía imágenes pequeñas. El `max-height` se calcula en QWeb con el
  `paperformat_id` de la compañía. Desviación respecto a la decisión 4 ("ancho 100%").
- El pie (se alinea por arriba, se recorta por abajo) se limita a `margin_bottom` con `overflow:hidden`.
- Tamaños recomendados en `readme/CONFIGURE.md`.

---

## 11. Árbol de archivos (ampliación de módulo existente)
No es un módulo nuevo: NO se crean `README.rst`, `static/description/index.html`
ni `readme/` salvo decisión del usuario (preguntas 6-7).

```
custom_footer_by_company/
├── __manifest__.py                 (MODIF: version 17.0.2.0.0)
├── models/
│   └── res_company.py              (MODIF: + campos replace/imagen)
├── template/
│   └── report_tamplate.xml         (MODIF: header por imagen + pie replace, 4 layouts)
├── views/
│   └── res_company_views.xml       (MODIF: campos nuevos en la pestaña)
├── wizards/
│   ├── base_document_layout.py     (MODIF: related + depends del compute preview)
│   └── base_document_layout.xml    (MODIF: campos nuevos en el asistente)
├── migrations/                     (OPCIONAL, solo si se decide forzar modo replace, §8)
│   └── 17.0.2.0.0/
│       └── post-migration.py
└── tests/                          (NUEVO)
    ├── __init__.py
    └── test_report_layout.py
```

---

## Plan de prueba en el VPS del cliente (al implementar)
- Actualizar `custom_footer_by_company` (`odoo-dev 17 actualizar
  custom_footer_by_company` en local primero; tests con `odoo-dev 17 tests
  custom_footer_by_company`).
- En el VPS, por cada uno de los 4 diseños (Ajustes → Diseño de documento):
  imprimir una factura/presupuesto y verificar: (a) sin activar nada = idéntico
  a antes; (b) con encabezado por imagen = imagen a ancho completo, sin header
  estándar; (c) con pie replace = solo el pie personalizado (y paginación según
  decisión 1). Probar con 2 compañías distintas.
```
