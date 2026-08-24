# Observabilidad y configuracion de la reconstruccion

## Alcance Hito 8

Estado: CERRADO.

El runtime aislado incorpora observabilidad global, configuracion operativa y
configuracion de evidencia sin cambiar el esquema SQL ni los entrypoints
historicos. `logs_tareas` conserva stdout/stderr por ejecucion; `logs_sistema`
representa eventos internos de APP Scheduler.

## Contratos

| Superficie | Tabla | Lectura/escritura | Permiso |
| --- | --- | --- | --- |
| `/logs/` y `/logs/<id>` | `logs_sistema` | Lectura paginada/detalle | `LOGS_VER` |
| `/operacion/estado` | `scheduler_worker_heartbeat`, `configuracion_scheduler`, `ejecuciones`, `logs_sistema`, `tareas` | Lectura acotada | `SCHEDULER_CONFIG_VER` |
| `/configuracion/` | `configuracion_sistema`, `configuracion_scheduler` | Matriz solo lectura | `SCHEDULER_CONFIG_VER` |
| `POST /configuracion/scheduler` | `configuracion_scheduler`, `auditoria_cambios` | Edicion por allowlist | `SCHEDULER_CONFIG_EDITAR` |
| `/tareas/<id>/evidencia` | `notificaciones_config_tarea`, script/version activa | Upsert tipado | `TAREAS_EDITAR` |

Todas las escrituras HTTP usan CSRF global. Scheduler y evidencia registran
`auditoria_cambios` en la misma unidad de trabajo.

## Logs y retencion

Filtros disponibles: fecha desde/hasta, nivel real, modulo, evento y busqueda.
El orden es fijo `fecha_hora DESC, id DESC`; la pagina contiene 25 filas. Los
detalles se autoescapan y patrones comunes de secretos se protegen antes de la
presentacion. La tabla no tiene campos separados de origen o worker, por lo que
no se inventan esos filtros.

No existe una politica ejecutable respaldada para eliminar `logs_sistema`. Hito
8 no crea jobs, `DELETE` ni retencion automatica. La cuantificacion y ejecucion
segura de retencion permanece como deuda operativa.

## Estado operativo

El estado worker usa el ultimo heartbeat activo. Es `ACTIVO` dentro de dos
intervalos, advertencia `STALE` sobre dos y error `STALE` sobre cinco; tambien
distingue `ERROR`, `DETENIDO` y `NO_REGISTRADO`. Scheduler, mantenimiento,
concurrencia, errores de 24 horas, candidatas vencidas y ultima automatica son
datos SQL reales, no metricas simuladas.

## Configuracion

`configuracion_sistema` se clasifica como solo lectura. Un valor con
`es_sensible=1` se muestra como `[PROTEGIDO]`. No se aceptan claves desde el
request ni se migran secretos ENV a SQL.

Allowlist editable de scheduler:

* `scheduler_activo` (booleano);
* `permitir_ejecucion_automatica` (booleano);
* `modo_mantenimiento` (booleano);
* `intervalo_revision_segundos` (10-3600);
* `max_ejecuciones_concurrentes` (1-20).

Los cambios se aplican cuando el worker lee la configuracion en su siguiente
ciclo; Flask no reinicia procesos o contenedores.

Matriz de autorizacion Hito 8:

| Modulo/accion | Ruta | Metodo | Permiso | CSRF | Roles bootstrap |
| --- | --- | --- | --- | --- | --- |
| Logs/listar | `/logs/` | GET | `LOGS_VER` | No aplica | `SUPER_ADMIN`, `ADMIN`, `TI`, `TERCERO` |
| Logs/detalle | `/logs/<id>` | GET | `LOGS_VER` | No aplica | `SUPER_ADMIN`, `ADMIN`, `TI`, `TERCERO` |
| Operacion/estado | `/operacion/estado` | GET | `SCHEDULER_CONFIG_VER` | No aplica | `SUPER_ADMIN`, `ADMIN`, `TI` |
| Configuracion/ver | `/configuracion/` | GET | `SCHEDULER_CONFIG_VER` | No aplica | `SUPER_ADMIN`, `ADMIN`, `TI` |
| Scheduler/editar | `/configuracion/scheduler` | POST | `SCHEDULER_CONFIG_EDITAR` | Obligatorio | `SUPER_ADMIN`, `ADMIN`, `TI` |
| Evidencia/configurar | `/tareas/<id>/evidencia` | POST | `TAREAS_EDITAR` | Obligatorio | `SUPER_ADMIN`, `ADMIN`, `TI` |

`SUPER_ADMIN_ENV` conserva autorizacion global por el contrato transversal de
identidad. Los nombres de rol anteriores provienen del seed canonico; no se
crearon permisos ni roles nuevos.

## Evidencia

La UI configura exclusivamente campos existentes de captura: habilitacion,
archivos declarados y log tecnico, con plantilla fija `STDOUT_V1`. Antes de
habilitar, el `.py` activo se analiza con AST sin ejecutar ni importar codigo.
Debe declarar soporte/version 1.0 y contener ambos delimitadores como strings
reales. Comentarios por si solos no son compatibles. Graph, destinatarios y
correo permanecen fuera de Hito 8.

## QA y seguridad

El smoke QA es primero de solo lectura con `user_scheduler`: conexion, contrato,
tablas, columnas, indices, FK y consultas representativas. No modifica schema,
no ejecuta scripts operativos y no inicia ciclos scheduler. Si no existe una
credencial SQL de aplicacion autorizada, el login SQL valido se documenta como
no ejecutado; nunca se solicitan ni imprimen passwords.

Controles aplicados: permisos backend, CSRF, autoescape, CSP, SQL parametrizado,
allowlist, rangos, UoW/rollback, auditoria, confinamiento de rutas y minimizacion
de secretos. Esto no constituye una declaracion formal de cumplimiento OWASP.

## Resultado de integracion QA

El smoke `tests/reconstruccion/smoke_qa_hito8.py` se ejecuto desde los
contenedores reconstruidos contra la unica base autorizada,
`APP_SCHEDULER_QA`, con `user_scheduler`. Confirmo 21 tablas minimas, cuatro
indices criticos, dos FK criticas, lecturas paginadas de logs, heartbeat,
scheduler, configuracion y rutas filesystem existentes.

El login invalido permanecio en el flujo de autenticacion con mensaje generico
y sin `ErrorPersistencia`. `SUPER_ADMIN_ENV` fue validado. El login SQL valido
no se ejecuto porque no se proporciono una credencial de aplicacion autorizada;
no se pidio ni se mostro ningun secreto. El smoke fuerza rollback para sus
intentos de autenticacion y confirmo `QA_HITO8_* = 0` antes y despues.

No se ejecutaron ciclos del scheduler, scripts operativos ni escritura
confirmada. No se modificaron schema, `.env`, `.env.docker`, bootstrap, release
o runtime historico. El worker observado en QA estaba `DETENIDO`; la lectura y
clasificacion fueron correctas y no se intento iniciarlo desde Flask.
