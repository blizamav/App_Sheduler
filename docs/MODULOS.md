# Modulos

## Implementados

* Login inicial desde `.env`.
* Panel principal base.
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

## Modulos pendientes

* Dashboard avanzado del scheduler.
* Logs de sistema completos.
* Auditoria.
* Configuracion.
* Sincronizacion automatica programada de feriados.
* Dashboard ejecutivo.
* Notificaciones.

## Definicion Fase 4.3

Antes de implementar tareas, scripts y scheduler se definio:

* Cada version de script podra indicar si requiere `.env`.
* Los `.env` de scripts viviran en `env_scripts/`, separados del codigo en `scripts/`.
* La base guardara solo rutas de `.env`, no secretos.
* Las ejecuciones registraran `pid_proceso` y datos de detencion manual.
* La interfaz futura debera permitir detener ejecuciones solo si estan `EN_EJECUCION`.
* Toda detencion debe confirmarse con modal corporativo y registrarse en logs.

## Estado de implementacion

La aplicacion esta en Fase 11A: usuarios, roles, permisos, mantenedores base, tareas, scripts, ejecucion manual, configuracion scheduler, worker automatico separado, historial de ejecuciones, calendario local de feriados, sincronizacion controlada desde Nager.Date y panel operativo del scheduler. Aun no existe sincronizacion automatica programada, control de worker desde la app ni panel avanzado de auditoria.

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

No implementado en Fase 6:

* No se ejecutan scripts.
* No existe scheduler real.
* No existe carga/versionamiento funcional de scripts.
* No existe API de feriados.

## Mantenedores base

Implementado en Fase 5:

* `/clientes`: listar, filtrar, crear, editar, activar y desactivar clientes.
* `/categorias`: listar, filtrar, crear, editar, activar y desactivar categorias.
* `/tipos`: listar, filtrar, crear, editar, activar y desactivar tipos.
* Filtros por estado y busqueda general.
* Contador de resultados.
* Modal corporativo para crear, editar y cambiar estado.
* Validacion de nombre obligatorio y duplicados por nombre normalizado.
* Eliminacion fisica controlada solo si el registro no tiene dependencias en `tareas`.
* Logs en `logs_sistema` para creacion, edicion, activacion y desactivacion.
* Logs en `logs_sistema` para eliminacion definitiva e intento bloqueado por dependencias.

## Modulo de usuarios

Implementado en Fase 4:

* Login hibrido: primero `.env`, luego tabla `usuarios`.
* Usuario `.env` con rol de sesion `SUPER_ADMIN_ENV`.
* Usuarios de base de datos con roles y permisos desde tablas de seguridad.
* Pantalla `/usuarios` para listar, filtrar, crear, editar, activar y desactivar usuarios.
* Filtros por estado, rol y busqueda general.
* Confirmacion antes de activar o desactivar usuarios.
* Advertencias visuales al cambiar rol o contrasena.
* Asignacion de un rol activo por usuario desde el formulario inicial.
* Contrasenas con hash seguro.
* Sin eliminacion fisica de usuarios.
* Eventos principales registrados en `logs_sistema`.

## Impacto del versionamiento de scripts

* Gestion de scripts debe permitir cargar version 1, 2 o 3.
* Gestion de scripts debe impedir una cuarta version directa.
* Gestion de scripts debe permitir reemplazar una version existente con auditoria.
* Gestion de scripts debe manejar versiones por estado: `ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`.
* Gestion de scripts no debe permitir eliminacion fisica desde la app en la primera version.
* Ejecucion manual debe permitir elegir version disponible.
* Ejecucion automatica debe usar la version activa.
* Logs y auditoria deben permitir reconstruir que version se ejecuto.
