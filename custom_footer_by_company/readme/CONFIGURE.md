La configuración se puede hacer en **Ajustes > Usuarios y compañías > Compañías > (compañía) > pestaña «Pie de página personalizado»** o en **Ajustes > Configurar diseño del documento**. Se requieren permisos de Ajustes. La vista previa del asistente es orientativa: es HTML y no refleja exactamente el PDF (por ejemplo, la numeración de páginas no aparece en la vista previa).

* **Replace standard header with image** (Sustituir la cabecera estándar por la imagen): activa la cabecera por imagen. Solo actúa si además se ha cargado la imagen.
* **Replace standard footer** (Sustituir el pie estándar): si está activo, el pie personalizado sustituye todo el pie estándar. Si no, se añade tras el pie estándar. Si el pie personalizado está vacío no se sustituye nada.
* **Keep page numbers** (Mantener la numeración de páginas): activo por defecto; al sustituir el pie, mantiene la banda «Página x / y» (solo PDF) bajo el pie personalizado.

### Tamaño de la imagen de cabecera

Con el formato de papel por defecto (A4 europeo, margen superior de 40 mm) el módulo limita la imagen a **unos 37 mm de alto** (margen superior − 3 mm) y a todo el ancho útil, respetando su proporción. No la amplía por encima de su tamaño natural; una imagen más alta se reduce y queda más estrecha y centrada.

Tamaño recomendado para A4: ancho útil de unos 196 mm (210 mm menos 7 + 7 mm de márgenes laterales) por el alto útil, a unos 250 ppp (≈ 10 px por mm), es decir, **unos 1960 × 370 px** por defecto. Formatos PNG o JPG.

### Cabecera más alta (opcional)

Si se quiere una cabecera por imagen de más de unos 37 mm, cree un formato de papel propio (Ajustes > Técnico > Informes > Formatos de papel, duplicando «A4») con un mayor `margen superior`, y **selecciónelo en el asistente de diseño del documento**. No edite el formato de papel compartido, porque es el predeterminado de todas las compañías.

Aviso: los informes que definen su propio formato de papel ignoran el de la compañía.

| Margen superior | Alto útil de la imagen | Recomendado (A4) |
|---|---|---|
| 40 mm (por defecto) | ~37 mm | 1960 × 370 px |
| 50 mm | ~47 mm | 1960 × 470 px |
| 60 mm | ~57 mm | 1960 × 570 px |

### Pie personalizado

Cuando sustituye al pie estándar, el pie queda limitado por el **margen inferior del formato de papel** (32 mm por defecto en A4 europeo). En el PDF, wkhtmltopdf recorta unos 4 mm por abajo, así que la altura útil real es menor:

| Caso (A4 europeo, margen inferior 32 mm) | Altura útil del contenido |
|---|---|
| Sin numeración (`Keep page numbers` desactivado) | **~28 mm** |
| Con `Keep page numbers` (por defecto) | **~23 mm** de contenido, más la línea de numeración debajo |

Con otro formato de papel, el contenido se limita a `margen inferior − 9 mm` si se mantiene la numeración y al margen inferior si no.

**Aviso:** si el pie es más alto que el espacio disponible, **su parte inferior se recorta SIN AVISO**. Por eso hay que **comprobarlo siempre en el PDF impreso, no en la vista previa** del asistente, que es HTML y no refleja el recorte.

### Vista de código HTML del pie

El campo del pie (en la compañía y en el asistente de diseño del documento) tiene activada la opción de vista de código: un botón `<>` permite ver y editar el HTML. **Este botón solo aparece en modo desarrollador** (Odoo lo exige además de la opción, que ya está activada en la vista).

Ejemplo de pie con **dos imágenes en la misma línea** (imágenes en línea dentro de un `<p>`, de unos 12 mm de alto para que quepan en el pie):

```html
<p style="text-align:center; margin:0;">
  <img src="/web/image/…logo1…" style="height:12mm; margin-right:10mm;"/>
  <img src="/web/image/…logo2…" style="height:12mm;"/>
</p>
```
