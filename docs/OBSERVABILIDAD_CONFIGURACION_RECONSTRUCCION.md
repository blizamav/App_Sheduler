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
| `/tareas/<id>/notificaciones` | Configuracion, destinatarios y script/version activa | Reemplazo atomico auditado | `TAREAS_EDITAR` |
| `/configuracion/mail-graph` | `configuracion_mail_graph` + estado ENV | Lectura/edicion no secreta | `CONFIGURACION_ADMIN` |

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

El estado del Worker usa exclusivamente el ultimo registro activo de
`scheduler_worker_heartbeat`, leido por `RepositorioOperacion`. El Worker
actualiza `fecha_ultimo_heartbeat` mediante `RepositorioHeartbeat` al iniciar,
entrar o cerrar un ciclo, reportar error y detenerse.

La politica central deriva sus ventanas desde
`configuracion_scheduler.intervalo_revision_segundos`:

* `OPERATIVO`: heartbeat con antiguedad menor o igual a dos intervalos;
* `ATENCION`: sobre dos y hasta cinco intervalos, o error reciente reportado;
* `DETENIDO`: sobre cinco intervalos o estado explicito `DETENIDO`;
* `DESCONOCIDO`: heartbeat inexistente, fecha invalida, estado no reconocido o
  fallo de consulta. Nunca se asume `OPERATIVO` por defecto.

Si falta configuracion se usa una unica politica de respaldo de 60 segundos,
centralizada en el caso de uso. El endpoint read-only
`GET /operacion/worker`, disponible para cualquier sesion autenticada, retorna
solo estado, antiguedad, pendientes y proximo intervalo de consulta; no expone
PID, host, credenciales ni detalles de conexion. La UI consulta inicialmente y
luego cada medio intervalo real, acotado entre 10 y 60 segundos.

Scheduler, mantenimiento, concurrencia, errores de 24 horas, candidatas
vencidas, pendientes y ultima automatica son datos SQL reales, no metricas
simuladas. Mantenimiento critico bloquea reservas; Worker detenido no las
bloquea y conserva las nuevas ejecuciones como `PENDIENTE`.

El heartbeat representa la vida del proceso Worker y no exige que el Scheduler
este habilitado en ese proceso. Por eso el modo oficial `--queue-only` informa
el mismo ciclo `EN_CICLO`/`ESPERANDO`/`DETENIDO` y puede clasificarse como
`OPERATIVO` mientras consume la cola. Su resultado tecnico es `QUEUE_ONLY`; no
debe confundirse con una evaluacion de programaciones. La dimension Scheduler
continua derivandose de su configuracion y actividad SQL independiente.

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
| Operacion/Worker compacto | `/operacion/worker` | GET | Sesion autenticada | No aplica | Todos los perfiles autenticados |
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
correo permanecen fuera del cierre de Hito 8 y se incorporan en Hito 10.

## Extension Hito 10

`/operacion/estado` incorpora un resumen no sensible del calendario local y de
Graph: disponibilidad de fila global, activacion efectiva, presencia del secret
y ultimo resultado registrado. Nunca muestra tenant, client secret, token ni
destinatarios de ejecuciones.

La configuracion Mail Graph edita solo campos SQL no secretos. El estado
efectivo exige fila activa, `GRAPH_MAIL_ENABLED`, identificadores completos y
secret presente. Los intentos quedan en `notificaciones_envios`; los errores
tecnicos se resumen tambien en `logs_sistema` sin sobrescribir el estado de la
ejecucion. No se implementa retry automatico.

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

## Healthchecks Docker Hito 13

Web usa `/salud` como comprobacion de proceso sin abrir SQL. Worker usa
`python -m app_scheduler.worker.aplicacion --healthcheck`: valida configuracion,
consulta en SQL el heartbeat reconstruido del hostname exacto del contenedor y
exige un estado vivo dentro de cinco intervalos. El comando es de solo lectura,
no construye Scheduler, no reclama cola y falla cerrado ante SQL no disponible.

Docker `healthy` no sustituye el panel operativo: la Web sigue mostrando la
clasificacion completa `OPERATIVO/ATENCION/DETENIDO/DESCONOCIDO`. La politica
`unless-stopped` reinicia el contenedor si muere su proceso principal; Docker
Compose por si solo no reinicia un proceso vivo solo porque su healthcheck pase
a `unhealthy`.
