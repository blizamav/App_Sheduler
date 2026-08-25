# Hito 10: feriados, notificaciones y Microsoft Graph

Estado: **CERRADO**. El contrato fue implementado y validado en el runtime
aislado sin modificar el esquema SQL ni habilitar envios reales.

## Matriz contract-first

| Capacidad | SQL canonico | Runtime historico | Documentacion | Reconstruccion al iniciar Hito 10 | Decision Hito 10 |
|---|---|---|---|---|---|
| Calendario local | `feriados` y `reglas_feriados_irrenunciables` | CRUD y reglas locales | Scheduler consume SQL local | El scheduler ya consulta `feriados` | Mantener SQL como unica fuente operativa del scheduler |
| Mantenedor feriados | Campos fecha, nombre, tipo, pais, irrenunciable, origen, activo y trazabilidad | Listar, crear, editar, estado y borrado manual | Permisos `FERIADOS_*` | Sin UI reconstruida | Reconstruir CRUD autorizado, paginado y auditado |
| Sincronizacion Nager.Date | `origen=API_NAGER`; unicidad activa fecha/pais | Preview y aplicacion manual | Manual preserva prioridad | No reconstruida | Cliente central con endpoint fijo oficial, timeout y TLS; sin cron automatico |
| Configuracion por tarea | `notificaciones_config_tarea` | Configuracion por tarea | Evidencia stdout V1 | Captura tecnica parcial | Completar asunto, alertas y destinatarios sin duplicar fuente |
| Destinatarios | `notificaciones_destinatarios`, tipos `EVIDENCIA/ALERTA`, canales `TO/CC/BCC` | Administracion por tarea | Validacion y no duplicados | No reconstruidos | Normalizar, validar y reemplazar atomica y auditadamente |
| Evidencia | `evidencias_ejecucion`, una por ejecucion, solo metadata | Captura stdout | JSON no persiste completo | Captura y metadata operativas | Conservar JSON solo en memoria para componer el correo |
| Trazabilidad email | `notificaciones_envios` | Estados de envio | Separada del estado de ejecucion | No consumida | Reservar `PENDIENTE`, enviar fuera de transaccion y cerrar `ENVIADO/FALLIDO/OMITIDO` |
| Graph global | `configuracion_mail_graph`, clave unica `MAIL_GRAPH` | Client credentials y `sendMail` | Secret solo ENV | Variables `GRAPH_*` tipadas | SQL administra identificadores no secretos; ENV conserva kill switch y secret |
| Correo evidencia | `EVIDENCIA_CLIENTE` | Ejecucion exitosa + evidencia valida | Evento respaldado | No implementado | Enviar tras confirmar resultado de ejecucion |
| Alerta interna | `ALERTA_INTERNA` | Error de proceso/evidencia | Evento respaldado | No implementado | Alertar por ejecucion `ERROR` o evidencia requerida no valida |
| Reintentos | Columnas `intento`, `es_reintento`, `id_envio_origen`; sin cola durable completa | Sin politica robusta | No duplicar correo | No implementado | Sin retry automatico en Hito 10; politica at-most-once mediante reserva |
| Adjuntos | Declarados en JSON, no persistidos como paths separados | Adjuntos simples | Solo archivos autorizados | Valida obligatorio/existencia | Resolver exclusivamente bajo carpeta de version; rechazar enlaces, `.env`, `.py` y exceso de tamano |

## Contrato de feriados

- `dbo.feriados`: PK `id_feriado`; fecha, nombre, tipo, pais, irrenunciable, activo, origen, observacion y trazabilidad.
- Origen permitido por SQL: `MANUAL`, `API`, `API_NAGER`, `IMPORTACION`.
- Unicidad activa: fecha + pais. La aplicacion valida antes de escribir y SQL mantiene la ultima defensa.
- Un registro manual no se sobrescribe durante sincronizacion.
- Un registro inactivo no se reactiva automaticamente.
- La eliminacion fisica desde UI se limita a registros `MANUAL`; los demas se desactivan.
- Los irrenunciables se calculan desde `reglas_feriados_irrenunciables`.

## Sincronizacion Nager.Date

- Endpoint permitido: `https://date.nager.at/api/v3/PublicHolidays/{Year}/{CountryCode}`.
- Pais de uso actual: `CL`; el formulario acepta un codigo ISO alfabetico de dos caracteres.
- La consulta externa ocurre solo por accion POST autorizada y nunca dentro del ciclo del scheduler.
- Preview y aplicacion vuelven a comparar contra SQL para evitar decisiones obsoletas.
- Fallos DNS, timeout, HTTP, JSON o esquema se convierten en error controlado; nunca vacian el calendario local.

## Variables Graph

| Variable | Secreta | Visible UI | Editable UI | Origen | Consumidor |
|---|---:|---:|---:|---|---|
| `GRAPH_MAIL_ENABLED` | No | Estado | No | ENV | Web/worker |
| `GRAPH_CLIENT_SECRET` | Si | Solo presencia | No | ENV | Cliente Graph |
| `GRAPH_SECRET_CONFIG_MODE` | No | Estado | No | ENV | Diagnostico |
| `GRAPH_TENANT_ID` | No | Solo presencia | Reemplazo SQL | ENV + SQL | Configuracion efectiva |
| `GRAPH_CLIENT_ID` | No | Solo presencia | Reemplazo SQL | ENV + SQL | Configuracion efectiva |
| `GRAPH_SCOPE` | No | Si | Si, SQL | ENV + SQL | Token Graph |
| `GRAPH_SEND_MAIL_USER` | No | Si | Si, SQL | ENV + SQL | `sendMail` |
| `GRAPH_SAVE_TO_SENT_ITEMS` | No | Si | Si, SQL | ENV + SQL | Payload Graph |
| `GRAPH_ALERTAS_DEFAULT` | No | Si | Si, SQL | ENV + SQL | Alertas internas |

La configuracion efectiva exige simultaneamente `GRAPH_MAIL_ENABLED=true`, fila SQL activa, identificadores completos y secret presente. Ningun valor secreto se serializa en DTO publico, HTML, auditoria o logs.

## Eventos y permisos

| Modulo/accion | Permiso real | Ruta/metodo |
|---|---|---|
| Ver feriados | `FERIADOS_VER` | `GET /feriados/` |
| Crear | `FERIADOS_CREAR` | `GET/POST /feriados/nuevo` |
| Editar | `FERIADOS_EDITAR` | `GET/POST /feriados/<id>/editar` |
| Cambiar estado | `FERIADOS_ESTADO` | `POST /feriados/<id>/estado` |
| Eliminar manual | `FERIADOS_ELIMINAR` | `POST /feriados/<id>/eliminar` |
| Sincronizar | `FERIADOS_SINCRONIZAR` | `GET /feriados/sincronizar`, `POST` preview/aplicar |
| Configuracion por tarea | `TAREAS_EDITAR` | `POST /tareas/<id>/evidencia` |
| Configuracion Graph | `CONFIGURACION_ADMIN` | `GET/POST /configuracion/mail-graph` |

Todos los POST usan CSRF global. Los cambios humanos se escriben junto con `auditoria_cambios` en la misma unidad de trabajo.

## Seguridad y limites

- Endpoints Nager y Graph son constantes de backend; no se aceptan URLs desde request.
- No se usa `verify=False`, `eval`, `exec` ni importacion de scripts de usuario.
- Direcciones se validan, normalizan en minusculas y deduplican por tipo/canal/email.
- El HTML de correo se genera con templates y autoescape; el contenido externo se sanitiza antes de renderizar.
- Adjuntos directos se mantienen bajo el limite conservador del request Graph; carga por sesion queda fuera de Hito 10.
- El fallo Graph no altera el estado final de la ejecucion.
- No hay correo de prueba ni envio real durante la suite automatica.

## Deuda legitima

- No existe sincronizacion automatica Nager respaldada por contrato.
- No se implementa retry automatico hasta contar con politica durable de recuperacion de reservas `PENDIENTE`.
- Adjuntos grandes mediante upload session Graph quedan fuera del alcance actual.
- El smoke real Graph requiere autorizacion y destinatario de prueba explicitos.

## Implementacion y validacion

La implementacion vive exclusivamente en `src/app_scheduler/`: modulo
`feriados`, modulo `notificaciones`, repositorios dedicados, integracion
post-ejecucion en el worker, vistas Bootstrap y observabilidad. Se reutilizaron
las tablas, restricciones y permisos del bootstrap vigente; no se crearon
migraciones ni seeds.

La suite automatica cubre CRUD, auditoria, preview/aplicacion, idempotencia,
prioridad manual, errores Nager, destinatarios, configuracion efectiva, payload
Graph, sanitizacion, confinamiento de adjuntos, despacho, alertas y aislamiento
del estado de ejecucion. Las llamadas HTTP se simulan: QA Graph real permanece
pendiente de autorizacion expresa.

Gate local: `306 passed, 1 skipped`, compileall, 32 templates Jinja, seis
archivos JavaScript, checks web/worker, Compose y build Docker aprobados. Las
vistas fueron revisadas en 1440x900, 390x844 y 844x390 sin overflow global ni
errores de consola.

El gate especifico de reconstruccion aprobo `280 passed, 1 skipped`. Se realizo
un unico GET no destructivo a Nager.Date para 2026/CL: DNS, TLS, HTTP y esquema
minimo del parser fueron correctos, con 17 registros recibidos y cero
persistencia. No se llamo Microsoft Graph ni se envio correo real.

El smoke QA fue exclusivamente de lectura: confirmo la base autorizada, 17
feriados, reglas locales y las cinco tablas de notificaciones. La configuracion
Graph QA se clasifica `DESHABILITADA`: existe una fila SQL activa con
identificadores completos, mientras el kill switch ENV esta apagado y el secret
no esta presente. No se imprimieron identificadores, direcciones ni secretos;
no hubo DML ni envio real.

Tenant ID y Client ID vigentes tampoco se incluyen en el HTML. La UI informa
solo si estan configurados y permite escribir un valor nuevo para reemplazarlos;
dejar esos campos vacios conserva la configuracion actual.
