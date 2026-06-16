# APP Scheduler

Aplicacion web Flask para programar, ejecutar, monitorear y auditar tareas Python orientadas a equipos de TI.

## Estado actual

El proyecto avanzo hasta Fase 9A:

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
* Fase 5.1: eliminacion controlada en mantenedores.
* Fase 6: tareas con programacion base, sin ejecucion real ni scheduler.
* Fase 7: gestion de scripts, versiones v1-v3 y `.env` por version.
* Fase 8: ejecucion manual con consola, logs y detencion controlada.
* Fase 9A: configuracion operativa del scheduler en base de datos, sin worker automatico.

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
* Modulo de tareas en `/tareas`.
* Programacion base declarativa: manual, diaria, semanal, mensual y fecha especifica.
* Gestion de scripts por tarea.
* Versionamiento de scripts hasta v3.
* Asociacion de `.env` por version sin mostrar contenido.
* Ejecucion manual de version activa.
* Consola visual de ejecucion con polling.
* Detencion manual de ejecucion.
* Configuracion operativa del scheduler en `/scheduler/configuracion`.
* Filtros de usuarios por estado, rol y busqueda general.
* Confirmaciones para activar/deshabilitar usuarios.
* Roles y permisos iniciales desde base de datos.
* Logs de sistema iniciales para login y cambios de usuarios.
* Definicion tecnica de `.env` por script y detencion manual de ejecuciones.

## Funcionalidades pendientes

* Scheduler automatico.
* Ejecuciones automaticas por calendario.
* Panel avanzado de logs.
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
MAX_SCRIPT_SIZE_MB=5
MAX_ENV_SIZE_KB=100
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
11. `database/migrations/008_ajustar_tareas_y_programaciones_base.sql`
12. `database/seeds/004_permisos_tareas.sql`
13. `database/seeds/005_permisos_scripts.sql`
14. `database/migrations/009_corregir_nombre_script_contenedor.sql`
15. `database/seeds/006_permisos_ejecuciones.sql`
16. `database/migrations/010_crear_configuracion_scheduler.sql`
17. `database/seeds/007_permisos_scheduler.sql`

La base `APP_SCHEDULER_QA` ya fue creada y validada manualmente en SQL Server local. El usuario inicial de la aplicacion sigue validandose desde `.env`; no se crea `blizama` en base de datos todavia.

Fase 4.3 agrega una migracion propuesta, no ejecutada automaticamente:

```text
database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql
```

Esta migracion prepara rutas `.env` por version de script y campos para detencion manual de ejecuciones.

Fase 6 agrega scripts incrementales, no ejecutados automaticamente:

```text
database/migrations/008_ajustar_tareas_y_programaciones_base.sql
database/seeds/004_permisos_tareas.sql
```

Ejecutalos manualmente en SSMS antes de usar persistencia completa del modulo `/tareas`.

Fase 7 no requiere migracion nueva si la migracion 007 ya fue aplicada. Solo agrega permisos:

```text
database/seeds/005_permisos_scripts.sql
```

Ejecutalo manualmente en SSMS para usuarios de base de datos. El administrador desde `.env` puede acceder sin seed.

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
