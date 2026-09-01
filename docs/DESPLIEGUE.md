# Despliegue APP Scheduler v1.0.1

## Prerrequisitos

* Python 3.11 o superior;
* SQL Server con `APP_SCHEDULER_QA` y bootstrap 19C.1, o una base historica con
  la migracion incremental 023 aplicada;
* ODBC Driver 17 for SQL Server;
* Docker Desktop/Engine con Compose para QA;
* acceso de red al SQL Server;
* cuenta SQL ordinaria para Web/Worker;
* cuenta de mantenimiento separada solo si se habilitara Factory Reset.

No subas `.env` ni `.env.docker` a Git. Las plantillas no contienen secretos y
nunca deben sobrescribir configuraciones reales existentes.

## Local Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host ".env ya existe. No se sobrescribe." }
$env:PYTHONPATH="src"
python -m app_scheduler.web --check
python -m app_scheduler.web
```

Worker completo en otra terminal:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="src"
python -m app_scheduler.worker.aplicacion
```

Diagnostico sin Scheduler:

```powershell
python -m app_scheduler.worker.aplicacion --queue-only
python -m app_scheduler.worker.aplicacion --queue-only --once
```

`run.py` y `scheduler_worker.py` no son comandos oficiales de v1.0.0.

## QA Docker

`.env.docker` es el unico archivo de entorno de Compose.

```powershell
if (!(Test-Path .env.docker)) { Copy-Item .env.docker.example .env.docker } else { Write-Host ".env.docker ya existe. No se sobrescribe." }
docker compose config --quiet
docker compose build web worker
docker compose up -d web worker
docker compose ps
```

Comprobaciones:

```powershell
curl.exe --fail http://127.0.0.1:5000/salud
docker compose logs --tail 200 web
docker compose logs --tail 200 worker
docker inspect --format='{{.State.Health.Status}}' app-scheduler-web
docker inspect --format='{{.State.Health.Status}}' app-scheduler-worker
```

El Worker puede tardar hasta la ventana de `start_period` en registrar su primer
heartbeat. El healthcheck Worker es read-only.

## Reinicio y detencion

```powershell
docker compose restart web
docker compose restart worker
docker compose stop worker
docker compose up -d worker
docker compose down
```

`restart: unless-stopped` recupera la caida del proceso principal. Una detencion
manual persiste hasta volver a iniciar el servicio.

## Variables

Las plantillas `.env.example` y `.env.docker.example` contienen las claves
vigentes para Flask, SQL, Worker, Scheduler, rutas, Graph y Factory Reset. Los
valores reales se configuran manualmente por ambiente.

Reglas:

* `.env` corresponde a LOCAL;
* `.env.docker` corresponde a QA Docker;
* `DB_DATABASE` debe ser `APP_SCHEDULER_QA`;
* `GRAPH_MAIL_ENABLED=false` es el default seguro;
* `FACTORY_RESET_HABILITADO=false` es el default seguro;
* no copies secretos entre archivos mediante scripts automaticos;
* el Worker Docker anula credenciales Web y de mantenimiento que no necesita.

## Checks de release

```powershell
$env:PYTHONPATH="src"
python -m pytest -q tests/reconstruccion
python -m pytest -q
python -m compileall app src scheduler_worker.py
python -m app_scheduler.web --check
python -m app_scheduler.worker.aplicacion --check
python -m app_scheduler.worker.aplicacion --help
docker compose config --quiet
docker compose build web worker
```

Jinja:

```powershell
python -c "from pathlib import Path; from jinja2 import Environment; e=Environment(); [e.parse(p.read_text(encoding='utf-8')) for p in Path('src/app_scheduler/presentacion/templates').rglob('*.html')]; print('JINJA_OK')"
```

JavaScript:

```powershell
Get-ChildItem src/app_scheduler/presentacion/static/js -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
```

## Troubleshooting

### Web no saludable

Revisar `docker compose logs web`, variables requeridas, conectividad ODBC y
`/salud`. No imprimir la connection string completa.

### Worker detenido o desconocido

Revisar `docker compose ps`, logs, heartbeat en **Estado del sistema** y modo
mantenimiento. Scheduler OFF no significa necesariamente Worker detenido.

### Cola pendiente

Una fila `PENDIENTE` espera claim y es recuperable. Iniciar Worker o usar
`--queue-only`; no mutar estados por SQL.

### Worker cae durante EN_EJECUCION

No se aplica auto-retry. Revisar proceso, PID, log y efectos externos antes de
decidir una accion operacional.

### Graph

La disponibilidad exige kill switch ENV, secret y fila SQL activa. No habilitar
para diagnosticos generales ni repetir un envio ambiguo.

## Produccion

v1.0.0 define y valida LOCAL y QA Docker. Un despliegue productivo debe fijar
TLS/cookies, gestion de secretos, backups, monitoreo, rotacion y procedimiento
de rollback conforme a la infraestructura de destino; no debe reutilizar
credenciales QA.
