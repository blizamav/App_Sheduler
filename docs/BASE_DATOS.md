# Base de datos

## Estado

Base `APP_SCHEDULER_QA` creada y validada manualmente en SQL Server local. Migraciones 001-010 y seeds 001-007 ejecutados localmente. La migracion 012 y el seed 008 de Fase 10A fueron ejecutados y validados localmente para feriados. Fase 10B agrega migracion 013 y seeds 009/010, pendientes de ejecucion manual en SSMS. Fase 11B agrega migracion 014 para heartbeat del worker, pendiente de ejecucion manual. Fase 11D agrega migracion 015 para eventos y omisiones del programador, pendiente de ejecucion manual. Fase 11F agrega migracion 016 para borrado operativo seguro y snapshots, pendiente de ejecucion manual. Fase 11G agrega seed 011 para permisos de papelera, pendiente de ejecucion manual. Fase 11H agrega migracion 017 para desacople historico, pendiente de ejecucion manual.

Roadmap vigente: `docs/ROADMAP.md`.

## Base objetivo

* Motor: SQL Server.
* Base: `APP_SCHEDULER_QA`.
* Variable de entorno: `DB_DATABASE`.
* Servidor, usuario, clave y driver deben venir desde `.env`.

## Conexion desde Flask

Fase 3D agrega conexion inicial desde Flask mediante `pyodbc`, sin CRUD ni repositorios funcionales aun.

Variables requeridas en `.env`:

* `DB_SERVER`
* `DB_DATABASE`
* `DB_USER`
* `DB_PASSWORD`
* `DB_DRIVER`

El modulo `app/database/conexion.py` construye la cadena ODBC y expone `probar_conexion_bd()`, que ejecuta `SELECT 1`, cierra la conexion y retorna estado `OK` o `ERROR` sin exponer credenciales.

La ruta `/diagnostico/bd` solo esta disponible en `APP_ENV=LOCAL` o `APP_ENV=QA`.

## Scripts SQL versionados

Estructura creada:

```text
database/
  migrations/
    001_crear_base_datos.sql
    002_crear_catalogos.sql
    003_crear_tablas_seguridad.sql
    004_crear_tablas_negocio.sql
    005_crear_tablas_ejecucion_logs.sql
    006_crear_indices.sql
    007_agregar_control_ejecucion_y_env_scripts.sql
    008_ajustar_tareas_y_programaciones_base.sql
    009_corregir_nombre_script_contenedor.sql
    010_crear_configuracion_scheduler.sql
    011_agregar_control_scheduler_ejecuciones.sql
    012_crear_calendario_feriados.sql
    013_crear_reglas_feriados_irrenunciables.sql
    014_crear_scheduler_worker_heartbeat.sql
    015_crear_eventos_programador.sql
    016_agregar_snapshots_historial_borrado_operativo.sql
    017_desacople_historico_papelera.sql
  seeds/
    001_datos_iniciales_catalogos.sql
    002_roles_permisos_iniciales.sql
    006_permisos_ejecuciones.sql
    007_permisos_scheduler.sql
    008_permisos_feriados.sql
    009_reglas_irrenunciables_chile.sql
    010_permisos_sincronizacion_feriados.sql
    011_permisos_papelera.sql
```

Orden correcto de ejecucion manual en SQL Server Management Studio:

1. `database/migrations/001_crear_base_datos.sql`
2. `database/migrations/002_crear_catalogos.sql`
3. `database/migrations/003_crear_tablas_seguridad.sql`
4. `database/migrations/004_crear_tablas_negocio.sql`
5. `database/migrations/005_crear_tablas_ejecucion_logs.sql`
6. `database/migrations/006_crear_indices.sql`
7. `database/seeds/001_datos_iniciales_catalogos.sql`
8. `database/seeds/002_roles_permisos_iniciales.sql`
9. `database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql`
10. `database/seeds/003_permisos_mantenedores.sql`
11. `database/migrations/008_ajustar_tareas_y_programaciones_base.sql`
12. `database/seeds/004_permisos_tareas.sql`
13. `database/seeds/005_permisos_scripts.sql`
14. `database/migrations/009_corregir_nombre_script_contenedor.sql`
15. `database/seeds/006_permisos_ejecuciones.sql`
16. `database/migrations/010_crear_configuracion_scheduler.sql`
17. `database/seeds/007_permisos_scheduler.sql`
18. `database/migrations/011_agregar_control_scheduler_ejecuciones.sql`
19. `database/migrations/012_crear_calendario_feriados.sql`
20. `database/seeds/008_permisos_feriados.sql`
21. `database/migrations/013_crear_reglas_feriados_irrenunciables.sql`
22. `database/seeds/009_reglas_irrenunciables_chile.sql`
23. `database/seeds/010_permisos_sincronizacion_feriados.sql`
24. `database/migrations/014_crear_scheduler_worker_heartbeat.sql`
25. `database/migrations/015_crear_eventos_programador.sql`
26. `database/migrations/016_agregar_snapshots_historial_borrado_operativo.sql`
27. `database/seeds/011_permisos_papelera.sql`
28. `database/migrations/017_desacople_historico_papelera.sql`

Resumen por script:

* `001_crear_base_datos.sql`: crea `APP_SCHEDULER_QA` si no existe.
* `002_crear_catalogos.sql`: crea catalogos de estados, tipos y niveles.
* `003_crear_tablas_seguridad.sql`: crea usuarios, roles, permisos, usuarios_roles y roles_permisos. No crea usuario inicial.
* `004_crear_tablas_negocio.sql`: crea clientes, categorias, tipos, tareas, programaciones, scripts, scripts_versiones y configuracion_sistema.
* `005_crear_tablas_ejecucion_logs.sql`: crea ejecuciones, logs_tareas, logs_sistema y auditoria_cambios.
* `006_crear_indices.sql`: crea indices recomendados, indice unico filtrado para version activa y FK diferida `scripts.id_version_activa`.
* `007_agregar_control_ejecucion_y_env_scripts.sql`: agrega soporte propuesto para `.env` por version de script y trazabilidad de detencion manual de ejecuciones.
* `008_ajustar_tareas_y_programaciones_base.sql`: ajusta `tareas` y `programaciones` para Fase 6.
* `009_corregir_nombre_script_contenedor.sql`: corrige registros existentes donde `scripts.nombre_script` quedo como nombre de archivo `.py`; no toca versiones, rutas ni archivos. Ejecutada localmente sin errores; afecto 0 filas porque no existian registros antiguos que corregir.
* `010_crear_configuracion_scheduler.sql`: crea `configuracion_scheduler` con defaults seguros para Fase 9A; no inicia worker ni ejecuciones automaticas.
* `011_agregar_control_scheduler_ejecuciones.sql`: agrega trazabilidad de ejecuciones automaticas y clave anti-duplicados para Fase 9B.
* `012_crear_calendario_feriados.sql`: crea tabla local `feriados` para Fase 10A; ejecutada y validada localmente; no conecta API externa.
* `013_crear_reglas_feriados_irrenunciables.sql`: crea reglas locales de irrenunciables y ajusta `CK_feriados_origen` para permitir `API_NAGER`.
* `014_crear_scheduler_worker_heartbeat.sql`: crea tabla `scheduler_worker_heartbeat` para registrar senal de vida del worker; no inicia ni detiene procesos desde la app.
* `015_crear_eventos_programador.sql`: crea tabla `scheduler_eventos` para registrar decisiones, omisiones y errores del programador; no crea ejecuciones ni logs de tarea.
* `016_agregar_snapshots_historial_borrado_operativo.sql`: agrega snapshots historicos y campos de borrado operativo seguro para retirar registros sin perder historial.
* `017_desacople_historico_papelera.sql`: elimina FKs historicas desde `ejecuciones` y `logs_tareas`, vuelve anulables sus IDs historicos y conserva snapshots para permitir eliminacion permanente real desde papelera sin borrar historia.
* `001_datos_iniciales_catalogos.sql`: inserta estados y catalogos base con `MERGE`.
* `002_roles_permisos_iniciales.sql`: inserta roles y permisos base con `MERGE`; no crea usuarios.
* `003_permisos_mantenedores.sql`: inserta permisos incrementales para clientes, categorias y tipos, y los asigna a roles base.
* `004_permisos_tareas.sql`: inserta permisos incrementales para tareas y los asigna a roles base.
* `005_permisos_scripts.sql`: inserta permisos incrementales para gestion de scripts, versiones y env.
* `006_permisos_ejecuciones.sql`: inserta permisos incrementales para ejecucion manual, consola, log y detencion.
* `007_permisos_scheduler.sql`: inserta permisos incrementales para ver y editar configuracion operativa del scheduler.
* `008_permisos_feriados.sql`: inserta permisos incrementales para ver, crear, editar, activar/desactivar y eliminar feriados; ejecutado y validado localmente.
* `009_reglas_irrenunciables_chile.sql`: carga reglas iniciales Chile para 01/01, 01/05, 18/09, 19/09 y 25/12.
* `010_permisos_sincronizacion_feriados.sql`: inserta permiso `FERIADOS_SINCRONIZAR`.
* `011_permisos_papelera.sql`: inserta permisos `PAPELERA_VER`, `PAPELERA_RESTAURAR` y `PAPELERA_ELIMINAR_PERMANENTE`. Debe ejecutarse manualmente en SSMS.

## Fase 11B - Heartbeat worker scheduler

Se crea migracion incremental `014_crear_scheduler_worker_heartbeat.sql`.

Tabla: `scheduler_worker_heartbeat`.

Objetivo: mantener un registro por worker activo y actualizarlo en cada ciclo del proceso `scheduler_worker.py`.

Campos principales:

* `nombre_worker`.
* `estado`.
* `fecha_inicio`.
* `fecha_ultimo_heartbeat`.
* `fecha_ultimo_ciclo`.
* `resultado_ultimo_ciclo`.
* `ultimo_error`.
* `ciclos_ejecutados`.
* `tareas_evaluadas_ultimo_ciclo`.
* `tareas_ejecutadas_ultimo_ciclo`.
* `tareas_omitidas_ultimo_ciclo`.
* `pid_proceso`.
* `host`.
* `version_app`.
* `activo`.

Estados permitidos:

* `INICIADO`.
* `ACTIVO`.
* `EN_CICLO`.
* `ESPERANDO`.
* `ERROR`.
* `DETENIDO`.

Restricciones e indices:

* `CHECK` para estados permitidos.
* `CHECK` para contadores no negativos.
* Indice unico filtrado por `nombre_worker` cuando `activo = 1`.
* Indices por `nombre_worker`, `fecha_ultimo_heartbeat` y `estado`.

Regla operativa: no se crea un registro por ciclo. El worker actualiza el mismo registro activo para evitar crecimiento innecesario.

## Fase 11D - Eventos del programador

Se crea migracion incremental `015_crear_eventos_programador.sql`.

Tabla: `scheduler_eventos`.

Objetivo: registrar decisiones operativas del programador que no deben confundirse con ejecuciones reales ni con auditoria funcional.

Casos registrados:

* Ciclo iniciado.
* Ciclo finalizado.
* Tarea enviada a ejecucion automatica.
* Tarea omitida por feriado.
* Tarea omitida por ejecucion ya en curso.
* Tarea omitida por duplicado de `clave_programacion`.
* Tarea omitida por limite de concurrencia.
* Tarea omitida por scheduler inactivo, ejecucion automatica deshabilitada o modo mantenimiento.
* Error controlado del programador.

Campos principales:

* `fecha_evento`.
* `nombre_worker`.
* `id_tarea`.
* `nombre_tarea`.
* `id_programacion`.
* `fecha_programada`.
* `clave_programacion`.
* `tipo_evento`.
* `decision`.
* `motivo`.
* `detalle`.
* `estado_scheduler`.
* `ejecutar_en_feriados`.
* `es_feriado`.
* `nombre_feriado`.
* `origen`.

Restricciones:

* `tipo_evento`: `CICLO_INICIADO`, `CICLO_FINALIZADO`, `TAREA_EVALUADA`, `TAREA_EJECUTADA`, `TAREA_OMITIDA`, `ERROR_SCHEDULER`.
* `decision`: `EJECUTAR`, `OMITIR`, `ERROR`, `INFO`.
* `origen`: `SCHEDULER`.

Decisiones:

* No se crean registros en `ejecuciones` cuando una tarea se omite.
* No se generan `logs_tareas` para omisiones, porque no existio ejecucion real.
* No se usa `logs_sistema` para cada omision operativa del programador.
* `scheduler_worker_heartbeat` sigue separado y no se registra como evento por cada senal.
* La tabla guarda snapshot de nombre de tarea, worker, clave y motivo para conservar trazabilidad aun si datos descriptivos cambian despues.
* No se agregan claves foraneas para no alterar reglas existentes de eliminacion controlada ni bloquear mantenedores por eventos operativos.

Fase 11D.1 agrega consultas de resumen sobre esta misma tabla, sin crear migracion nueva:

* Resumen de eventos del dia actual.
* Omisiones del dia agrupadas por `motivo`.
* Ultimos eventos relevantes activos, limitados a 10 registros.
* Retencion logica mediante `limpiar_eventos_antiguos(dias_retencion=90)`, que actualiza `activo = 0`.

La retencion no elimina fisicamente registros y no se ejecuta automaticamente en esta fase.

Fase 11D.2 agrega consulta paginada sobre la misma tabla:

* Condicion fija `activo = 1`.
* Filtros opcionales por fecha, tarea, tipo evento, decision, motivo, worker y texto.
* Orden `fecha_evento DESC, id_evento DESC`.
* Paginacion SQL Server mediante `OFFSET / FETCH`.

No se crea migracion nueva porque la tabla `scheduler_eventos` ya contiene los campos necesarios.

## Fase 11F - Borrado operativo seguro

La migracion `016_agregar_snapshots_historial_borrado_operativo.sql` permite borrar registros desde la operacion normal sin destruir historia. Si el registro no tiene historial, la app puede eliminar fisicamente. Si tiene historial, se usa retiro operativo mediante `eliminado_operativo = 1`.

Campos de control agregados a `tareas`, `scripts`, `scripts_versiones`, `usuarios`, `clientes`, `categorias` y `tipos`:

* `eliminado_operativo bit not null default 0`
* `fecha_eliminado_operativo datetime2(0) null`
* `usuario_eliminado_operativo nvarchar(100) null`
* `motivo_eliminado_operativo nvarchar(500) null`

Snapshots agregados a `ejecuciones`:

* `id_tarea_original`
* `nombre_tarea_snapshot`
* `cliente_snapshot`
* `categoria_snapshot`
* `tipo_snapshot`
* `nombre_script_snapshot`
* `nombre_archivo_snapshot`
* `version_script_snapshot`
* `usuario_ejecucion_snapshot`

Snapshots agregados a `scheduler_eventos`:

* `id_tarea_original`
* `nombre_tarea_snapshot`
* `cliente_snapshot`
* `categoria_snapshot`
* `tipo_snapshot`

La migracion rellena snapshots existentes con JOIN hacia `tareas`, `clientes`, `categorias`, `tipos`, `scripts` y `scripts_versiones`. No elimina filas historicas, no modifica `.env` y debe ejecutarse manualmente en SQL Server.

Las vistas historicas deben consultar `COALESCE(snapshot, tabla_maestra)` para soportar registros maestros retirados de la operacion normal.

Reglas:

* `eliminado_operativo = 1` no elimina fisicamente la fila.
* El registro retirado desaparece de la operacion normal.
* Los snapshots conservan historia legible.
* Papelera operativa implementada en Fase 11G para consultar, restaurar y eliminar permanentemente registros retirados bajo reglas seguras.
* Falta purga controlada para eliminacion fisica posterior bajo reglas estrictas.

## Fase 11G - Papelera y eliminacion permanente segura

Implementado funcionalmente en Fase 11G.

La papelera operativa debe trabajar sobre registros con `eliminado_operativo = 1`.

Acciones permitidas:

* `Restaurar`: revierte `eliminado_operativo` si pasa validaciones de integridad y permisos.
* `Eliminar permanentemente`: ejecuta `DELETE` fisico solo sobre la tabla operativa o maestra del registro, cuando no existen dependencias operativas no historicas y las claves foraneas lo permiten.

Al eliminar permanentemente:

* El registro deja de aparecer en `/papelera`, mantenedores, selects, candidatos del scheduler y paneles operativos.
* No se debe ejecutar `DELETE CASCADE` destructivo.
* No se deben borrar `ejecuciones`, `logs_tareas`, `logs_sistema`, `scheduler_eventos`, snapshots historicos, futura `auditoria_cambios` ni archivos historicos de log.
* La historia debe seguir legible mediante snapshots o texto historico.

Si no es seguro eliminar fisicamente:

* No se fuerza el `DELETE`.
* El registro mantiene `eliminado_operativo = 1`.
* El registro sigue visible en `/papelera` y oculto de la operacion normal.

## Fase 11H - Desacople historico de papelera

La migracion `017_desacople_historico_papelera.sql` separa las referencias historicas de las relaciones operativas vivas.

Cambios:

* Rellena snapshots faltantes en `ejecuciones` y `scheduler_eventos` antes del cambio estructural.
* Elimina las FKs historicas `FK_ejecuciones_tareas`, `FK_ejecuciones_scripts`, `FK_ejecuciones_scripts_versiones` y `FK_logs_tareas_tareas`.
* Cambia `ejecuciones.id_tarea`, `ejecuciones.id_script`, `ejecuciones.id_version` y `logs_tareas.id_tarea` a `NULL`.
* Mantiene `logs_tareas.id_ejecucion` apuntando a `ejecuciones`.
* No borra filas historicas ni archivos historicos.

La app valida que esta migracion exista antes de permitir eliminacion permanente real de `tareas`, `scripts` o `scripts_versiones` desde `/papelera`.

## Auditoria pendiente

La tabla `auditoria_cambios` existe en el modelo inicial, pero el modulo funcional de Auditoria sigue pendiente para Fase 12.

Distincion:

* `scheduler_eventos` registra decisiones automaticas del programador.
* `ejecuciones` registra intentos reales de ejecutar scripts.
* `logs_sistema` registra eventos operativos basicos.
* `auditoria_cambios` debe registrar acciones humanas criticas en una fase posterior.

## Fase 7 - Scripts y versiones

No se crea migracion nueva porque el modelo vigente ya contiene:

* `scripts.id_tarea`
* `scripts.id_version_activa`
* `scripts_versiones.numero_version`
* `scripts_versiones.ruta_fisica`
* `scripts_versiones.ruta_relativa`
* `scripts_versiones.hash_archivo`
* `scripts_versiones.estado_version`
* `scripts_versiones.requiere_env`
* `scripts_versiones.ruta_env_fisica`
* `scripts_versiones.ruta_env_relativa`

Se agrega solo seed incremental `005_permisos_scripts.sql`, que debe ejecutarse manualmente para usuarios de base de datos.

## Fase 8 - Ejecucion manual

No se crea migracion nueva para Fase 8 porque el modelo vigente ya contiene:

* `ejecuciones.pid_proceso`.
* `ejecuciones.usuario_detencion`.
* `ejecuciones.fecha_hora_detencion`.
* `ejecuciones.motivo_detencion`.
* `ejecuciones.fue_detencion_forzada`.
* `logs_tareas` para registrar metadatos del archivo de log por ejecucion.

Se agrega seed incremental `006_permisos_ejecuciones.sql`, que debe ejecutarse manualmente para usuarios de base de datos.

Permisos:

* `EJECUCIONES_VER`.
* `EJECUCIONES_EJECUTAR`.
* `EJECUCIONES_DETENER`.
* `EJECUCIONES_LOG_VER`.

La ejecucion manual registra `id_tarea`, `id_script`, `id_version`, estado, fechas, usuario, PID y codigo de salida. El archivo de log se registra en `logs_tareas` con ruta fisica y relativa.

## Fase 9A - Configuracion scheduler

Se crea migracion incremental `010_crear_configuracion_scheduler.sql`.

Tabla: `configuracion_scheduler`.

Objetivo: almacenar configuracion operativa del scheduler en SQL Server para que el worker futuro no dependa de `.env`.

Campos principales:

* `scheduler_activo bit`.
* `intervalo_revision_segundos int`.
* `max_ejecuciones_concurrentes int`.
* `permitir_ejecucion_automatica bit`.
* `modo_mantenimiento bit`.
* `nombre_worker_principal varchar(100)`.
* `descripcion varchar(500)`.
* `usuario_actualizacion nvarchar(100)`.
* `activo bit`.

Defaults seguros:

* Scheduler apagado.
* Ejecucion automatica no permitida.
* Intervalo 60 segundos.
* Maximo 3 ejecuciones concurrentes.
* Modo mantenimiento inactivo.
* Worker `worker_default`.

Restricciones:

* `intervalo_revision_segundos BETWEEN 10 AND 3600`.
* `max_ejecuciones_concurrentes BETWEEN 1 AND 20`.
* Indice unico filtrado para una sola configuracion activa.

Seed: `007_permisos_scheduler.sql` con `SCHEDULER_CONFIG_VER` y `SCHEDULER_CONFIG_EDITAR`.

Validacion local:

* `010_crear_configuracion_scheduler.sql` fue ejecutado correctamente en SQL Server local.
* `007_permisos_scheduler.sql` fue ejecutado correctamente en SQL Server local.
* La tabla `configuracion_scheduler` existe y contiene un registro inicial activo.
* Los defaults seguros quedaron validados: scheduler apagado, ejecucion automatica deshabilitada, intervalo 60, maximo concurrentes 3 y mantenimiento desactivado.
* Los permisos `SCHEDULER_CONFIG_VER` y `SCHEDULER_CONFIG_EDITAR` fueron insertados.
* La configuracion se edita desde `/scheduler/configuracion` y los cambios se registran en `logs_sistema`.
* Esta validacion no habilita worker automatico ni ejecuciones automaticas.

## Fase 9B - Worker automatico

Se crea migracion incremental `011_agregar_control_scheduler_ejecuciones.sql`.

Campos agregados a `ejecuciones` si no existen:

* `fecha_programada datetime2(0) NULL`.
* `clave_programacion varchar(200) NULL`.
* `nombre_worker varchar(100) NULL`.

Tambien valida `origen_ejecucion` si fuera necesario para mantener valores `MANUAL` y `AUTOMATICA`.

Indices:

* `UX_ejecuciones_clave_programacion_automatica`: indice unico filtrado sobre `clave_programacion` cuando `origen_ejecucion = 'AUTOMATICA'` y la clave no es nula.
* `IX_ejecuciones_origen_estado`: apoyo para conteo de automaticas `EN_EJECUCION`.

Reglas:

* Cada ejecucion automatica debe guardar `fecha_programada`.
* Cada ejecucion automatica debe guardar `clave_programacion`.
* La clave evita duplicar un mismo slot.
* El worker registra `nombre_worker`.
* La consola y logs de Fase 8 siguen asociados por `id_ejecucion`.
* La migracion debe ejecutarse manualmente en SSMS; no se ejecuta automaticamente desde Flask ni desde Codex.

## Fase 10A - Feriados locales

Se crea migracion incremental `012_crear_calendario_feriados.sql`.

Tabla: `feriados`.

Objetivo: mantener calendario local de feriados como fuente de verdad del scheduler. No depende de API externa en tiempo real.

Campos principales:

* `id_feriado int identity primary key`.
* `fecha date`.
* `nombre varchar(200)`.
* `tipo varchar(50)`.
* `pais varchar(10)` con default `CL`.
* `irrenunciable bit`.
* `activo bit`.
* `origen varchar(50)` con default `MANUAL`.
* `observacion varchar(500)`.
* `fecha_creacion`, `fecha_actualizacion`.
* `usuario_creacion`, `usuario_actualizacion` como texto de usuario de sesion.

Restricciones e indices:

* `UX_feriados_fecha_pais_activo`: no permite duplicar fecha + pais activa.
* `IX_feriados_fecha`.
* `IX_feriados_pais`.
* `IX_feriados_activo`.

Seed: `008_permisos_feriados.sql`.

Permisos:

* `FERIADOS_VER`.
* `FERIADOS_CREAR`.
* `FERIADOS_EDITAR`.
* `FERIADOS_ESTADO`.
* `FERIADOS_ELIMINAR`.

Regla: la carga inicial es manual desde `/feriados`. La sincronizacion con API externa queda para Fase 10B.

Validacion local reportada:

* Tabla `feriados` creada correctamente.
* Permisos `FERIADOS_*` insertados.
* Restriccion de fecha + pais activa validada.
* `servicio_calendario.es_feriado` validado con resultado `True` y `False` segun existencia de feriado activo.
* Scheduler validado respetando `ejecutar_en_feriados`.
* No se conecto API externa ni sincronizacion automatica.

## Fase 10B - Sincronizacion Nager.Date

Se crea migracion incremental `013_crear_reglas_feriados_irrenunciables.sql`.

Cambios:

* Ajusta `CK_feriados_origen` para permitir `API_NAGER`.
* Crea tabla `reglas_feriados_irrenunciables`.
* Agrega indice unico filtrado por `pais, mes, dia` cuando la regla esta activa.

Tabla: `reglas_feriados_irrenunciables`.

Campos principales:

* `id_regla int identity primary key`.
* `pais varchar(10)`.
* `mes int`.
* `dia int`.
* `nombre_referencia varchar(200)`.
* `irrenunciable bit`.
* `activo bit`.
* `observacion varchar(500)`.
* Campos de auditoria `fecha_creacion`, `fecha_actualizacion`, `usuario_creacion`, `usuario_actualizacion`.

Seeds:

* `009_reglas_irrenunciables_chile.sql`: reglas locales Chile.
* `010_permisos_sincronizacion_feriados.sql`: permiso `FERIADOS_SINCRONIZAR`.

Reglas:

* `MANUAL` tiene prioridad y no se sobrescribe por `API_NAGER`.
* `API_NAGER` puede insertarse o actualizarse desde vista previa confirmada.
* Feriados inactivos no se reactivan automaticamente.
* La tabla local `feriados` sigue siendo fuente final para el scheduler.
* `scheduler_worker.py` no consulta Nager.Date.

Restricciones implementadas en scripts:

* `IF DB_ID(...) IS NULL` para crear base.
* `IF OBJECT_ID(...) IS NULL` para crear tablas.
* PK, FK y `UNIQUE` principales.
* FK desde estados/tipos operativos hacia tablas catalogo.
* `CHECK(numero_version BETWEEN 1 AND 3)`.
* `UNIQUE(id_script, numero_version)`.
* Indice unico filtrado `UX_scripts_versiones_script_activa` para una sola version activa por `id_script`.
* `CHECK` para estados simples de versiones, origen de ejecucion, niveles de log y rangos basicos.

## Resumen del ajuste de versionamiento

El modelo separa el concepto de script en dos niveles:

* `scripts`: contenedor estable asociado a una tarea. Su `nombre_script` debe ser descriptivo, por ejemplo `Script de Carga audios BECS`.
* `scripts_versiones`: archivos Python reales versionados disponibles para ese contenedor.

Decision aprobada: se mantiene esta separacion `scripts` + `scripts_versiones`.

Reglas principales:

* Cada tarea puede tener un contenedor de script asociado.
* Cada contenedor puede mantener maximo 3 versiones disponibles.
* Solo una version puede estar activa por script.
* La ejecucion automatica usa siempre la version activa.
* La ejecucion manual puede usar la activa o una version especifica disponible.
* Toda ejecucion registra `id_script` e `id_version`.
* Los logs se relacionan con `id_ejecucion`; desde ejecuciones se obtiene script y version exacta.
* Los reemplazos de version quedan en `auditoria_cambios` y `logs_sistema`.
* Una version `REEMPLAZADA` no cuenta dentro del maximo de 3 versiones disponibles.
* `scripts.id_version_activa` se mantiene como referencia directa a la version activa.
* El archivo activo real siempre se obtiene desde `scripts_versiones.nombre_archivo` de la version activa.
* El nombre del primer archivo cargado no define `scripts.nombre_script`.
* La eliminacion fisica desde la app se permite solo de forma controlada cuando no existe historial operativo asociado.
* La migracion 009 ya fue validada localmente. En este ambiente afecto 0 filas porque no existian contenedores antiguos con `nombre_script` terminado en `.py`; la nueva logica queda vigente para proximas cargas.

## Fase 6 - Tareas y programacion base

La Fase 6 usa las tablas existentes `tareas` y `programaciones`, agregando campos faltantes mediante migracion incremental.

Campos nuevos propuestos:

* `tareas.observacion_tecnica`: notas internas de operacion.
* `programaciones.modo_ejecucion_dia`: `UNA_VEZ` o `INTERVALO`.
* `programaciones.fecha_especifica`: fecha para programaciones puntuales.
* `programaciones.ejecutar_en_feriados`: marca declarativa; desde Fase 10A el worker la valida contra calendario local de feriados.

Reglas de persistencia:

* Cada tarea mantiene una programacion activa.
* Al editar la programacion se inactiva la programacion activa anterior y se crea una nueva.
* La eliminacion fisica de tareas solo se permite si no existe historial y no se rompe integridad.
* Si hay historial, desde Fase 11F se usa borrado operativo seguro con snapshots.

## Convenciones propuestas

* Tablas en minuscula y plural: `usuarios`, `scripts_versiones`.
* Llaves primarias con prefijo `id_`.
* Llaves foraneas con el mismo nombre de la PK referenciada.
* Fechas en `datetime2(0)`.
* Estados en `varchar(30)` con validacion desde servicio y `CHECK` cuando sea simple.
* Rutas en `nvarchar(500)`.
* Hash de archivos en `varchar(128)`.

## Campos estandar recomendados

* `fecha_creacion datetime2(0) not null default sysdatetime()`
* `fecha_actualizacion datetime2(0) null`
* `usuario_creacion nvarchar(100) null`
* `usuario_actualizacion nvarchar(100) null`
* `activo bit not null default 1`

## Estados propuestos

### estado_tarea

`ACTIVA`, `INACTIVA`, `SUSPENDIDA`, `EN_EJECUCION`, `ERROR`, `FINALIZADA`.

### estado_ejecucion

`PENDIENTE`, `EN_EJECUCION`, `EXITOSA`, `ERROR`, `CANCELADA`, `DETENIDA_MANUALMENTE`, `OMITIDA`, `OMITIDA_FERIADO`, `OMITIDA_FIN_SEMANA`.

### tipo_programacion

`DIARIA`, `SEMANAL`, `MENSUAL`, `FECHAS_ESPECIFICAS`, `INTERVALO_DIARIO`, `MANUAL`.

### estado_version

`ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`.

## Tablas criticas para primera version

* `usuarios`
* `roles`
* `permisos`
* `usuarios_roles`
* `clientes`
* `categorias`
* `tipos`
* `tareas`
* `programaciones`
* `scripts`
* `scripts_versiones`
* `ejecuciones`
* `logs_tareas`
* `logs_sistema`
* `auditoria_cambios`
* `configuracion_sistema`

## Tablas posteriores y futuras

Implementadas despues del modelo inicial:

* `feriados`
* `reglas_feriados_irrenunciables`
* `configuracion_scheduler`
* `scheduler_worker_heartbeat`
* `scheduler_eventos`

Pendientes para fases posteriores:

* `calendarios_laborales`
* `notificaciones`
* `parametros_tarea`
* `ambientes`
* `respaldos`

## Relaciones principales

* Un usuario puede tener varios roles mediante `usuarios_roles`.
* Un rol puede tener varios permisos mediante `permisos`.
* Una tarea pertenece a un cliente, categoria y tipo.
* Una tarea tiene un contenedor de script mediante `scripts.id_tarea`.
* Un contenedor de script tiene hasta 3 versiones disponibles en `scripts_versiones`.
* `scripts.id_version_activa` referencia la version activa vigente.
* Una programacion pertenece a una tarea.
* Una ejecucion pertenece a una tarea, contenedor de script y version exacta ejecutada.
* Un log de tarea pertenece a una ejecucion.
* Auditoria registra cambios de versiones, activaciones y reemplazos.

## Diccionario inicial de datos

### usuarios

Objetivo: almacenar usuarios internos de la aplicacion cuando se implemente Fase 4.

Campos: `id_usuario int identity`, `usuario nvarchar(100)`, `nombre_completo nvarchar(200)`, `email nvarchar(200) null`, `password_hash nvarchar(300)`, `debe_cambiar_password bit`, `ultimo_login datetime2(0) null`, `intentos_fallidos int`, `bloqueado bit`, campos estandar.
PK: `id_usuario`.
Indices: `UX_usuarios_usuario`, `IX_usuarios_activo`.
Observacion: el usuario inicial sigue viniendo desde `.env` hasta Fase 4.

### roles

Objetivo: definir perfiles de acceso.

Campos: `id_rol int identity`, `nombre_rol nvarchar(80)`, `descripcion nvarchar(300) null`, `es_sistema bit`, campos estandar.
PK: `id_rol`.
Indices: `UX_roles_nombre_rol`.

### permisos

Objetivo: controlar permisos por modulo y accion para cada rol.

Campos: `id_permiso int identity`, `id_rol int`, `modulo nvarchar(80)`, `accion nvarchar(80)`, `permitido bit`, campos estandar.
PK: `id_permiso`.
FK: `id_rol -> roles.id_rol`.
Indices: `IX_permisos_rol_modulo`, `UX_permisos_rol_modulo_accion`.

### usuarios_roles

Objetivo: relacionar usuarios con uno o mas roles.

Campos: `id_usuario_rol int identity`, `id_usuario int`, `id_rol int`, `fecha_creacion datetime2(0)`, `usuario_creacion nvarchar(100) null`, `activo bit`.
PK: `id_usuario_rol`.
FK: `id_usuario -> usuarios.id_usuario`, `id_rol -> roles.id_rol`.
Indices: `UX_usuarios_roles_usuario_rol`, `IX_usuarios_roles_rol`.

### clientes

Objetivo: catalogar clientes asociados a tareas.

Campos: `id_cliente int identity`, `nombre_cliente nvarchar(150)`, `nombre_normalizado nvarchar(150)`, `descripcion nvarchar(300) null`, campos estandar.
PK: `id_cliente`.
Indices: `UX_clientes_nombre_normalizado`, `IX_clientes_activo`.

### categorias

Objetivo: agrupar tareas por categoria funcional.

Campos: `id_categoria int identity`, `nombre_categoria nvarchar(150)`, `nombre_normalizado nvarchar(150)`, `descripcion nvarchar(300) null`, campos estandar.
PK: `id_categoria`.
Indices: `UX_categorias_nombre_normalizado`.

### tipos

Objetivo: clasificar tareas por tipo operacional.

Campos: `id_tipo int identity`, `nombre_tipo nvarchar(150)`, `nombre_normalizado nvarchar(150)`, `descripcion nvarchar(300) null`, campos estandar.
PK: `id_tipo`.
Indices: `UX_tipos_nombre_normalizado`.

### tareas

Objetivo: registrar tareas ejecutables asociadas a cliente, categoria, tipo y contenedor de script.

| Campo | Tipo SQL Server | Descripcion |
| --- | --- | --- |
| id_tarea | int identity(1,1) | PK |
| nombre_tarea | nvarchar(200) | Nombre visible |
| descripcion | nvarchar(1000) null | Detalle |
| id_cliente | int | FK clientes |
| id_categoria | int | FK categorias |
| id_tipo | int | FK tipos |
| tipo_tarea | varchar(20) | PROGRAMADA o MANUAL |
| estado_tarea | varchar(30) | Estado operacional |
| ultima_ejecucion | datetime2(0) null | Ultima ejecucion |
| proxima_ejecucion | datetime2(0) null | Proxima ejecucion calculada |
| ultimo_estado_ejecucion | varchar(30) null | Resultado reciente |
| permite_ejecucion_manual | bit | Habilita ejecucion manual |
| fecha_creacion | datetime2(0) | Auditoria |
| fecha_actualizacion | datetime2(0) null | Auditoria |
| requiere_env | bit | Indica si la version requiere archivo `.env` propio |
| ruta_env_fisica | nvarchar(500) null | Ruta fisica del `.env` de la version |
| ruta_env_relativa | nvarchar(500) null | Ruta relativa desde `RUTA_BASE_ENV_SCRIPTS` |
| usuario_creacion | nvarchar(100) null | Auditoria |
| usuario_actualizacion | nvarchar(100) null | Auditoria |
| activo | bit | Estado logico |

PK: `id_tarea`.
FK: `id_cliente`, `id_categoria`, `id_tipo`.
Indices: `IX_tareas_estado`, `IX_tareas_cliente_categoria_tipo`, `IX_tareas_proxima_ejecucion`, `IX_tareas_tipo_tarea`, `IX_tareas_nombre`.
Observacion: se elimina `id_script_actual` de `tareas`; el contenedor de script se resuelve desde `scripts.id_tarea`.

### scripts

Objetivo: representar el contenedor estable de scripts asociado a una tarea/proceso, sin guardar archivos fisicos directamente.

| Campo | Tipo SQL Server | Descripcion |
| --- | --- | --- |
| id_script | int identity(1,1) | PK |
| id_tarea | int | FK tareas |
| nombre_script | nvarchar(200) | Nombre descriptivo del contenedor, no nombre de archivo `.py` |
| descripcion | nvarchar(1000) null | Descripcion funcional |
| id_version_activa | int null | FK a `scripts_versiones.id_version` |
| fecha_creacion | datetime2(0) | Auditoria |
| fecha_actualizacion | datetime2(0) null | Auditoria |
| usuario_creacion | nvarchar(100) null | Auditoria |
| usuario_actualizacion | nvarchar(100) null | Auditoria |
| activo | bit | Estado logico |

PK: `id_script`.
FK: `id_tarea -> tareas.id_tarea`, `id_version_activa -> scripts_versiones.id_version`.
Indices: `UX_scripts_id_tarea`, `IX_scripts_version_activa`, `IX_scripts_activo`.
Observacion: `id_version_activa` fue aprobado como FK directa. Puede quedar `null` durante la creacion inicial antes de cargar la primera version; luego debe apuntar a una version activa. Desde Fase 7.5, al crear el primer archivo el contenedor usa formato `Script de {nombre_tarea}` y el archivo real queda en `scripts_versiones.nombre_archivo`.

### scripts_versiones

Objetivo: almacenar hasta 3 versiones disponibles por contenedor de script con trazabilidad de carga, hash, rutas y estado.

| Campo | Tipo SQL Server | Descripcion |
| --- | --- | --- |
| id_version | int identity(1,1) | PK |
| id_script | int | FK scripts |
| numero_version | tinyint | 1, 2 o 3 |
| nombre_archivo | nvarchar(255) | Archivo `.py` seguro |
| ruta_fisica | nvarchar(500) | Ruta resuelta en ambiente |
| ruta_relativa | nvarchar(500) | Ruta desde `RUTA_BASE_SCRIPTS` |
| hash_archivo | varchar(128) | Hash del contenido |
| estado_version | varchar(30) | ACTIVA, DISPONIBLE, REEMPLAZADA, INACTIVA |
| es_activa | bit | Marca rapida de version activa |
| usuario_carga | nvarchar(100) | Usuario que cargo/reemplazo |
| fecha_carga | datetime2(0) | Fecha de carga/reemplazo |
| observacion | nvarchar(1000) null | Motivo o comentario |
| fecha_creacion | datetime2(0) | Auditoria |
| fecha_actualizacion | datetime2(0) null | Auditoria |

PK: `id_version`.
FK: `id_script -> scripts.id_script`.
Indices recomendados:

* `UX_scripts_versiones_script_numero`: unico por `id_script, numero_version`.
* `UX_scripts_versiones_script_activa_filtrado`: unico filtrado por `id_script` donde `es_activa = 1`.
* `IX_scripts_versiones_script_estado`: busqueda por script y estado.
* `IX_scripts_versiones_hash`: trazabilidad por hash.

Observaciones:

* La ruta relativa debe seguir `CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/vN/NOMBRE_SCRIPT.py`.
* `ruta_fisica` se deriva de `RUTA_BASE_SCRIPTS` y no debe quemarse en codigo.
* No se permite eliminacion fisica desde la app en primera version.
* Para deshabilitar una version se debe usar `estado_version = INACTIVA`.
* Para reemplazar una version se debe usar `estado_version = REEMPLAZADA` sobre la version anterior y registrar auditoria.
* Los archivos fisicos deben conservarse para trazabilidad; cualquier politica futura de limpieza debe ser posterior, controlada y auditada.
* Si `requiere_env = 1`, el servicio de ejecucion debe validar que exista `ruta_env_fisica` antes de iniciar el proceso.
* La base solo guarda rutas del `.env` de script; nunca contenido sensible.

### programaciones

Objetivo: guardar reglas de agenda para tareas programadas o manuales.

Campos: `id_programacion int identity`, `id_tarea int`, `tipo_programacion varchar(30)`, `hora_inicio time(0) null`, `hora_termino time(0) null`, `hora_ejecucion time(0) null`, `intervalo_minutos int null`, `dias_semana varchar(50) null`, `dia_mes tinyint null`, `fechas_especificas nvarchar(max) null`, `configuracion_json nvarchar(max) null`, `zona_horaria nvarchar(80)`, `fecha_inicio_vigencia date null`, `fecha_fin_vigencia date null`, campos estandar.
PK: `id_programacion`.
FK: `id_tarea -> tareas.id_tarea`.
Indices: `IX_programaciones_tarea_activo`, `IX_programaciones_tipo`.

### ejecuciones

Objetivo: registrar cada intento de ejecucion manual o automatica, indicando exactamente la version ejecutada.

| Campo | Tipo SQL Server | Descripcion |
| --- | --- | --- |
| id_ejecucion | bigint identity(1,1) | PK |
| id_tarea | int | FK tareas |
| id_script | int | FK contenedor de script ejecutado |
| id_version | int | FK version exacta ejecutada |
| origen_ejecucion | varchar(20) | MANUAL o AUTOMATICA |
| estado_ejecucion | varchar(30) | Estado |
| fecha_hora_inicio | datetime2(0) | Inicio |
| fecha_hora_termino | datetime2(0) null | Termino |
| duracion_segundos | int null | Duracion |
| codigo_salida | int null | Codigo del proceso |
| mensaje_error | nvarchar(max) null | Error resumido |
| usuario_ejecucion | nvarchar(100) null | Usuario o scheduler |
| pid_proceso | int null | Proceso local si aplica |
| usuario_detencion | nvarchar(100) null | Usuario que solicito detener |
| fecha_hora_detencion | datetime2(0) null | Fecha/hora de detencion |
| motivo_detencion | nvarchar(500) null | Motivo informado |
| fue_detencion_forzada | bit | Indica si fue necesario forzar termino |
| fecha_creacion | datetime2(0) | Auditoria |

PK: `id_ejecucion`.
FK: `id_tarea -> tareas.id_tarea`, `id_script -> scripts.id_script`, `id_version -> scripts_versiones.id_version`.
Indices: `IX_ejecuciones_tarea_fecha`, `IX_ejecuciones_script_version`, `IX_ejecuciones_estado`, `IX_ejecuciones_inicio`.
Observacion: el servicio debe validar que `id_version` pertenezca al `id_script` informado.

Para detencion manual, el servicio debe actualizar `estado_ejecucion` a `DETENIDA_MANUALMENTE` o `CANCELADA`, cerrar `fecha_hora_termino`, calcular duracion y registrar usuario/motivo de detencion.

### logs_tareas

Objetivo: vincular ejecuciones con logs fisicos y metadatos.

Campos: `id_log bigint identity`, `id_tarea int`, `id_ejecucion bigint`, `nombre_tarea nvarchar(200)`, `nombre_script nvarchar(255)`, `nombre_archivo_log nvarchar(255)`, `ruta_fisica_log nvarchar(500)`, `ruta_relativa_log nvarchar(500)`, `fecha_hora_inicio datetime2(0)`, `fecha_hora_termino datetime2(0) null`, `duracion_segundos int null`, `estado_final varchar(30)`, `codigo_salida int null`, `mensaje_error nvarchar(max) null`, `usuario_ejecucion nvarchar(100) null`, `fecha_creacion datetime2(0)`.
PK: `id_log`.
FK: `id_tarea -> tareas.id_tarea`, `id_ejecucion -> ejecuciones.id_ejecucion`.
Indices: `IX_logs_tareas_tarea_fecha`, `IX_logs_tareas_ejecucion`, `IX_logs_tareas_estado`.
Observacion: no duplica `id_version`; se obtiene desde `ejecuciones`.

### logs_sistema

Objetivo: registrar eventos internos de seguridad, sistema y operacion.

Campos: `id bigint identity`, `usuario nvarchar(100) null`, `accion nvarchar(100)`, `modulo nvarchar(100)`, `descripcion nvarchar(max)`, `valor_anterior nvarchar(max) null`, `valor_nuevo nvarchar(max) null`, `ip varchar(45) null`, `user_agent nvarchar(500) null`, `fecha_hora datetime2(0)`, `nivel varchar(30)`, `fecha_creacion datetime2(0)`.
PK: `id`.
Indices: `IX_logs_sistema_fecha`, `IX_logs_sistema_usuario`, `IX_logs_sistema_modulo_nivel`.

### auditoria_cambios

Objetivo: registrar cambios de datos importantes con trazabilidad antes/despues.

Campos: `id_auditoria bigint identity`, `tabla_afectada nvarchar(100)`, `id_registro nvarchar(100)`, `accion nvarchar(50)`, `valor_anterior nvarchar(max) null`, `valor_nuevo nvarchar(max) null`, `usuario nvarchar(100)`, `ip varchar(45) null`, `user_agent nvarchar(500) null`, `fecha_hora datetime2(0)`, `modulo nvarchar(100)`.
PK: `id_auditoria`.
Indices: `IX_auditoria_tabla_registro`, `IX_auditoria_usuario_fecha`, `IX_auditoria_fecha`.
Observacion: debe registrar cargas, activaciones, reemplazos e inactivaciones de versiones.

### configuracion_sistema

Objetivo: guardar parametros no sensibles modificables desde UI futura.

Campos: `id_configuracion int identity`, `clave nvarchar(120)`, `valor nvarchar(max)`, `tipo_dato varchar(30)`, `descripcion nvarchar(300) null`, `es_sensible bit`, campos estandar.
PK: `id_configuracion`.
Indices: `UX_configuracion_clave`.
Observacion: secretos reales siguen en `.env`.

## Estrategia para maximo 3 versiones

Decision aprobada para primera version: validar el maximo de 3 versiones en capa de servicio y reforzar en base con constraints e indice unico filtrado.

### Validacion en servicio

Ventajas:

* Mensajes claros al usuario antes de tocar archivos.
* Permite flujo guiado: si hay 3 versiones, pedir seleccion de version a reemplazar.
* Mantiene el control junto con validaciones de extension, ruta, hash y auditoria.

Desventajas:

* Si otro proceso escribe directo a la base, podria saltarse la regla.

### Indices y constraints recomendados

* `CHECK(numero_version between 1 and 3)` limita los numeros permitidos.
* `UNIQUE(id_script, numero_version)` evita dos versiones con el mismo numero.
* Indice unico filtrado `WHERE es_activa = 1` garantiza una sola version activa.

### Trigger o procedimiento almacenado

Uso futuro aprobado si se requiere blindaje en base:

* Trigger `AFTER INSERT/UPDATE` puede impedir mas de 3 versiones activas/disponibles por `id_script`.
* Procedimiento almacenado `sp_cargar_version_script` centraliza la regla.

Decision aprobada: iniciar con servicio + constraints simples; trigger o procedimiento almacenado queda como mejora futura.

## Estructura fisica propuesta para scripts versionados

Decision aprobada: usar carpetas `v1`, `v2` y `v3`.

```text
scripts/CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/v1/NOMBRE_SCRIPT.py
scripts/CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/v2/NOMBRE_SCRIPT.py
scripts/CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/v3/NOMBRE_SCRIPT.py
```

Ejemplo:

```text
scripts/AUDIOS/VENTAS/BECS/PROGRAMADAS/SCRIPT1/v1/SCRIPT1.py
scripts/AUDIOS/VENTAS/BECS/PROGRAMADAS/SCRIPT1/v2/SCRIPT1.py
scripts/AUDIOS/VENTAS/BECS/PROGRAMADAS/SCRIPT1/v3/SCRIPT1.py
```

## Estructura fisica para env por script y logs

Fase 4.3 define separar codigo, variables sensibles y logs:

```text
scripts/CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/v1/NOMBRE_SCRIPT.py
env_scripts/CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/v1/.env
logs_tareas/ANIO/MES/DIA/LOG_NombreScript_fecha_hora.log
```

Reglas:

* `scripts/` contiene codigo cargado por usuarios.
* `env_scripts/` contiene variables sensibles por script/version.
* `logs_tareas/` contiene trazabilidad de ejecucion.
* `env_scripts/` y cualquier `.env` interno no se versionan.
* La app no debe guardar contenido de `.env` de script en base de datos.

## Migracion Fase 4.3 ejecutada

Se requirio nueva migracion porque los scripts ejecutados en Fase 3B no tenian todos los campos necesarios para detencion manual ni `.env` por version.

Archivo creado:

```text
database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql
```

Ejecutada y validada manualmente en SQL Server local el 2026-06-12.

Incluye:

* Catalogo `DETENIDA_MANUALMENTE` en `cat_estados_ejecucion`.
* `scripts_versiones.requiere_env`.
* `scripts_versiones.ruta_env_fisica`.
* `scripts_versiones.ruta_env_relativa`.
* `ejecuciones.usuario_detencion`.
* `ejecuciones.fecha_hora_detencion`.
* `ejecuciones.motivo_detencion`.
* `ejecuciones.fue_detencion_forzada`.
* Indices de apoyo para busqueda por `requiere_env` y detenciones.

Validaciones reportadas:

* `DETENIDA_MANUALMENTE` existe en `cat_estados_ejecucion`.
* `scripts_versiones` contiene `requiere_env`, `ruta_env_fisica` y `ruta_env_relativa`.
* `ejecuciones` contiene `usuario_detencion`, `fecha_hora_detencion`, `motivo_detencion` y `fue_detencion_forzada`.

No se implemento ejecucion real, scheduler ni tareas en Flask.

## Scripts SQL sugeridos, no ejecutados

Estos fragmentos son propuesta para discusion; no deben ejecutarse hasta aprobar modelo y estrategia de migraciones.

```sql
-- PROPUESTA NO EJECUTADA
-- Una sola version activa por script:
-- CREATE UNIQUE INDEX UX_scripts_versiones_script_activa
-- ON scripts_versiones(id_script)
-- WHERE es_activa = 1;

-- Numeros permitidos:
-- ALTER TABLE scripts_versiones
-- ADD CONSTRAINT CK_scripts_versiones_numero
-- CHECK (numero_version between 1 and 3);

-- Estados permitidos:
-- ALTER TABLE scripts_versiones
-- ADD CONSTRAINT CK_scripts_versiones_estado
-- CHECK (estado_version in ('ACTIVA','DISPONIBLE','REEMPLAZADA','INACTIVA'));
```

## Decisiones aprobadas antes de Fase 3B

* Se aprueba mantener `scripts` como script logico y `scripts_versiones` como tabla fisica de versiones.
* Se aprueba mantener `scripts.id_version_activa`.
* Una version `REEMPLAZADA` no cuenta dentro del maximo de 3 versiones disponibles.
* En primera version, el maximo de 3 se controla en capa de servicio.
* En base de datos se refuerza con `CHECK(numero_version between 1 and 3)`, `UNIQUE(id_script, numero_version)` e indice unico filtrado para una sola version activa.
* Trigger o procedimiento almacenado queda como mejora futura.
* Se aprueba estructura fisica con carpetas `v1`, `v2` y `v3`.

## Decisiones pendientes antes de implementar

* Confirmar estrategia exacta de reemplazo fisico: sobrescribir carpeta `vN` con auditoria previa o preservar copia historica adicional antes de reemplazar.
* Ejecutar scripts manualmente en SQL Server Management Studio cuando se apruebe la aplicacion fisica del modelo.
* Fase posterior: crear conexion Flask-SQL Server y repositorios, sin quemar credenciales.
