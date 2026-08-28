# APP Scheduler

APP Scheduler v1.0.0 es una aplicacion web interna para programar, ejecutar,
monitorear y auditar procesos Python de equipos TI. Centraliza tareas, scripts
versionados, programaciones, ejecuciones, logs, evidencia opcional y
notificaciones bajo autorizacion backend y trazabilidad SQL Server.

## Estado

**Version estable: v1.0.0.** Los Hitos 0-15 de la reconstruccion estan
cerrados. El runtime oficial vive en `src/app_scheduler/`; `app/`, `run.py` y
`scheduler_worker.py` se conservan unicamente como referencia historica y no
son entrypoints operativos.

## Arquitectura

```text
Usuario -> Web Flask -> SQL Server <- Scheduler/Worker -> Motor subprocess
                         |                    |
                         +-- auditoria        +-- logs/evidencia/notificaciones
```

* **Web**: autenticacion, autorizacion, mantenedores, solicitudes manuales,
  consulta operativa y administracion.
* **Scheduler**: evalua programaciones activas, calendario y configuracion; si
  corresponde crea una ejecucion `PENDIENTE` idempotente.
* **Worker**: consume la cola compartida, reclama atomica y ejecuta tanto
  solicitudes manuales como automaticas.
* **Motor**: inicia Python con `shell=False`, entorno controlado, timeout,
  captura incremental y detencion persistida.
* **SQL Server**: fuente de verdad de configuracion, cola, estados, heartbeat,
  auditoria y trazabilidad.

Flujo manual:

```text
Web -> PENDIENTE -> Worker -> EN_EJECUCION -> estado final
```

Flujo automatico:

```text
Scheduler -> PENDIENTE -> Worker -> EN_EJECUCION -> estado final
```

## Capacidades

* login hibrido con `SUPER_ADMIN_ENV` y usuarios SQL;
* usuarios, roles, permisos y autorizacion backend;
* clientes, categorias, tipos, tareas y programaciones;
* scripts logicos con hasta tres versiones y `.env` por version;
* hub global `/scripts`, carga y descarga confinadas y hash de archivo;
* ejecucion manual/automatica, consola, detencion y logs con timestamp;
* Scheduler, Worker, heartbeat, semaforo operativo y modo `queue-only`;
* feriados locales y sincronizacion manual con Nager.Date;
* auditoria inmutable y Papelera con eliminacion permanente condicionada;
* evidencia stdout V1 opcional y notificaciones at-most-once por Graph;
* Factory Reset in-place, transaccional y fail-closed sobre la unica base QA.

## Runtime oficial

Con el entorno virtual activo y `PYTHONPATH=src`:

```powershell
# Web
python -m app_scheduler.web

# Worker completo: Scheduler + cola
python -m app_scheduler.worker.aplicacion

# Solo cola, sin evaluar programaciones
python -m app_scheduler.worker.aplicacion --queue-only

# Un ciclo controlado de cola
python -m app_scheduler.worker.aplicacion --queue-only --once
```

Los checks no abren puertos ni ejecutan ciclos:

```powershell
python -m app_scheduler.web --check
python -m app_scheduler.worker.aplicacion --check
python -m app_scheduler.worker.aplicacion --help
```

## Instalacion local en Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host ".env ya existe. No se sobrescribe." }
$env:PYTHONPATH="src"
python -m app_scheduler.web
```

Completa `.env` manualmente con los valores del ambiente. Nunca sobrescribas un
archivo real ni copies secretos a Git, documentacion, UI o logs.

## Docker QA

Docker usa siempre `.env.docker`; no existe fallback hacia `.env`.

```powershell
if (!(Test-Path .env.docker)) { Copy-Item .env.docker.example .env.docker } else { Write-Host ".env.docker ya existe. No se sobrescribe." }
docker compose config --quiet
docker compose build web worker
docker compose up -d web worker
docker compose ps
```

* Web: `http://127.0.0.1:5000/`
* Salud Web: `http://127.0.0.1:5000/salud`
* Logs: `docker compose logs --tail 200 web worker`
* Detencion: `docker compose down`

El Worker usa `restart: unless-stopped`; su healthcheck consulta el heartbeat
del hostname sin reclamar ejecuciones. Detalle en
[`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md).

## Operacion

`PENDIENTE` significa que la solicitud esta persistida y espera un Worker. Si
el Worker se detiene antes de reclamarla, no se pierde: se recupera al volver a
estar operativo. El semaforo distingue `OPERATIVO`, `ATENCION`, `DETENIDO` y
`DESCONOCIDO` usando heartbeat y configuracion real.

Para diagnosticar sin crear automaticas:

```powershell
python -m app_scheduler.worker.aplicacion --queue-only
```

Consulta primero **Estado del sistema**, luego heartbeat y logs. No cambies
estados de ejecucion mediante SQL manual. Guia completa:
[`docs/OPERACION_WORKER.md`](docs/OPERACION_WORKER.md).

## Base de datos y Factory Reset

La unica base de la aplicacion es `APP_SCHEDULER_QA`.

* `database/release/`: release SQL publicado y protegido.
* `database/bootstrap/`: instalacion limpia y validacion canonica.
* `database/factory_reset/`: reconstruccion in-place controlada.
* `database/migrations/`: correcciones incrementales historicas.

El Factory Reset v1.0.0 no crea, elimina ni renombra bases. Usa cuenta de
mantenimiento dedicada con `db_owner` solo sobre `APP_SCHEDULER_QA`, lock,
transaccion SQL, cuarentena filesystem y rollback. Permanece deshabilitado por
defecto y requiere autorizacion operativa explicita. Ver
[`docs/FACTORY_RESET.md`](docs/FACTORY_RESET.md).

## Notificaciones, Graph y evidencia

Microsoft Graph utiliza client credentials almacenadas en el entorno. Su kill
switch ENV y la configuracion SQL deben estar activos simultaneamente. El
despacho reserva en SQL antes de llamar Graph y no aplica retry automatico.
Evidencia 1.0 es opcional y se captura desde stdout delimitado; el JSON completo
no se persiste. Graph quedo deshabilitado al cerrar QA.

## Seguridad

La version incluye controles implementados y validados durante QA: sesion
minima, CSRF, autoescape Jinja, SQL parametrizado, permisos backend,
confinamiento filesystem, uploads/downloads controlados, `shell=False`,
separacion de credenciales SQL y secretos fuera de UI/BD/logs cuando
corresponde. Esto no equivale a una certificacion externa ni a declarar
ausencia total de vulnerabilidades.

## Pruebas

```powershell
$env:PYTHONPATH="src"
python -m pytest -q tests/reconstruccion
python -m pytest -q
python -m compileall app src scheduler_worker.py
```

Los checks Jinja, JavaScript y Docker usados para release estan descritos en
[`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md).

## Limitacion conocida

Si el Worker cae abruptamente despues del claim y mientras una ejecucion esta
`EN_EJECUCION`, APP Scheduler no la relanza automaticamente. Esta decision
evita duplicar efectos de scripts no idempotentes; el caso requiere diagnostico
operacional. Una estrategia futura de lease/recuperacion puede abordarlo sin
cambiar el contrato de v1.0.0.

## Documentacion

* [Arquitectura oficial](docs/ARQUITECTURA_RECONSTRUCCION.md)
* [Mapa de modulos](docs/MODULOS.md)
* [Despliegue](docs/DESPLIEGUE.md)
* [Operacion Worker](docs/OPERACION_WORKER.md)
* [Observabilidad](docs/OBSERVABILIDAD_CONFIGURACION_RECONSTRUCCION.md)
* [UI/UX](docs/UI_UX_RECONSTRUCCION.md)
* [Seguridad](docs/SEGURIDAD.md)
* [Roadmap](docs/ROADMAP.md)
* [Changelog](docs/CHANGELOG.md)
* [Bitacora tecnica](log_codex.md)

Los documentos de fases anteriores se conservan como historia tecnica. Ante
una contradiccion operativa, prevalecen este README y los documentos de
reconstruccion v1.0.0 enlazados arriba.
