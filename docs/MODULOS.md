# Modulos

## Implementados

* Login inicial desde `.env`.
* Panel principal general con metricas reales.
* Layout corporativo inicial.
* Diseno UI/UX base responsive de Fase 2.
* Propuesta de modelo SQL Server inicial en Fase 3, sin implementacion fisica.
* Ajuste documental Fase 3A para versionamiento controlado de scripts con maximo 3 versiones.
* Scripts SQL Server versionados de Fase 3B creados en `database/`, sin ejecucion automatica.
* Conexion Flask-SQL Server desde `.env` y diagnostico `/diagnostico/bd`.
* Fase 4 inicial: login hibrido `.env` + SQL Server.
* Fase 4 inicial: administracion basica de usuarios, roles y permisos.
* Fase 4 inicial: logs de sistema para login y cambios de usuarios.
* Fase 4.1: filtros, confirmaciones y mejoras UX del modulo usuarios.
* Fase 4.3: definicion tecnica de ejecucion segura, detencion manual y `.env` por script.
* Fase 5: mantenedores funcionales de clientes, categorias y tipos.
* Fase 5.1: eliminacion fisica controlada en mantenedores solo cuando no existen dependencias.
* Fase 6: tareas con programacion base.
* Fase 7: gestion de scripts, versiones y `.env` por version.
* Fase 8: ejecucion manual con consola, logs y detencion controlada.
* Fase 9A: configuracion operativa del scheduler en base de datos.
* Fase 9B: worker automatico separado y ejecuciones automaticas.
* Fase 9D: historial agrupado de ejecuciones con filtros y paginacion.
* Fase 10A: calendario local de feriados en base de datos.
* Fase 10B: sincronizacion controlada desde Nager.Date con reglas locales.
* Fase 11A: panel operativo del scheduler.
* Fase 11A.1: panel principal general con metricas reales y accesos operativos.
* Fase 11B: heartbeat del worker scheduler.
* Fase 11C: modernizacion visual UI/UX general sin cambios funcionales.
* Fase 11D: eventos y omisiones del programador en tabla dedicada.
* Fase 11D.1: resumen inteligente y retencion logica de eventos.
* Fase 11D.2: historial filtrable de eventos del programador.
* Fase 11E: control de ejecuciones huerfanas.
* Fase 11F: borrado operativo seguro con snapshots historicos.
* Fase 11G: papelera operativa, restauracion y eliminacion permanente segura.
* Fase 12B.1D-Papelera: eliminacion permanente masiva segura desde `/papelera`, ejecutada item por item con modal fuerte, resumen y auditoria.
* Fase 11H: desacople historico para eliminacion permanente real desde papelera.
* Fase 11I: revision integral post-borrado y endurecimiento de historial por snapshots.
* Fase 12A: auditoria base con `/auditoria`, detalle, filtros y registro inicial de acciones humanas criticas.
* Fase 12A.1: correccion visual del detalle de auditoria y reglas criticas de jerarquia `SUPER_ADMIN`/`ADMIN`.
* Fase 12A.2: validacion transversal de duplicados considerando registros activos, inactivos y en Papelera Operativa.
* Fase 12B: cobertura ampliada de auditoria, acciones normalizadas, bloqueos `BLOQUEADO`, errores controlados `ERROR` y sanitizacion reforzada.
* Fase 12B.1A: cierre garantizado de ejecucion manual para evitar ejecuciones huerfanas en condiciones normales.
* Fase 12B.1B: sincronizacion visual de consola para badge, resumen, acciones y toast de termino sin recarga completa.
* Fase 12B.1C: validacion operativa de ejecucion manual iniciada; pendiente de pruebas reales completas en entorno con login y SQL Server operativo.
* Fase 12B.1D: modernizacion visual del app shell, sidebar responsive, topbar, tablas, grillas y componentes compartidos.
* Fase 12B.1E: rediseno visual profundo del shell con sidebar iconografico textual, topbar compacta y ajustes visuales generales sin cambios funcionales.
* Fase 12B.1F: correccion profunda del shell visual, sidebar con scroll flexible robusto y modernizacion UI/UX premium sin cambios funcionales.
* Fase 12B.2: validacion real del `scheduler_worker.py` iniciada; bloqueada por error ODBC local, con correccion acotada de cierre seguro en ejecuciones automaticas y robustez de heartbeat.
* Fase 13A.1: optimizacion de `scheduler_eventos` y limpieza controlada de eventos informativos antiguos.
* Fase 13A.1B: limpieza parametrizable de eventos del scheduler con whitelist de categorias y previsualizacion.
* Fase 14B.1: logging controlado del worker con `app/servicios/servicio_logging_worker.py`, salida simultanea a terminal y buffer visual `logs/worker_console.log`.
* Fase 14C: API interna de monitoreo del worker con `/api/worker/estado`, `/api/worker/consola`, `/api/worker/monitor`, `/api/worker/eventos` y `/api/worker/ejecuciones`.
* Fase 14D: panel lateral `Logs` conectado a la API del worker, con estado operativo, alertas, consola reciente, eventos y ejecuciones recientes.
* Fase 14D.1: claridad visual del monitor del programador, separacion entre estado de vista y estado real del worker, y panel lateral redimensionable.
* Fase 14D.2: simplificacion del monitor del programador para mostrar solo eventos propios del worker/programador, con estados visuales reutilizables y sin mezclar ejecuciones manuales.
* Fase 14D.3: correccion de estados reales del programador para distinguir `DETENIDO`, `ADVERTENCIA`, `SIN SENAL` y `NO DISPONIBLE` segun heartbeat real y detencion explicita.
* Fase 14E: operacion del worker como proceso separado con `Dockerfile`, `docker-compose.yml`, volumenes compartidos de runtime y comandos documentados para `web` y `worker`.
* Fase 14F.1: diagnostico seguro del panel principal, con alertas visibles por bloque fallido y logging tecnico controlado cuando SQL Server no responde.
* Fase 14F.2: normalizacion segura de la cadena SQL Server ODBC con parametros explicitos `DB_ENCRYPT`, `DB_TRUST_SERVER_CERTIFICATE` y `DB_TIMEOUT`, resumen seguro de conexion y soporte opcional `DOCKER_ENV_FILE`.
* Fase 15A.1: contrato documental de evidencia por `stdout`, con delimitadores oficiales, validacion estatica requerida y regla de no guardar JSON fisico persistente ni JSON completo en BD.
* Fase 15B: modelo documental minimo para evidencias y notificaciones, separando configuracion por tarea, destinatarios, evidencia por ejecucion e intentos de envio Graph.
* Fase 15D: backend minimo de configuracion de notificaciones por tarea, con servicio, repositorio y API JSON protegida por permisos de tareas.
* Correccion UX de disponibilidad de ejecucion en `/tareas`: estado `Ejecutable` o `No ejecutable` con motivo visible y diagnostico manual de scripts/versiones.

## Modulos pendientes

Ver detalle formal en `docs/ROADMAP.md`.

Pendiente critico inmediato:

* Fase 12C: trazabilidad extendida de auditoria, mejoras avanzadas y exportaciones futuras cuando se autorice.

Pendiente operativo:

* Scripts adicionales de automatizacion Windows/Linux.
* Estrategia de backups.
* Estrategia de retencion automatica.

Pendiente mejora:

* Exportacion de eventos.
* Notificaciones.
* Reportes.
* Dashboard avanzado.
* Fase 15E+: UI de configuracion, capturador de evidencia por `stdout`, integracion Graph, alertas internas y validacion QA.

## Definicion Fase 4.3

Antes de implementar tareas, scripts y scheduler se definio:

* Cada version de script podra indicar si requiere `.env`.
* Los `.env` de scripts viviran en `env_scripts/`, separados del codigo en `scripts/`.
* La base guardara solo rutas de `.env`, no secretos.
* Las ejecuciones registraran `pid_proceso` y datos de detencion manual.
* La interfaz futura debera permitir detener ejecuciones solo si estan `EN_EJECUCION`.
* Toda detencion debe confirmarse con modal corporativo y registrarse en logs.

## Estado de implementacion

La aplicacion esta en Fase 14E a nivel operativo del worker: usuarios, roles, permisos, mantenedores base, tareas, scripts versionados, `.env` por script, ejecucion manual con cierre garantizado, consola sincronizada sin recarga completa, detencion manual, configuracion scheduler, worker automatico separado, historial de ejecuciones, calendario local de feriados, sincronizacion controlada desde Nager.Date, panel operativo del scheduler, panel principal general con metricas reales, heartbeat del worker, modernizacion visual general, rediseno visual profundo del shell, correccion visual premium del app shell, eventos operativos del programador, resumen inteligente, vista filtrable de eventos, control de ejecuciones huerfanas, borrado operativo seguro con snapshots, papelera operativa con eliminacion permanente individual y masiva segura, desacople historico para eliminacion permanente real, revision post-borrado, disponibilidad visible de ejecucion manual en `/tareas`, auditoria base, reglas reforzadas de jerarquia de roles, validacion transversal de duplicados, cobertura ampliada de auditoria, logging controlado del worker con buffer visual acotado, monitor lateral enfocado solo en eventos del programador con estados reales del worker y despliegue base con `web` y `worker` separados en Docker Compose. La validacion real de `scheduler_worker.py` sigue condicionada al entorno con SQL Server accesible.

Fase 15A.1 solo agrega definicion documental del contrato de evidencias y reportes por Microsoft Graph. Fase 15B agrega el modelo documental minimo. No hay capturador, tablas fisicas, UI ni envio implementados en estas fases.

Fase 15D agrega backend minimo para consultar, guardar y desactivar configuracion de notificaciones por tarea mediante API JSON. No envia correos, no captura `stdout`, no valida todavia delimitadores del script y no implementa Microsoft Graph.

## UI/UX general

Implementado en Fase 11C:

* Modernizacion visual de sidebar, topbar, botones, cards, tablas, formularios, filtros, modales, toasts, consola e historial.
* Ajuste de textos visibles para usar `Programador`, `Proceso programador` y `Senal de vida` en vez de mezclar ingles en la interfaz.
* Retiro de etiquetas visibles de fases en pantallas operativas.
* Mejora de hover, focus, sombras, bordes, estados y responsive basico.

No implementado en Fase 11C:

* No se agregan funcionalidades nuevas.
* No se modifica logica de permisos, consultas, ejecuciones, scheduler ni feriados.
* No se crean migraciones.

## Panel principal general

Implementado en Fase 11A.1:

* `/panel`: resumen ejecutivo de tareas, scripts, ejecuciones, scheduler y feriados.
* Metricas leidas desde SQL Server mediante `repositorio_panel.py`.
* Servicio `servicio_panel.py` para normalizar datos y entregar estado general.
* Ultimas ejecuciones con enlace a consola.
* Accesos rapidos visibles segun permisos de la sesion.
* Estado de heartbeat del worker integrado desde Fase 11B.
* Fase 14F.1: cuando falla SQL Server, `/panel` deja trazabilidad visible por origen (`metricas_panel`, `configuracion_scheduler`, `ejecuciones_recientes`) y evita que los valores `0` se interpreten como datos reales.

Estado desde Fase 11B:

* El panel principal puede mostrar estado de heartbeat mediante la capa de servicio.
* No inicia ni detiene el worker.
* No crea acciones operativas para controlar el proceso desde la app.

## Modulo de ejecuciones

Implementado en Fase 8:

* `/tareas/<id_tarea>/ejecutar`: inicia ejecucion manual usando la version activa.
* `/ejecuciones/<id_ejecucion>`: consola visual de ejecucion.
* `/ejecuciones/<id_ejecucion>/log`: polling JSON del log.
* `/ejecuciones/<id_ejecucion>/detener`: detencion manual con modal corporativo.
* `/ejecuciones`: historial agrupado por ano, mes y dia con filtros y paginacion.
* Validaciones previas de tarea, script, version activa, archivo fisico, `.env` requerido y ejecucion simultanea.
* Registro de `pid_proceso` en `ejecuciones`.
* Archivo de log por ejecucion bajo `logs_tareas/AAAA/MM/DD/`.
* Registro de metadatos en `logs_tareas`.
* Carga de `.env` de la version activa sin mostrar contenido.
* Estados `EN_EJECUCION`, `EXITOSA`, `ERROR` y `DETENIDA_MANUALMENTE`.
* Seed incremental `database/seeds/006_permisos_ejecuciones.sql`.
* Fase 9D: filtros por id, tarea, origen, estado, fecha, usuario y worker; resumen por estado calculado con los mismos filtros.
* Fase 11I: el historial y la consola soportan ejecuciones con `id_tarea`, `id_script` o `id_version` en `NULL`, usando snapshots y fallback historico.
* Fase 12B.1B: `/ejecuciones/<id_ejecucion>/log` tambien entrega estado, bandera final, termino, alias `fecha_hora_fin`, duracion, codigo de salida y mensaje de error para sincronizar la consola sin reload.
* Fase 12B.1B: la consola actualiza badge, texto de estado, indicador, resumen y acciones; muestra toast una sola vez al pasar a estado final.

No implementado en Fase 8:

* No existe scheduler automatico.
* No existe ejecucion programada por calendario.
* No existe API de feriados.
* No existe cola avanzada de trabajos.

## Modulo scheduler

Implementado en Fase 9A:

* `/scheduler/configuracion`: pantalla para ver y editar configuracion operativa.
* Configuracion persistida en SQL Server, no en `.env`.
* Defaults seguros: scheduler apagado y ejecucion automatica deshabilitada.
* Validaciones de intervalo entre 10 y 3600 segundos.
* Validaciones de maximo concurrentes entre 1 y 20.
* Modo mantenimiento con advertencia visual.
* Logs de sistema para cambios.
* Seed incremental `database/seeds/007_permisos_scheduler.sql`.

No implementado en Fase 9A:

* No existe worker automatico.
* No se evaluan tareas programadas.
* No se ejecutan tareas automaticas.
* No se conecta API de feriados.

Implementado en Fase 9B:

* `scheduler_worker.py`: proceso separado.
* `app/servicios/servicio_scheduler_worker.py`: ciclo del worker.
* `app/servicios/servicio_programador.py`: evaluacion de programaciones diaria, semanal, mensual y fecha especifica.
* `app/repositorios/repositorio_scheduler.py`: tareas candidatas, concurrencia y claves.
* `app/servicios/servicio_calendario.py`: consulta de feriados locales.
* Ejecuciones automaticas con version activa y motor de Fase 8.
* Anti-duplicados por `clave_programacion`.
* Listado basico `/ejecuciones`.

Implementado en Fase 11A:

* `/scheduler/panel`: panel operativo de solo lectura.
* Resumen de configuracion activa.
* Estado operativo del scheduler.
* Ultimas ejecuciones automaticas.
* Errores recientes del scheduler desde `logs_sistema`.
* Tareas programadas candidatas.
* Estado del calendario local de feriados.

Implementado en Fase 11B:

* Tabla `scheduler_worker_heartbeat`.
* Registro de inicio, ciclo, error y detencion del worker.
* Contadores de ultimo ciclo: evaluadas, ejecutadas y omitidas.
* Clasificacion visual del estado del worker segun ultimo heartbeat e intervalo configurado.
* Seccion `Estado del worker` en `/scheduler/panel`.
* `python scheduler_worker.py --once` actualiza heartbeat y registra salida controlada.

Implementado en Fase 14B.1:

* `app/servicios/servicio_logging_worker.py`: configuracion centralizada de logging estandar del worker.
* `scheduler_worker.py`: inicializa logging antes de crear la app Flask.
* `logs/worker_console.log`: fuente controlada inicial para futura consola visual.
* `StreamHandler`: mantiene salida visible en terminal.
* Handler de buffer acotado: persiste salida reciente en archivo unico, maximo 300 lineas y sin backups.
* `servicio_scheduler_worker.py`: reemplaza `print()` por logging estructurado con origen `WORKER`, `CONFIG`, `HEARTBEAT`, `CICLO`, `SCHEDULER` y `EJECUCION`.
* `servicio_worker_heartbeat.py`: registra lineas operativas de inicio/error/detencion del heartbeat sin usar `scheduler_eventos` para ruido normal ni escribir heartbeat cada ciclo en el buffer visual.

Implementado en Fase 14C:

* `app/servicios/servicio_api_worker.py`: consolida heartbeat, configuracion, eventos, ejecuciones recientes y alertas operativas en formato JSON seguro.
* `app/rutas_scheduler.py`: expone endpoints internos `/api/worker/*` reutilizando permiso `SCHEDULER_CONFIG_VER`.
* `/api/worker/consola`: lee solo el buffer visual `logs/worker_console.log`.
* `/api/worker/monitor`: entrega vista consolidada para futura consola visual sin convertir la app en terminal real.

Implementado en Fase 14D:

* `app/templates/base.html`: panel lateral `Logs` reutilizado como monitor del worker.
* `app/static/js/app.js`: polling moderado, renderizado de estado, renderizado de consola, selector de lineas y copiado seguro del registro visible.
* `app/static/css/estilos.css`: estilos de dashboard operativo compacto y bloque visual tipo terminal.
* Auto-refresh cada `5` segundos solo mientras el panel permanece abierto.
* Sin acciones destructivas ni control operacional del proceso.

Implementado en Fase 14D.1:

* Estado de la vista sin ambiguedad: `Vista actualizada`, `Actualizando...`, `Actualizacion pausada`, `No se pudo actualizar`.
* Estado principal del programador con lenguaje operativo y `Ultima senal` en lugar de `heartbeat`.
* Reubicacion de la consola reciente como soporte diagnostico.
* Resize horizontal del panel `Logs` con persistencia local en escritorio.

Implementado en Fase 11D:

* Tabla `scheduler_eventos`.
* Registro de decisiones relevantes del programador.
* Eventos de ciclo iniciado/finalizado, tarea ejecutada, tarea omitida y error controlado.
* Omisiones por feriado, ejecucion en curso, duplicado de slot, limite de concurrencia, scheduler inactivo, ejecucion automatica deshabilitada y modo mantenimiento.
* Visualizacion de eventos recientes en `/scheduler/panel` mediante la variable explicita `eventos_programador`.

Correccion posterior Fase 11D:

* La seccion `Eventos recientes del programador` queda visible debajo del estado del proceso programador.
* Se muestran fecha, tarea, tipo evento, decision, motivo, detalle y proceso.
* Si no existen registros activos se muestra `Sin eventos recientes del programador`.
* Los datos se consultan desde `scheduler_eventos`, sin depender del historial de ejecuciones.

Implementado en Fase 11D.1:

* `/scheduler/panel` muestra resumen inteligente de eventos del programador.
* Conteos del dia: eventos, ejecutadas, omitidas y errores.
* Desglose de omisiones por motivo del dia.
* Ultimos 10 eventos relevantes filtrados para evitar ruido operativo.
* Funcion `limpiar_eventos_antiguos(dias_retencion=90)` para retencion logica manual.

Criterio visual Fase 11D.1:

* Relevantes: `ERROR_SCHEDULER`, `TAREA_EJECUTADA`, `FERIADO`, `EJECUCION_EN_CURSO`, `DUPLICADO_SLOT` y `LIMITE_CONCURRENCIA`.
* Resumidos: `CICLO_INICIADO`, `CICLO_FINALIZADO` y `FUERA_DE_VENTANA` repetitivo.
* La retencion no elimina fisicamente; marca eventos antiguos como inactivos.

Implementado en Fase 11D.2:

* Ruta `/scheduler/eventos`.
* Historial filtrable de eventos activos del programador.
* Filtros por fecha, tarea, tipo evento, decision, motivo, proceso y texto.
* Paginacion server-side con opciones 10, 25, 50 y 100 registros.
* Acceso desde sidebar como `Eventos programador`.
* Acceso desde `/scheduler/panel` con boton `Ver historial de eventos`.

La diferencia operativa es:

* `/scheduler/panel` resume y prioriza eventos relevantes.
* `/scheduler/eventos` permite investigar el historial activo con filtros.

## Control de ejecuciones huerfanas

Una ejecucion huerfana es una fila en `ejecuciones` con `estado_ejecucion = EN_EJECUCION` cuyo `pid_proceso` ya no existe en el sistema operativo.

Implementado:

* `app/servicios/servicio_control_ejecuciones.py`.
* `proceso_existe(pid)`: valida existencia de PID en Windows o POSIX si es posible.
* `verificar_ejecucion(id_ejecucion)`: valida una ejecucion especifica.
* `detectar_ejecuciones_huerfanas()`: revisa ejecuciones en curso y marca huerfanas.
* Boton `Verificar ejecucion` en la consola de ejecucion para casos `EN_EJECUCION`.

Comportamiento:

* Si el PID existe, la ejecucion sigue `EN_EJECUCION`.
* Si el PID no existe, se marca `ERROR`, se completa termino/duracion y se registra mensaje claro.
* Si el estado ya es final, no se modifica.
* Si no se puede validar el PID, no se cambia el estado.
* No se matan procesos automaticamente.

No implementado en Fase 11D:

* No se implementa auditoria funcional.
* No se crean ejecuciones para tareas omitidas.
* No se crean logs de tarea para omisiones.
* No se inicia ni detiene el worker desde la app.
* No se ejecuta limpieza automatica de eventos.

## Borrado operativo seguro

Fase 11F permite usar acciones `Borrar` en entidades operativas sin perder historial asociado.

Entidades cubiertas: tareas, scripts, versiones de scripts, usuarios, clientes, categorias y tipos.

Comportamiento:

* Sin historial: se elimina fisicamente cuando las FK lo permiten.
* Con historial: se aseguran snapshots y se marca `eliminado_operativo = 1`.
* Los registros retirados no aparecen en mantenedores, selects, candidatos del programador ni metricas operativas.
* Las ejecuciones, consola, logs y eventos historicos siguen visibles con nombres legibles.

Bloqueos vigentes:

* Tarea con ejecucion `EN_EJECUCION`.
* Usuario actualmente logueado.
* Ultimo administrador activo.
* Caso donde la integridad pueda romperse sin snapshot suficiente.

Auditoria base fue implementada en Fase 12A; queda pendiente ampliar cobertura y criterios de revision en Fase 12B.

Pendientes derivados:

* Papelera operativa para consultar registros retirados. Implementado en Fase 11G.
* Restauracion controlada cuando sea seguro. Implementado en Fase 11G.
* Eliminacion permanente segura desde papelera, solo sobre tablas operativas o maestras cuando no destruya trazabilidad. Implementado en Fase 11G.
* Desacople historico para eliminacion permanente real. Implementado en Fase 11H.
* Revision integral post-borrado antes de iniciar Auditoria. Implementado en Fase 11I.

## Papelera operativa y eliminacion permanente segura

Implementado en Fase 11G.

La papelera operativa debe listar registros con `eliminado_operativo = 1` y ofrecer dos acciones:

* `Restaurar`: devuelve el registro a operacion normal si pasa validaciones, sin asumir que queda activo.
* `Eliminar permanentemente`: elimina fisicamente solo desde tablas operativas o maestras cuando no rompe integridad ni borra historia.

La eliminacion permanente debe hacer desaparecer el registro de `/papelera`, `/tareas`, `/scripts`, `/usuarios`, `/clientes`, `/categorias`, `/tipos`, selects operativos, candidatos del scheduler, paneles operativos y tablas maestras cuando las claves foraneas lo permitan.

La eliminacion permanente nunca debe borrar `ejecuciones`, `logs_tareas`, `logs_sistema`, `scheduler_eventos`, snapshots historicos, futura `auditoria_cambios` ni archivos historicos de log.

Si existen dependencias operativas no historicas, el registro debe seguir con `eliminado_operativo = 1`, permanecer en papelera y mostrarse el mensaje: `No fue posible eliminar permanentemente este registro porque aún existen dependencias operativas no históricas. El registro seguirá en papelera y oculto de la operación normal.`

Fase 11H agrega la migracion 017 y validaciones en `/papelera` para desacoplar IDs historicos anulables de `ejecuciones` y `logs_tareas` antes de borrar fisicamente tareas, scripts o versiones. El historial se conserva con snapshots y texto historico.

## Roadmap vigente

El roadmap formal se mantiene en `docs/ROADMAP.md`.

Bloques aprobados:

* Fase 11: robustez operativa interna.
* Fase 12: Auditoria.
* Fase 13: operacion y despliegue.
* Fase 14: mantenimiento avanzado.

No implementado en Fase 9B:

* No se conecta API de feriados.
* No se implementa dashboard avanzado del scheduler.
* No se implementan notificaciones.

No implementado en Fase 11A:

* No se inicia ni detiene el worker desde la app.
* No se edita configuracion desde el panel.
* No se implementan notificaciones.

## Modulo feriados

Implementado en Fase 10A:

* `/feriados`: listado con filtros por ano, mes, pais y estado.
* `/feriados/nuevo`: creacion manual de feriados.
* `/feriados/<id>/editar`: edicion de datos del feriado.
* Activacion y desactivacion con modal corporativo.
* Eliminacion fisica controlada desde el mantenedor.
* Servicio `es_feriado(fecha, pais='CL')`.
* Servicio `obtener_feriado(fecha, pais='CL')`.
* Servicio `validar_fecha_laboral(fecha, pais='CL')`.
* Scheduler omite tareas en feriado cuando `ejecutar_en_feriados = 0`.
* Scheduler permite ejecucion en feriado cuando `ejecutar_en_feriados = 1`.
* Registro en `logs_sistema` cuando una tarea automatica se omite por feriado.
* Seed incremental `database/seeds/008_permisos_feriados.sql`.
* Migracion 012 y seed 008 ejecutados y validados localmente.
* Validado bloqueo de duplicado fecha + pais activa.
* Validado `es_feriado` con feriado activo y sin feriado activo.
* Validado scheduler con `ejecutar_en_feriados = 0` y `ejecutar_en_feriados = 1`.
* Validado que la ejecucion manual no se bloquea por feriados.
* `/feriados/sincronizar`: consulta manual Nager.Date, genera vista previa y aplica cambios confirmados.
* Reglas locales de irrenunciables para Chile.
* Prioridad de feriados `MANUAL` sobre `API_NAGER`.
* Permiso `FERIADOS_SINCRONIZAR`.

No implementado en Fase 10A:

* No se implementa sincronizacion automatica.
* No se implementan notificaciones.

No implementado en Fase 10B:

* No se implementa sincronizacion automatica programada.
* No se consulta Nager.Date desde el scheduler.
* No se implementan notificaciones.

## Modulo de scripts

Implementado en Fase 7:

* `/tareas/<id_tarea>/scripts`: vista de scripts y versiones de una tarea.
* Carga de archivos `.py` con validacion de extension, tamano y ruta segura.
* Creacion automatica de v1, v2 y v3.
* v1 queda activa automaticamente si es la primera version.
* Bloqueo de v4; si existen tres versiones, se debe reemplazar una existente.
* Cambio de version activa con confirmacion.
* Desactivacion y eliminacion controlada de versiones.
* Reemplazo de version solo si no tiene historial.
* Asociacion, reemplazo y eliminacion de `.env` por version.
* Registro de eventos principales en `logs_sistema`.
* Fase 7.1: mensajes contextuales diferenciando primer script, nueva version, maximo de 3 versiones y gestion de `.env`.
* Fase 7.2: bloque superior muestra el archivo activo real desde la version activa.
* Fase 7.3: el nombre interno se mantiene en base de datos, pero no se muestra en la vista principal para evitar confusion operativa.
* Fase 7.4: se diferencia `Eliminar script completo` de `Eliminar version`; la accion superior afecta todo el contenedor de script y la accion de tabla afecta solo una version.
* Fase 7.4: la eliminacion de version activa, unica version o version con historial se bloquea con mensaje controlado y log de sistema.
* Fase 7.5: `scripts` queda como contenedor descriptivo asociado a la tarea; los nombres reales de archivos `.py` viven en `scripts_versiones`.
* Fase 7.5: al crear el primer script, `scripts.nombre_script` usa `Script de {nombre_tarea}` y no el nombre del archivo cargado.

No implementado en Fase 7:

* No se ejecutan scripts.
* No se leen secretos de `.env`.
* No existe scheduler real.
* La consola de ejecucion se implementa recien en Fase 8.

## Modulo de tareas

Implementado en Fase 6:

* `/tareas`: listar y filtrar por estado, cliente, categoria, tipo, tipo de programacion y busqueda.
* `/tareas/nueva`: crear tarea con datos base y programacion.
* `/tareas/<id>/editar`: editar tarea y reemplazar la programacion activa por una nueva.
* Activar y desactivar tareas.
* Eliminar fisicamente solo si no existen dependencias en scripts, ejecuciones ni logs.
* Registrar acciones principales en `logs_sistema`.
* Programacion declarativa `MANUAL`, `DIARIA`, `SEMANAL`, `MENSUAL`, `FECHA_ESPECIFICA`.
* Modos `UNA_VEZ` e `INTERVALO`.
* Marca `ejecutar_en_feriados`, integrada al calendario local desde Fase 10A.
* Fase 6.1: resumen de confirmacion antes de crear o editar, usando datos actuales del formulario.
* Fase 6.1: validacion frontend previa para evitar confirmar programaciones incompletas.
* Fase 6.2: deteccion de cambios reales antes de guardar ediciones.
* Fase 6.2: si no hay cambios, no se envia formulario desde frontend y el backend evita `UPDATE` como respaldo.
* Fase 15E: `/tareas/<id>/editar` incluye bloque minimo `Notificaciones y evidencia` para configurar envio futuro de evidencia, asunto, adjuntos, alerta interna y destinatarios `EVIDENCIA`/`ALERTA` mediante la API JSON creada en Fase 15D.

No implementado en Fase 6:

* No se ejecutan scripts.
* No existe scheduler real.
* No existe carga/versionamiento funcional de scripts.
* No existe API de feriados.

No implementado en Fase 15E:

* No se envia correo real.
* No se implementa Microsoft Graph.
* No se captura `stdout`.
* No se valida estaticamente el script compatible con evidencia.

## Modulo Mail Automatico Graph

Implementado en Fase 15F:

* `/configuracion/mail-graph`: pantalla administrativa minima para origen global de correo automatico.
* `/api/configuracion/mail-graph`: API JSON para consultar y guardar configuracion global no sensible.
* Tabla propuesta en migracion incremental `020_crear_configuracion_mail_graph.sql`.
* Configura `activo`, `tenant_id`, `client_id`, `graph_scope`, `send_mail_user`, `save_to_sent_items` y destinatarios globales de alerta.
* Muestra estado `Client Secret configurado: Si/No`, sin revelar el valor.
* Reutiliza permisos administrativos `SCHEDULER_CONFIG_VER` y `SCHEDULER_CONFIG_EDITAR` en esta fase para evitar seed nuevo.
* Cierre validado: migracion 020 ejecutada manualmente en `APP_SCHEDULER_QA` y pantalla `/configuracion/mail-graph` cargando correctamente con configuracion inicial inactiva.
* Ajuste Fase 15F: la configuracion global se actualiza sobre la misma fila; no se acumula una fila nueva por cada guardado.
* Diagnostico preparado: `database/diagnostics/005_diagnostico_configuracion_mail_graph.sql` revisa filas existentes y deja propuesta segura de consolidacion sin ejecutar cambios destructivos.

No implementado en Fase 15F:

* No se envia correo real.
* No se obtiene token Graph.
* No se usa MSAL.
* No se hace llamada externa a Microsoft Graph.
* No se guarda `GRAPH_CLIENT_SECRET`, tokens ni passwords en base de datos.

## Modulo de evidencias stdout

Implementado en Fase 15G:

* Servicio `app/servicios/servicio_evidencias.py`.
* Validacion estatica de script activo por tarea.
* Endpoint `GET /api/tareas/<id>/evidencia/validar-soporte`.
* Integracion con configuracion de notificaciones para bloquear `enviar_evidencia=true` si el script no cumple contrato.
* Integracion visual en `/tareas/<id>/editar` dentro del bloque `Notificaciones y evidencia`.

Validaciones:

* declaracion `APP_SCHEDULER_EVIDENCIA = True`;
* version `APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"`;
* delimitador de inicio como string real del codigo;
* delimitador de fin como string real del codigo;
* ruta `.py` segura bajo `RUTA_BASE_SCRIPTS`.

Ajustado en Fase 15H.2:

* La validacion estatica ignora delimitadores escritos solo como comentarios.
* Se aceptan delimitadores en `print(...)`, constantes string o helpers, siempre que existan como strings reales del codigo.
* No se ejecuta, importa, evalua ni interpreta dinamicamente el script.
* La UI aclara que los delimitadores deben imprimirse durante la ejecucion para que la captura por `stdout` funcione.
* La ayuda de destinatarios aclara el significado operativo de `TO`, `CC` y `BCC`.

No implementado en Fase 15G:

* No se ejecutan scripts.
* No se importan scripts.
* No se captura `stdout`.
* No se envia correo.
* No se implementa Graph.

Implementado en Fase 15H:

* Captura controlada del bloque de evidencia emitido por `stdout` durante la ejecucion.
* Parseo JSON y validacion de contrato minimo.
* Registro minimo en `dbo.evidencias_ejecucion` mediante upsert por `id_ejecucion`.
* Hash SHA-256 de evidencia normalizada, sin guardar JSON completo.
* Integracion comun para ejecucion manual y automatica desde `servicio_ejecuciones.py`.

Ajustado en Fase 15H.3:

* El log visible de ejecucion conserva stdout/stderr completo, incluyendo delimitadores y JSON emitido por el script.
* La captura de evidencia toma una copia en memoria para validar y persistir solo hash/trazabilidad minima.
* La omision del JSON bruto queda reservada para el futuro correo/notificacion, no para la consola operativa.

No implementado en Fase 15H:

* No se envia correo.
* No se llama Microsoft Graph.
* No se implementa alerta interna por correo.
* No se modifica `scheduler_worker.py`.

## Mantenedores base

Implementado en Fase 5:

* `/clientes`: listar, filtrar, crear, editar, activar y desactivar clientes.
* `/categorias`: listar, filtrar, crear, editar, activar y desactivar categorias.
* `/tipos`: listar, filtrar, crear, editar, activar y desactivar tipos.
* Filtros por estado y busqueda general.
* Contador de resultados.
* Modal corporativo para crear, editar y cambiar estado.
* Validacion de nombre obligatorio y duplicados por nombre normalizado.
* Borrado operativo seguro desde Fase 11F si el registro tiene dependencias en `tareas`.
* Logs en `logs_sistema` para creacion, edicion, activacion y desactivacion.
* Logs en `logs_sistema` para eliminacion fisica o retiro operativo.

## Modulo de usuarios

Implementado en Fase 4:

* Login hibrido: primero `.env`, luego tabla `usuarios`.
* Usuario `.env` con rol de sesion `SUPER_ADMIN_ENV`.
* Usuarios de base de datos con roles y permisos desde tablas de seguridad.
* Pantalla `/usuarios` para listar, filtrar, crear, editar, activar, desactivar y borrar usuarios de la operacion normal.
* Filtros por estado, rol y busqueda general.
* Confirmacion antes de activar o desactivar usuarios.
* Advertencias visuales al cambiar rol o contrasena.
* Asignacion de un rol activo por usuario desde el formulario inicial.
* Contrasenas con hash seguro.
* Borrado operativo de usuarios con historial, sin permitir borrar el usuario actual ni el ultimo administrador activo.
* Eventos principales registrados en `logs_sistema`.

## Impacto del versionamiento de scripts

* Gestion de scripts debe permitir cargar version 1, 2 o 3.
* Gestion de scripts debe impedir una cuarta version directa.
* Gestion de scripts debe permitir reemplazar una version existente con auditoria.
* Gestion de scripts debe manejar versiones por estado: `ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`.
* Gestion de scripts usa borrado operativo con snapshots cuando existe historial.
* Ejecucion manual debe permitir elegir version disponible.
* Ejecucion automatica debe usar la version activa.
* Logs y auditoria deben permitir reconstruir que version se ejecuto.

## Modulo de base de datos y release SQL

Implementado en Fase 13A:

* `database/release/` contiene instalacion SQL limpia desde cero para `APP_SCHEDULER_QA`.
* `002_schema_final.sql` consolida el modelo vigente de seguridad, mantenedores, tareas, scripts, ejecuciones, logs, scheduler, feriados, papelera, snapshots y auditoria.
* Seeds consolidados cargan datos base sin usuarios reales ni credenciales.
* `099_validacion_instalacion.sql` valida estructura y datos base con consultas de solo lectura.
* `database/migrations/` y `database/seeds/` permanecen como historial de desarrollo incremental.

No implementado en Fase 13A:

* No se ejecutan scripts SQL desde Codex.
* No se crean usuarios reales.
* No se cambia conexion Flask ni `.env`.
* No se avanza a scripts operativos, QA Linux, produccion, Docker ni servicios.

## Modulo de eventos del programador

Desde Fase 13A.1:

* `scheduler_eventos` queda orientada a hechos relevantes, no a registrar cada ciclo normal sin novedades.
* No se persisten por defecto `CICLO_INICIADO`, `CICLO_FINALIZADO` ni omisiones por `FUERA_DE_VENTANA`.
* `/scheduler/eventos` permite limpiar eventos informativos antiguos con permiso `SCHEDULER_CONFIG_EDITAR`.
* La limpieza solo elimina `CICLO_INICIADO`, `CICLO_FINALIZADO` y `TAREA_OMITIDA/FUERA_DE_VENTANA` anteriores al periodo seleccionado.
* Eventos importantes como ejecuciones, errores, feriados, duplicados y limites de concurrencia se conservan por defecto.

Desde Fase 13A.1B:

* La limpieza permite seleccionar categorias especificas.
* El backend usa whitelist `CATEGORIAS_LIMPIEZA`; no acepta tipos libres del navegador.
* Existe previsualizacion con total y detalle por categoria.
* La eliminacion recalcula el filtro en backend antes de borrar.
* Se mantiene permiso `SCHEDULER_CONFIG_EDITAR`; no hay seed ni migracion nueva.
