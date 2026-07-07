# Auditoria visual UI SOEX - Fase UI-7

Fecha: 2026-07-07  
Alcance: diagnostico visual y plan de pulido. No se implementan cambios funcionales ni visuales en esta fase.

## Nota de avance UI-8

El 2026-07-07 se ejecuto la Fase UI-8 sobre Tareas, Scripts y Ejecuciones. Se aplico pulido visual acotado a plantillas y CSS: jerarquia de listados, acciones agrupadas, secciones operativas, versionamiento de scripts, lectura diagnostica de ejecuciones y consola/log. No se modifico backend, rutas, permisos, Graph, evidencias, worker ni base de datos.

## 1. Diagnostico general

La aplicacion ya tiene una base visual corporativa consistente: sidebar oscuro, topbar clara, tarjetas blancas, badges por estado, botones reutilizables, tablas comunes, mensajes flotantes y acentos SOEX controlados. La direccion visual es correcta para una herramienta operativa TI.

El principal problema pendiente no es la paleta, sino la organizacion por modulo. Varias pantallas crecieron funcionalmente y ahora concentran demasiadas acciones, badges, ayudas y tablas en una sola vista. Esto afecta escaneo rapido, jerarquia y claridad operacional.

Patrones detectados:

* Los modulos administrativos simples se ven consistentes, pero algo genericos.
* Los modulos operativos complejos necesitan jerarquia secundaria: resumen, estado principal, acciones primarias, acciones peligrosas y detalle tecnico separados.
* Hay filtros extensos que ocupan demasiado espacio antes del contenido real.
* Las tablas tienen buen tratamiento base, pero en pantallas densas requieren columnas priorizadas, acciones agrupadas y estados mas legibles.
* Algunos mensajes permanentes usan clases de alerta global y se perciben como toasts aunque son informacion estructural.
* El panel lateral de logs esta bien orientado, pero puede mejorar densidad, niveles visuales y lectura de eventos.

## 2. Diagnostico por modulo

### Panel

Se ve bien:

* Buena entrada ejecutiva con saludo, acciones rapidas y metricas.
* Tarjetas de metricas claras y coherentes con el resto de la app.
* Estados y badges son comprensibles.

Pendiente:

* El dashboard mezcla resumen ejecutivo, accesos, estado general y ultimas ejecuciones con jerarquia similar.
* Las acciones rapidas compiten visualmente con los indicadores.
* Falta una lectura mas ejecutiva de "requiere atencion" versus "solo informacion".

Pulido sugerido:

* Crear una franja superior de salud operativa con 3-4 estados clave.
* Separar acciones rapidas de metricas.
* Dar mas peso visual a errores/advertencias reales y menos a contadores neutros.

### Usuarios

Se ve bien:

* Filtros, tabla y formulario siguen patrones comunes.
* Badges de rol y estado ayudan a leer permisos.
* Acciones de cambio de estado usan confirmacion.

Pendiente:

* La tabla tiene muchas acciones en una celda y puede crecer horizontalmente.
* El texto descriptivo del hero es largo para una pantalla administrativa recurrente.
* Roles protegidos y acciones disponibles podrian distinguirse con mayor claridad visual.

Pulido sugerido:

* Compactar hero y filtros.
* Agrupar acciones por prioridad: editar como accion principal, estado/borrado como secundarias.
* Mejorar chips de rol para diferenciar SUPER_ADMIN, ADMIN y roles normales.

### Clientes, Categorias y Tipos

Se ve bien:

* Los tres mantenedores comparten plantilla y son consistentes.
* La estructura es simple y predecible.

Pendiente:

* Se perciben como genericos por usar exactamente el mismo titulo, tabla y descripcion.
* Falta contexto visual de impacto: donde se usa cada maestro.
* Las acciones editar/activar/borrar tienen el mismo peso.

Pulido sugerido:

* Agregar microresumen por entidad: activos, inactivos, usados en tareas.
* Diferenciar accion principal de acciones destructivas.
* Ajustar textos por entidad para que no parezcan plantilla base.

### Tareas

Se ve bien:

* Es el modulo mas completo a nivel operacional.
* El listado muestra contexto, programacion, feriados, ejecutabilidad y acciones.
* El formulario separa datos generales, programacion y notificaciones.

Pendiente:

* Alta densidad en listado: muchos filtros, columnas y acciones por fila.
* "No ejecutable" puede volverse muy largo dentro de un badge.
* El formulario de edicion concentra configuracion de tarea y notificaciones/evidencia en una sola pagina extensa.
* Checkboxes y ayudas de notificaciones pueden verse como bloque tecnico pesado.

Pulido sugerido:

* Convertir acciones por fila en grupo ordenado: editar/scripts como primarias; ejecutar destacada; activar/borrar en menu o zona secundaria.
* Resumir ejecutabilidad con estado corto y detalle aparte.
* Separar visualmente notificaciones como subpanel con tabs o secciones mas compactas.
* Mejorar jerarquia del bloque evidencia: estado de compatibilidad primero, configuracion despues.

### Scripts

Se ve bien:

* Flujo de script activo, carga de version y tabla de versiones esta completo.
* Badges de version activa y estado .env ayudan al usuario TI.
* Respeta separacion entre script y .env.

Pendiente:

* Pantalla muy densa en acciones: activar, .env, reemplazar, desactivar, borrar.
* Los paneles desplegables dentro de filas pueden sentirse pesados y romper lectura de tabla.
* Las acciones peligrosas no quedan suficientemente separadas de acciones normales.
* La ruta relativa puede ocupar mucho ancho.

Pulido sugerido:

* Crear cards por version o tabla con accion principal y menu secundario.
* Separar administracion de .env en un bloque dedicado o panel lateral.
* Reforzar visualmente version activa y maximo 3 versiones.
* Usar textos mas cortos para usuario TI recurrente.

### Ejecuciones

Se ve bien:

* El historial agrupado por anio/mes/dia da contexto temporal.
* La consola tiene buen contraste y lectura tecnica.
* El detalle muestra estado, metadata, log y acciones.

Pendiente:

* El formulario de filtros es muy grande y desplaza el historial.
* En ejecuciones, el estado `ERROR` en listado agrupado cae en `inactivo` en algunos casos visuales, lo que reduce urgencia.
* El usuario necesita entender rapidamente que fallo: hoy depende mucho de abrir consola.
* La consola no diferencia visualmente INFO/WARN/ERROR dentro del log.

Pulido sugerido:

* Crear filtros colapsables o compactos con resumen de filtros activos.
* Destacar errores y ejecuciones en curso en el listado.
* Agregar bloque "resultado rapido" en detalle: codigo salida, duracion, ultimo error/resumen si existe.
* Mejorar legibilidad de consola con niveles, busqueda o resaltado liviano.

### Programador

Se ve bien:

* Panel operativo contiene buen detalle de heartbeat, eventos, configuracion, feriados y candidatas.
* Estados del worker y programador estan visibles.
* Eventos del programador tienen filtros completos.

Pendiente:

* El panel programador es extenso y puede sentirse como reporte tecnico largo.
* Hay muchas tablas con el mismo peso visual.
* Eventos + limpieza controlada compiten en una misma pantalla.
* Configuracion programador es clara, pero los toggles criticos pueden requerir mayor peso de riesgo.

Pulido sugerido:

* Reordenar panel en capas: salud, senal de vida, alertas, actividad, detalle.
* En eventos, separar historial de limpieza controlada con mejor jerarquia visual.
* En configuracion, destacar parametros que detienen o permiten ejecuciones automaticas.
* Consolidar componentes de estado del scheduler para panel, eventos y configuracion.

### Feriados

Se ve bien:

* Listado, formulario y sincronizacion estan alineados al resto de mantenedores.
* La vista previa de sincronizacion es clara y controlada.

Pendiente:

* Feriados se percibe mas como tabla administrativa que calendario operativo.
* No hay lectura rapida de proximos feriados o impacto en programador.
* La sincronizacion tiene tablas anchas y muchos badges en cabecera.

Pulido sugerido:

* Agregar resumen de proximos feriados y feriados activos del anio.
* Mejorar lectura de origen manual/API y feriado irrenunciable.
* Compactar vista previa de sincronizacion para destacar acciones propuestas.

### Mail Automatico

Se ve bien:

* La pantalla comunica separacion entre origen, destinatarios y contenido.
* Campos sensibles estan ocultos por defecto y con accion explicita.
* El estado global es visible.

Pendiente:

* Hay mensajes informativos redundantes respecto al hero.
* La pantalla mezcla resumen, explicacion, seguridad y edicion con peso similar.
* El panel de parametros sensibles dentro del formulario puede intimidar visualmente.

Pulido sugerido:

* Crear bloque superior de estado: activo, secret configurado, buzon, ultima actualizacion.
* Separar "seguridad Graph" de "parametros editables".
* Reducir mensajes duplicados y dejar ayudas mas contextuales.
* Dar una identidad visual mas de consola administrativa SUPER_ADMIN.

### Auditoria

Se ve bien:

* Listado formal con filtros completos.
* Detalle de auditoria separa usuario, entidad, descripcion y valores antes/despues.
* Buen uso de pre para valores tecnicos.

Pendiente:

* Filtros son densos y similares a ejecuciones/eventos.
* Tabla puede ser muy ancha y la descripcion truncada puede ocultar lo importante.
* El detalle podria destacar mejor resultado, entidad y cambio principal antes de datos tecnicos.

Pulido sugerido:

* Filtros colapsables o barra compacta por campos mas usados.
* En listado, mostrar accion/resultado/modulo como lectura primaria.
* En detalle, agregar resumen superior del cambio con estado y entidad afectada.

### Papelera operativa

Se ve bien:

* Comunica correctamente historial protegido y acciones peligrosas.
* Usa confirmaciones fuertes para eliminacion permanente.
* Incluye resumen de procesos masivos.

Pendiente:

* Es una pantalla de alto riesgo y tiene muchas acciones destructivas visibles.
* Tabla muy ancha y con muchos estados simultaneos.
* Algunos textos muestran caracteres mal codificados en confirmaciones.

Pulido sugerido:

* Reforzar separacion visual entre restaurar y eliminar permanentemente.
* Agrupar eliminacion permanente en zona de peligro diferenciada.
* Revisar textos con caracteres corruptos.
* Resumir dependencias/bloqueo con chips y detalle expandible.

### Logs

Se ve bien:

* Panel lateral de logs esta disponible desde la app autenticada.
* Consola reciente usa fondo oscuro y lectura tecnica.
* Cards de estado de worker, scheduler, automatica y senal ayudan al diagnostico.

Pendiente:

* No hay resaltado visual por nivel INFO/WARN/ERROR.
* La consola puede ser densa si hay muchas lineas.
* Alertas operativas y actividad reciente podrian diferenciar mejor eventos criticos de ruido.
* El panel lateral tiene mucha informacion para un espacio angosto.

Pulido sugerido:

* Agregar niveles visuales en log si el formato lo permite.
* Mejorar densidad de terminal y scroll.
* Separar alertas criticas de actividad informativa.
* Agregar controles de copia/filtro mas visibles y compactos.

## 3. Problemas visuales detectados

* Densidad alta en Tareas, Scripts, Ejecuciones, Programador y Papelera.
* Filtros extensos ocupan demasiado espacio en vistas de historial.
* Acciones destructivas conviven con acciones normales sin suficiente separacion visual.
* Estados largos dentro de badges reducen legibilidad.
* Tablas operativas con muchas columnas requieren priorizacion responsive.
* Hay mensajes permanentes que visualmente parecen toasts o alertas de evento.
* Algunos textos siguen muy tecnicos o largos para vistas recurrentes.
* Existen caracteres corruptos en algunos mensajes de Papelera.

## 4. Priorizacion

### Alta prioridad

* Tareas: reducir densidad de listado y ordenar acciones por prioridad.
* Scripts: separar acciones normales, .env y acciones peligrosas.
* Ejecuciones + Logs: mejorar lectura rapida de errores y consola.
* Papelera: separar zona de peligro y corregir textos corruptos.

### Media prioridad

* Programador: reorganizar panel operativo y eventos por capas de importancia.
* Mail Automatico: separar resumen, seguridad y edicion.
* Auditoria: compactar filtros y mejorar resumen de detalle.
* Usuarios: compactar acciones y reforzar chips de rol.

### Baja prioridad

* Panel: ajustar jerarquia ejecutiva.
* Clientes/Categorias/Tipos: agregar contexto y pequenos resumenes.
* Feriados: sumar lectura calendario/proximos feriados.

## 5. Propuesta de fases siguientes

### UI-8 - Pulido Panel + Usuarios + Mantenedores

Objetivo: estabilizar patron visual de pantallas administrativas simples.

Archivos probables:

* `app/templates/panel.html`
* `app/templates/usuarios/listado.html`
* `app/templates/usuarios/formulario.html`
* `app/templates/mantenedores/listado.html`
* `app/templates/mantenedores/formulario.html`
* `app/static/css/estilos.css`
* `app/static/js/app.js` solo si se requiere interaccion visual menor.

### UI-9 - Pulido Tareas + Scripts

Objetivo: reducir densidad operativa, ordenar acciones y reforzar claridad para usuario TI.

Archivos probables:

* `app/templates/tareas/listado.html`
* `app/templates/tareas/formulario.html`
* `app/templates/scripts/listado.html`
* `app/static/css/estilos.css`
* `app/static/js/app.js`

### UI-10 - Pulido Ejecuciones + Logs

Objetivo: acelerar diagnostico de ejecuciones, errores y consola.

Archivos probables:

* `app/templates/ejecuciones/listado.html`
* `app/templates/ejecuciones/consola.html`
* `app/templates/base.html`
* `app/static/css/estilos.css`
* `app/static/js/app.js`

### UI-11 - Pulido Programador + Feriados

Objetivo: reorganizar salud del scheduler, eventos, configuracion y calendario.

Archivos probables:

* `app/templates/scheduler/panel.html`
* `app/templates/scheduler/eventos.html`
* `app/templates/scheduler/_eventos_historial.html`
* `app/templates/scheduler/configuracion.html`
* `app/templates/feriados/listado.html`
* `app/templates/feriados/sincronizar.html`
* `app/templates/feriados/formulario.html`
* `app/static/css/estilos.css`
* `app/static/js/app.js`

### UI-12 - Pulido Mail Automatico + Auditoria + Papelera

Objetivo: mejorar pantallas sensibles, trazabilidad y acciones de riesgo.

Archivos probables:

* `app/templates/configuracion/mail_graph.html`
* `app/templates/auditoria/listado.html`
* `app/templates/auditoria/detalle.html`
* `app/templates/papelera/listado.html`
* `app/static/css/estilos.css`
* `app/static/js/app.js`

## 6. Riesgos

* Cambios visuales en tablas densas pueden afectar responsive si no se prueban con datos largos.
* Agrupar acciones puede ocultar comandos usados frecuentemente por usuarios TI.
* Mejorar consola/logs requiere cuidar rendimiento con mucho texto.
* Cambios en pantallas sensibles como Papelera y Mail Automatico deben mantener confirmaciones y mensajes de seguridad.
* Cualquier pulido futuro debe evitar tocar permisos, rutas, backend, Graph, worker o BD.

## 7. Confirmaciones de alcance

* No se implementaron cambios funcionales.
* No se modifico backend.
* No se modificaron rutas.
* No se modificaron permisos.
* No se modifico Graph.
* No se modificaron evidencias.
* No se modificaron alertas operativas.
* No se modifico worker ni `scheduler_worker.py`.
* No se modifico base de datos.
* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se modifico `.env.docker`.
* No se toco `database/release/`.
* No se hizo commit.
* No se hizo push.
