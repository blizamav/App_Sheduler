# UI/UX de la reconstruccion

## Estado y alcance

Esta guia define el contrato visual transversal de `src/app_scheduler/` incluido
en el cierre del Hito 7 y extendido hasta Hito 10. Este hito no reemplaza el
pulido final previsto para Hito 12.

La base frontend es Flask + Jinja2 + HTML5 + Bootstrap 5.3.3 + CSS y JavaScript
modulares. Bootstrap se distribuye localmente en
`presentacion/static/vendor/bootstrap/`; QA no depende de Internet ni de CDN.
El bundle incluye los componentes requeridos y no carga Popper por separado.

Assets controlados:

* `bootstrap.min.css`: SHA-256
  `3C8F27E6009CCFD710A905E6DCF12D0EE3C6F2AC7DA05B0572D3E0D12E736FC8`.
* `bootstrap.bundle.min.js`: SHA-256
  `0833B2E9C3A26C258476C46266E6877FC75218625162E0460BE9A3A098A61C6C`.
* Licencia MIT incluida junto a los assets.

## Sistema visual

Los tokens viven en `css/tokens.css`. Blanco y grises frios dominan las
superficies; azul corporativo expresa acciones primarias y cyan moderado aporta
foco. Verde, amarillo y rojo se reservan para exito, advertencia y error. Radios,
sombras, espaciado, z-index y transiciones se definen una sola vez.

El layout usa sidebar estable en escritorio, topbar compacta y contenido fluido
que ocupa todo el ancho disponible. En escritorio el usuario puede contraer la barra a
una franja de iconos; la preferencia se conserva localmente y cada icono mantiene
nombre accesible y `title`. Bajo 992 px la navegacion se convierte en Offcanvas
Bootstrap. El panel agrupa accesos reales por Operacion, Maestros y Seguridad;
no inventa indicadores.

Hito 8 agrega vistas Bootstrap integradas al mismo shell:

* logs con filtros apilables, tabla con scroll local y detalle en bloques `pre`
  de texto autoescapado;
* cards de estado adaptables para worker, scheduler, mantenimiento y capacidad;
* configuracion con switches, rangos visibles, confirmacion modal y matriz ancha
  con scroll local;
* evidencia en la edicion de tarea con estado compatible/requiere ajuste y ayuda
  colapsable del contrato stdout.

Hito 9 agrega Auditoria y Papelera dentro de Administracion, visibles solo con
sus permisos. Auditoria usa filtros compactos, tabla responsive y detalle de
JSON con scroll local. Papelera usa cards operativas con tipo, retiro,
dependencias, badges de capacidad, motivo de bloqueo y acciones separadas. Las
confirmaciones reutilizan el modal Bootstrap global; no se introduce
`window.confirm` ni JavaScript inline.

Hito 10 agrega Feriados y Microsoft Graph al sidebar segun permiso. El
mantenedor usa filtros, tabla responsive, estados y confirmaciones globales; la
sincronizacion separa consulta, preview y aplicacion. La tarea integra
notificaciones, destinatarios y ayuda de evidencia sin una card anidada. La
configuracion Graph distingue datos SQL editables de secretos ENV solo mediante
estados de presencia, nunca valores.

Los layouts usan todo el ancho disponible y cambian a una columna bajo 780 px;
no generan overflow global en 390x844, 768 px, notebook ni 1440x900.

La paleta evita mezclar azules desconectados: azul profundo identifica la
navegacion, azul corporativo las acciones y cyan moderado solo el foco o detalle.
Superficies, bordes y texto comparten la misma escala de grises frios. Los
overrides de escritorio de Offcanvas se declaran de forma explicita para impedir
que Bootstrap vuelva transparente el sidebar.

## Componentes

* Navegacion: `nav-link`, estado activo, enlace clickeable completo, foco visible
  y cierre del Offcanvas al navegar en movil.
* Formularios: labels asociados por envoltura, controles Bootstrap, ayuda,
  `invalid-feedback`, validacion temprana y autoridad final en backend.
* Botones: tipo explicito, estados hover/focus/disabled y texto con spinner para
  evitar doble envio visual.
* Confirmaciones: Modal Bootstrap sobre `submit`; conserva validacion, CSRF y el
  submitter original mediante `requestSubmit()`.
* Tablas: encabezados consistentes, hover, alineacion vertical y contenedor
  responsive. Las celdas conservan su semantica de tabla; las acciones se
  distribuyen dentro de la celda sin convertir el `td` en flex. Las acciones
  numerosas de Tareas se agrupan en dropdown. Mientras ese menu esta abierto,
  el contenedor libera temporalmente su recorte para mostrar todas las opciones.
* Estados: badges con texto y color; empty states con explicacion y CTA solo
  cuando el permiso permite la accion.
* Feedback: flashes en alertas dismissible con `aria-live`; errores importantes
  no dependen de un toast efimero.
* Scripts: cards v1-v3 muestran version activa, protegida o reemplazable, estado,
  `.env` e historial.
* Programaciones: campos no aplicables se ocultan y deshabilitan sin ejecutar
  reglas de negocio en JavaScript.
* Ejecuciones: listado operativo y detalle con consola monoespaciada, polling,
  estado visible y control de auto-scroll.
* Formularios: filas y campos se alinean desde el inicio; un textarea alto no
  estira artificialmente los inputs vecinos.

## Responsive, movimiento y accesibilidad

Los objetivos minimos son 390x844, 768 px, notebook y 1440x900. Filtros y grids
se apilan, las tablas conservan scroll horizontal y la consola evita overflow
global. Modal, dropdown y Offcanvas usan el manejo de teclado/foco de Bootstrap.
No se elimina el outline global. `prefers-reduced-motion` reduce transiciones y
animaciones a una duracion minima.

El estado contraido del sidebar se restaura con un script local bloqueante y
minimo antes de cargar los estilos. Esto evita que una navegacion pinte primero
la barra expandida y luego la contraiga, sin incorporar JavaScript inline.

En movil el Offcanvas conserva la capa Bootstrap `1045`, por encima de su
backdrop, usa alto dinamico `100dvh` y scroll interno de navegacion. El fondo
queda bloqueado por Bootstrap y los enlaces mantienen objetivos tactiles de al
menos 44 px.

Los celulares en orientacion horizontal usan padding compacto, sidebar de hasta
72% del viewport y filtros de dos columnas. Las reglas combinan ancho y
orientacion para evitar que los CSS de cada modulo restauren grillas de cuatro o
cinco columnas. En vertical bajo 620 px los filtros vuelven a una columna.
La navegacion lateral no permite `flex-wrap`: grupos y enlaces permanecen en una
sola columna no reducible y, cuando falta altura, se recorren solo con scroll
vertical.

Paneles y formularios operativos no usan topes artificiales de 900-1440 px:
ocupan el ancho restante despues del sidebar. Se conservan limites solo en
elementos que los necesitan por legibilidad, como login, mensajes y textos de
estado vacio.

## Seguridad frontend y OWASP

No se declara cumplimiento formal de OWASP. Se mantienen controles verificables:

* permisos y contexto de objeto se validan en rutas/servicios, nunca por ocultar
  botones;
* todas las mutaciones pasan por CSRF global;
* autoescape Jinja permanece activo, no se usa `|safe`, JavaScript usa
  `textContent`/DOM seguro y los logs se muestran como texto;
* no hay JavaScript inline, `javascript:`, `eval` ni `new Function` propio;
* CSP local sin `unsafe-inline` ni `unsafe-eval`, anti-framing, `nosniff`,
  Referrer-Policy y Permissions-Policy;
* consultas SQL parametrizadas y ejecucion Python con `shell=False` permanecen
  fuera de la autoridad del frontend;
* credenciales, `.env`, rutas internas y secretos no se incluyen en HTML ni JS;
* uploads conservan extension, tamano, UTF-8, AST, nombre seguro, confinamiento,
  symlink y SHA-256 definidos en Hito 5;
* sesion minima, cookies endurecidas por ambiente, logout POST, limpieza/rotacion
  al autenticar y `next` restringido a destino local.

## Regla transversal

Cada hito nuevo debe entregar funcionalidad, seguridad, pruebas, UI/UX,
responsive e integracion visual. Hito 12 queda reservado para consistencia y
accesibilidad finales, no para reparar interfaces temporales acumuladas.

## Flujo guiado y notificaciones post-Hito 10

Tareas usa un stepper Bootstrap ligero de cinco pasos: Datos, Script,
Evidencia, Notificaciones y Programacion. Es navegacion server-rendered, no una
SPA. En alta se ofrecen `Guardar` y `Guardar y continuar`; la segunda opcion
abre Script despues de persistir la tarea.

La edicion diferencia tres cards: Exito, Error y Evidencia. Los dos primeros
switches son independientes del soporte Evidencia. La card Evidencia informa
`Compatible`, `No implementada` o `Requiere ajuste`, presenta checklist y solo
habilita su switch cuando el script es compatible y el exito esta activo. Las
grillas se reducen a una columna en movil y el stepper usa scroll horizontal
local, sin provocar overflow global.
