# APP Scheduler

APP Scheduler es una aplicacion web interna para administrar, programar, ejecutar, monitorear y auditar procesos Python orientados a equipos de TI.

## Estado del proyecto

El runtime actual permanece operativo como referencia mientras se realiza una reconstruccion limpia y controlada.

* Hito 0 - Inventario y arquitectura: CERRADO.
* Hito 1 - Base del proyecto y configuracion: CERRADO.
* Hito 2 - Base de datos y repositorios funcionales: CERRADO.
* Hito 3 - Autenticacion, usuarios, roles y permisos: CERRADO.
* Hito 4 - Clientes, categorias y tipos: NO INICIADO.

Fuentes maestras de la reconstruccion:

* [Inventario Maestro](docs/INVENTARIO_MAESTRO_RECONSTRUCCION.md)
* [Arquitectura de Reconstruccion](docs/ARQUITECTURA_RECONSTRUCCION.md)
* [Roadmap](docs/ROADMAP.md)
* [Persistencia de la Reconstruccion](docs/PERSISTENCIA_RECONSTRUCCION.md)

La implementacion no se reescribira de una sola vez. Los modulos se reemplazaran por hitos verificables, preservando reglas de negocio, trazabilidad, seguridad y compatibilidad necesarias.

El runtime historico sigue activo mediante `run.py` y `scheduler_worker.py`. El runtime reconstruido vive aislado en `src/app_scheduler/`; Hito 3 incorpora login, sesion, autorizacion y usuarios sin reemplazar las rutas historicas vigentes.

Validacion aislada del Hito 3:

```powershell
$env:PYTHONPATH="src"
python -m pytest -q tests/reconstruccion
python -m app_scheduler.web --check
```

El detalle funcional y la matriz de permisos estan en [Autenticacion y usuarios de la reconstruccion](docs/AUTENTICACION_USUARIOS_RECONSTRUCCION.md).

## Capacidades de referencia

El sistema actual incluye:

* autenticacion hibrida con `SUPER_ADMIN_ENV` y usuarios SQL;
* roles, permisos, usuarios y mantenedores;
* tareas, programaciones, scripts y hasta tres versiones;
* `.env` por version de script sin persistir secretos en la base;
* ejecucion manual y automatica, consola, logs y detencion;
* scheduler y worker separado con heartbeat y eventos;
* papelera, auditoria, feriados, evidencias y Microsoft Graph;
* Factory Reset in-place sobre la base autorizada.

Estas capacidades constituyen requisitos de reconstruccion, no una declaracion de que el nuevo runtime ya fue implementado.

## Arquitectura vigente

Stack principal:

* Python y Flask;
* Jinja, HTML, CSS y JavaScript;
* SQL Server mediante `pyodbc`;
* servicios separados `web` y `worker`;
* Docker Compose para QA.

Reglas centrales:

* unica base del aplicativo: `APP_SCHEDULER_QA`;
* `user_scheduler` para operacion normal con minimo privilegio;
* `user_scheduler_mantenimiento` para mantenimiento estructural, con `db_owner` solo en `APP_SCHEDULER_QA`;
* la cuenta de mantenimiento no requiere `sysadmin`, `CREATE ANY DATABASE`, `ALTER ANY DATABASE` ni `CONTROL SERVER`;
* Factory Reset es in-place; la arquitectura blue-green esta deprecada;
* `database/release/` es publicado, protegido y de solo lectura.

## Entornos

* `.env`: ejecucion LOCAL.
* `.env.docker`: ejecucion QA mediante Docker.

Docker carga explicitamente `.env.docker`. No existe fallback automatico hacia `.env`.

Los archivos reales no se versionan. Las plantillas son `.env.example` y `.env.docker.example`. Nunca sobrescribas un archivo `.env` existente.

## Ejecucion local de referencia

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host ".env ya existe. No se sobrescribe." }
python run.py
```

El worker se ejecuta en otro proceso:

```powershell
python scheduler_worker.py
```

Validacion no funcional del runtime reconstruido:

```powershell
$env:PYTHONPATH="src"
python -m app_scheduler.web --check
python -m app_scheduler.worker.aplicacion --check
```

Las opciones `--check` validan configuracion y bootstrap sin abrir puertos, consultar SQL o iniciar scheduler.

## Docker QA

Configura manualmente `.env.docker` a partir de su plantilla sin sobrescribir valores existentes. Luego valida la composicion antes de levantar servicios:

```powershell
docker compose config --quiet
docker compose up --build
```

## Base de datos

Los canales SQL tienen responsabilidades distintas:

* `database/release/`: release publicado y protegido.
* `database/bootstrap/`: instalacion limpia y validacion vigente.
* `database/factory_reset/`: reconstruccion in-place controlada.
* `database/migrations/`: correctivos incrementales especificos.
* `database/legacy_pre_release_13B/`: historia, no fuente ejecutable vigente.

No ejecutes SQL destructivo, migraciones o Factory Reset sobre QA sin diagnostico, revision y autorizacion explicita.

## Documentacion

La documentacion tecnica se encuentra en `docs/`. Para continuar el trabajo se debe leer primero:

1. `docs/INVENTARIO_MAESTRO_RECONSTRUCCION.md`
2. `docs/ARQUITECTURA_RECONSTRUCCION.md`
3. `docs/ROADMAP.md`
4. `docs/CHANGELOG.md`
5. `log_codex.md`

El historial detallado permanece en `docs/CHANGELOG.md` y `log_codex.md`; el README describe solamente el estado vigente.
