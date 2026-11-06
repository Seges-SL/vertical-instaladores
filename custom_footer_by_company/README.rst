===========================
Pie de página personalizado
===========================

.. 
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! Archivo GENERADO por odoo-readme (claude-odoo-kit) a partir de     !!
   !! readme/*.md y del __manifest__.py. No lo edites: se sobrescribe.    !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! fuente: sha256:d5a66201de0c4c2d36455576404bd49db8469240d8071acd3a708ae83894beb0

.. |insignia1| image:: https://img.shields.io/badge/licencia-AGPL--3-blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: Licencia: AGPL-3
.. |insignia2| image:: https://img.shields.io/badge/Odoo-17.0-875A7B.png
    :alt: Odoo 17.0

|insignia1| |insignia2|

Amplía el diseño de documentos externos de Odoo (estándar, negrita, caja y rayas) con dos opciones por compañía:

-  **Cabecera por imagen**: sustituye toda la cabecera estándar (logotipo, eslogan y datos de la compañía) por una imagen.
-  **Pie personalizado**: un pie en HTML que, según la opción elegida, se añade después del pie estándar (comportamiento histórico del módulo) o lo sustituye por completo, con la posibilidad de conservar la numeración de páginas.

Con las opciones desactivadas (valores por defecto) los informes quedan exactamente igual que los de Odoo, o que antes de actualizar el módulo. Cada informe usa la configuración de la compañía del documento. Solo se ven afectados los diseños externos; el diseño interno no se modifica.

**Índice**

.. contents::
   :local:

Configuración
=============

La configuración se puede hacer en **Ajustes > Usuarios y compañías > Compañías > (compañía) > pestaña «Pie de página personalizado»** o en **Ajustes > Configurar diseño del documento**. Se requieren permisos de Ajustes. La vista previa del asistente es orientativa: es HTML y no refleja exactamente el PDF (por ejemplo, la numeración de páginas no aparece en la vista previa).

-  **Replace standard header with image** (Sustituir la cabecera estándar por la imagen): activa la cabecera por imagen. Solo actúa si además se ha cargado la imagen.
-  **Replace standard footer** (Sustituir el pie estándar): si está activo, el pie personalizado sustituye todo el pie estándar. Si no, se añade tras el pie estándar. Si el pie personalizado está vacío no se sustituye nada.
-  **Keep page numbers** (Mantener la numeración de páginas): activo por defecto; al sustituir el pie, mantiene la banda «Página x / y» (solo PDF) bajo el pie personalizado.

Tamaño de la imagen de cabecera
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Con el formato de papel por defecto (A4 europeo, margen superior de 40 mm) el módulo limita la imagen a **unos 37 mm de alto** (margen superior − 3 mm) y a todo el ancho útil, respetando su proporción. No la amplía por encima de su tamaño natural; una imagen más alta se reduce y queda más estrecha y centrada.

Tamaño recomendado para A4: ancho útil de unos 196 mm (210 mm menos 7 + 7 mm de márgenes laterales) por el alto útil, a unos 250 ppp (≈ 10 px por mm), es decir, **unos 1960 × 370 px** por defecto. Formatos PNG o JPG.

Cabecera más alta (opcional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Si se quiere una cabecera por imagen de más de unos 37 mm, cree un formato de papel propio (Ajustes > Técnico > Informes > Formatos de papel, duplicando «A4») con un mayor ``margen superior``, y **selecciónelo en el asistente de diseño del documento**. No edite el formato de papel compartido, porque es el predeterminado de todas las compañías.

Aviso: los informes que definen su propio formato de papel ignoran el de la compañía.

=================== ====================== ================
Margen superior     Alto útil de la imagen Recomendado (A4)
=================== ====================== ================
40 mm (por defecto) ~37 mm                 1960 × 370 px
50 mm               ~47 mm                 1960 × 470 px
60 mm               ~57 mm                 1960 × 570 px
=================== ====================== ================

Pie personalizado
~~~~~~~~~~~~~~~~~

Cuando sustituye al pie estándar, el pie queda limitado por el **margen inferior del formato de papel** (32 mm por defecto en A4 europeo). En el PDF, wkhtmltopdf recorta unos 4 mm por abajo, así que la altura útil real es menor:

+-----------------------------------+-----------------------------------+
| Caso (A4 europeo, margen inferior | Altura útil del contenido         |
| 32 mm)                            |                                   |
+===================================+===================================+
| Sin numeración                    | **~28 mm**                        |
| (``Keep page numbers``            |                                   |
| desactivado)                      |                                   |
+-----------------------------------+-----------------------------------+
| Con ``Keep page numbers`` (por    | **~23 mm** de contenido, más la   |
| defecto)                          | línea de numeración debajo        |
+-----------------------------------+-----------------------------------+

Con otro formato de papel, el contenido se limita a ``margen inferior − 9 mm`` si se mantiene la numeración y al margen inferior si no.

**Aviso:** si el pie es más alto que el espacio disponible, **su parte inferior se recorta SIN AVISO**. Por eso hay que **comprobarlo siempre en el PDF impreso, no en la vista previa** del asistente, que es HTML y no refleja el recorte.

Vista de código HTML del pie
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

El campo del pie (en la compañía y en el asistente de diseño del documento) tiene activada la opción de vista de código: un botón ``<>`` permite ver y editar el HTML. **Este botón solo aparece en modo desarrollador** (Odoo lo exige además de la opción, que ya está activada en la vista).

Ejemplo de pie con **dos imágenes en la misma línea** (imágenes en línea dentro de un ``<p>``, de unos 12 mm de alto para que quepan en el pie):

.. code:: html

   <p style="text-align:center; margin:0;">
     <img src="/web/image/…logo1…" style="height:12mm; margin-right:10mm;"/>
     <img src="/web/image/…logo2…" style="height:12mm;"/>
   </p>

Uso
===

1. Configure las opciones en la compañía o en el asistente de diseño de documentos (ver la sección de configuración).
2. Elija el diseño de documento (estándar, negrita, caja o rayas) en **Ajustes > Configurar diseño del documento**; las opciones funcionan con los cuatro.
3. Imprima cualquier documento externo (presupuesto, factura, etc.) de esa compañía: se verá la imagen de cabecera y/o el pie personalizado según las opciones activas.
4. En empresas con varias compañías, cada documento usa la configuración de su propia compañía.

Nota: la vista previa del asistente es HTML orientativa; la numeración de páginas y el recorte exacto solo se aprecian en el PDF.

Limitaciones y mejoras pendientes
=================================

-  La cabecera por imagen está limitada por la franja que wkhtmltopdf reserva (margen superior menos espaciado de cabecera); con el formato europeo por defecto es muy pequeña y hay que ajustar el formato de papel.
-  No hay pie por imagen, solo pie HTML.
-  No se modifica el diseño interno (``web.internal_layout``).
-  Las dimensiones se calculan con el formato de papel de la compañía; un informe con formato de papel propio puede tener otra franja de cabecera.

Incidencias
===========

Si encuentras un error o tienes una propuesta de mejora, comunícalo al equipo de desarrollo de Seges indicando el módulo, la versión y los pasos para reproducirlo.

Créditos
========

Autores
-------

* Seges

Mantenimiento
-------------

Este módulo lo mantiene Seges.

Forma parte del repositorio `Seges-SL/vertical-instaladores <https://github.com/Seges-SL/vertical-instaladores/tree/17.0/custom_footer_by_company>`_.
