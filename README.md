# APP Scheduler

Aplicacion web Flask para programar, ejecutar, monitorear y auditar tareas Python orientadas a equipos de TI.

## Estado actual

El proyecto avanzo hasta Fase 5:

* Fase 1: estructura base, documentacion, login inicial desde `.env` y layout base.
* Fase 2: diseno UI/UX base, responsive y corporativo.
* Fase 3A: propuesta de modelo SQL Server.
* Ajuste Fase 3A: versionamiento de scripts con maximo 3 versiones.
* Fase 3B: scripts SQL Server versionados.
* Fase 3C: validacion manual de scripts SQL en SQL Server local.
* Fase 3D: conexion Flask con SQL Server desde `.env` y diagnostico controlado.
* Fase 4: usuarios, roles y permisos iniciales con login hibrido.
* Fase 4.1: mejoras UX del modulo usuarios, filtros y confirmaciones.
* Fase 4.2: modal corporativo reutilizable para confirmaciones.
* Fase 4.3: definicion tecnica de ejecucion segura, detencion manual y `.env` por script.
* Fase 5: mantenedores de clientes, categorias y tipos.

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
* Login hibrido: administrador inicial desde `.env` y usuarios desde SQL Server.
* Administracion basica de usuarios en `/usuarios`.
* Mantenedores de clientes en `/clientes`.
* Mantenedores de categorias en `/categorias`.
* Mantenedores de tipos en `/tipos`.
* Eliminacion controlada en mantenedores solo si no existen dependencias.
* Filtros de usuarios por estado, rol y busqueda general.
* Confirmaciones para activar/deshabilitar usuarios.
* Roles y permisos iniciales desde base de datos.
* Logs de sistema iniciales para login y cambios de usuarios.
* Definicion tecnica de `.env` por script y detencion manual de ejecuciones.

## Funcionalidades pendientes

* CRUD de tareas.
* Carga y versionamiento real de scripts.
* Carga funcional de `.env` por script.
* Scheduler.
* Ejecuciones manuales y automaticas.
* Detencion real de procesos en ejecucion.
* Logs reales de tareas y panel funcional de logs.
* Auditoria funcional.
* Docker QA/produccion.
* Calendario laboral y feriados.

## Ejecucion local en Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host ".env ya existe. No se sobrescribe." }
python run.py
```

En CMD:

```cmd
if not exist .env copy .env.example .env
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

No ejecutes `copy .env.example .env` si ya existe `.env`, porque sobrescribe credenciales locales. Si `.env` fue sobrescrito, reconstruyelo manualmente con tus valores reales; no inventar ni publicar credenciales.

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

RUTA_BASE_SCRIPTS=scripts
RUTA_BASE_ENV_SCRIPTS=env_scripts
RUTA_BASE_LOGS_TAREAS=logs_tareas
RUTA_BASE_LOGS_SISTEMA=logs_sistema
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
9. `database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql`
10. `database/seeds/003_permisos_mantenedores.sql`

La base `APP_SCHEDULER_QA` ya fue creada y validada manualmente en SQL Server local. El usuario inicial de la aplicacion sigue validandose desde `.env`; no se crea `blizama` en base de datos todavia.

Fase 4.3 agrega una migracion propuesta, no ejecutada automaticamente:

```text
database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql
```

Esta migracion prepara rutas `.env` por version de script y campos para detencion manual de ejecuciones.

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
