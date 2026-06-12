# APP Scheduler

Aplicacion web Flask para programar, ejecutar, monitorear y auditar tareas Python orientadas a equipos de TI.

## Estado actual

El proyecto avanzo hasta Fase 3D:

* Fase 1: estructura base, documentacion, login inicial desde `.env` y layout base.
* Fase 2: diseno UI/UX base, responsive y corporativo.
* Fase 3A: propuesta de modelo SQL Server.
* Ajuste Fase 3A: versionamiento de scripts con maximo 3 versiones.
* Fase 3B: scripts SQL Server versionados.
* Fase 3C: validacion manual de scripts SQL en SQL Server local.
* Fase 3D: conexion Flask con SQL Server desde `.env` y diagnostico controlado.

## Stack actual

* Python
* Flask
* HTML
* CSS
* JavaScript
* SQL Server
* pyodbc
* python-dotenv
* Docker planificado para QA y produccion

## Funcionalidades actuales

* Login inicial desde variables de entorno.
* Panel principal visual.
* Layout corporativo responsive.
* Documentacion tecnica en `docs/`.
* Scripts SQL versionados.
* Base `APP_SCHEDULER_QA` validada en SQL Server local.
* Conexion Flask-SQL Server mediante `.env`.
* Ruta de diagnostico de base de datos para `LOCAL` y `QA`: `/diagnostico/bd`.

## Funcionalidades pendientes

* Usuarios desde base de datos.
* Roles y permisos funcionales.
* CRUD de clientes, categorias y tipos.
* CRUD de tareas.
* Carga y versionamiento real de scripts.
* Scheduler.
* Ejecuciones manuales y automaticas.
* Logs reales.
* Auditoria funcional.
* Docker QA/produccion.
* Calendario laboral y feriados.

## Ejecucion local en Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Luego abrir:

```text
http://127.0.0.1:5000
```

Para diagnostico de base de datos, iniciar sesion y abrir:

```text
http://127.0.0.1:5000/diagnostico/bd
```

## Variables de entorno

El archivo `.env` no se sube a Git. El archivo `.env.example` sirve como plantilla.

Variables principales:

```env
APP_ENV=LOCAL
APP_SECRET_KEY=CAMBIAR_EN_ENV_REAL
APP_HOST=127.0.0.1
APP_PORT=5000

DB_SERVER=
DB_DATABASE=APP_SCHEDULER_QA
DB_USER=
DB_PASSWORD=
DB_DRIVER=ODBC Driver 17 for SQL Server

USUARIO_ADMIN_DEFECTO=blizama
PASSWORD_ADMIN_DEFECTO=CAMBIAR_EN_ENV_REAL
```

## Base de datos

Los scripts SQL Server estan en:

```text
database/migrations/
database/seeds/
```

Orden documentado:

1. `database/migrations/001_crear_base_datos.sql`
2. `database/migrations/002_crear_catalogos.sql`
3. `database/migrations/003_crear_tablas_seguridad.sql`
4. `database/migrations/004_crear_tablas_negocio.sql`
5. `database/migrations/005_crear_tablas_ejecucion_logs.sql`
6. `database/migrations/006_crear_indices.sql`
7. `database/seeds/001_datos_iniciales_catalogos.sql`
8. `database/seeds/002_roles_permisos_iniciales.sql`

La base `APP_SCHEDULER_QA` ya fue creada y validada manualmente en SQL Server local. El usuario inicial de la aplicacion sigue validandose desde `.env`; no se crea `blizama` en base de datos todavia.

## Documentacion

* `docs/README_PROYECTO.md`
* `docs/ARQUITECTURA.md`
* `docs/BASE_DATOS.md`
* `docs/MODULOS.md`
* `docs/FLUJOS.md`
* `docs/SEGURIDAD.md`
* `docs/DESPLIEGUE.md`
* `docs/CHANGELOG.md`
* `log_codex.md`

`log_codex.md` es la memoria tecnica del proyecto y debe leerse antes de continuar nuevas fases.
