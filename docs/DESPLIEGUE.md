# Despliegue

## Ejecucion local en Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host ".env ya existe. No se sobrescribe." }
python run.py
```

En CMD:

```cmd
if not exist .env copy .env.example .env
```

IMPORTANTE:
No ejecutar `copy .env.example .env` si ya existe un archivo `.env`, porque puede sobrescribir credenciales locales. Usar siempre comandos seguros que copien solo si `.env` no existe.

## QA Ubuntu

Pendiente para Fase 11. Debe ejecutarse idealmente con Docker, `.env` propio y volumenes para scripts y logs.

## Produccion Ubuntu

Pendiente para Fase 11. Debe usar Docker, volumenes persistentes, respaldo de base de datos, respaldo de scripts y respaldo de logs.

## Variables por ambiente

Cada ambiente debe tener su propio `.env`; nunca debe versionarse ni sobrescribirse automaticamente. `.env.example` es solo plantilla.

## Configuracion SQL Server local

Variables minimas para conexion Flask-SQL Server:

```env
APP_ENV=LOCAL
DB_SERVER=SERVIDOR_O_INSTANCIA
DB_DATABASE=APP_SCHEDULER_QA
DB_USER=USUARIO_SQL
DB_PASSWORD=PASSWORD_SQL
DB_DRIVER=ODBC Driver 17 for SQL Server
```

Pasos en Windows:

1. Instalar dependencias: `pip install -r requirements.txt`
2. Confirmar que el driver ODBC indicado exista en Windows.
3. Confirmar que SQL Server permita conexiones al servidor/instancia configurada.
4. Ejecutar la app: `python run.py`
5. Iniciar sesion con el usuario inicial desde `.env`.
6. Abrir `http://127.0.0.1:5000/diagnostico/bd`.

Errores comunes:

* `pyodbc` no instalado: ejecutar `pip install -r requirements.txt`.
* Driver ODBC no instalado o nombre distinto en `DB_DRIVER`.
* Instancia SQL Server no accesible por red o firewall.
* SQL Server Browser detenido cuando se usa instancia nombrada.
* Usuario SQL sin permisos sobre `APP_SCHEDULER_QA`.
* Problemas de cifrado/driver: revisar driver ODBC y configuracion SQL Server local.

La ruta de diagnostico no muestra credenciales y no esta disponible en `APP_ENV=PRODUCCION`.

## Ejecucion manual de scripts SQL Server

Los scripts de Fase 3B se encuentran en `database/` y ya fueron ejecutados correctamente de forma manual en SQL Server local para crear `APP_SCHEDULER_QA`.

Orden:

1. `database/migrations/001_crear_base_datos.sql`
2. `database/migrations/002_crear_catalogos.sql`
3. `database/migrations/003_crear_tablas_seguridad.sql`
4. `database/migrations/004_crear_tablas_negocio.sql`
5. `database/migrations/005_crear_tablas_ejecucion_logs.sql`
6. `database/migrations/006_crear_indices.sql`
7. `database/seeds/001_datos_iniciales_catalogos.sql`
8. `database/seeds/002_roles_permisos_iniciales.sql`

Consideraciones:

* Validacion local realizada: tablas existentes, catalogos cargados, roles/permisos cargados y usuario `blizama` no creado en base de datos.
* No ejecutar contra produccion sin respaldo y aprobacion.
* No modificar scripts para incluir claves, usuarios o servidores reales.
* El usuario inicial de aplicacion sigue validandose desde `.env`; los seeds no crean usuario `blizama`.
* La conexion Flask-SQL Server queda pendiente para una fase posterior.

## Docker

Pendiente para Fase 11.

## Volumenes

* Scripts: `RUTA_BASE_SCRIPTS`
* Env de scripts: `RUTA_BASE_ENV_SCRIPTS`
* Logs de tareas: `RUTA_BASE_LOGS_TAREAS`
* Logs de sistema: `RUTA_BASE_LOGS_SISTEMA`

`env_scripts/` debe tratarse como volumen privado por ambiente. No debe versionarse, copiarse a repositorios ni exponerse por servidor web.

Variables de tamano para Fase 7:

```env
MAX_SCRIPT_SIZE_MB=5
MAX_ENV_SIZE_KB=100
```

`scripts/` contiene archivos cargados por usuarios y tambien debe tratarse como volumen de datos, no como codigo fuente del sistema.

## Ejecucion manual Fase 8

Antes de probar ejecuciones manuales con usuarios de base de datos, ejecutar manualmente en SSMS:

```text
database/seeds/006_permisos_ejecuciones.sql
```

El administrador desde `.env` puede acceder sin ejecutar el seed, porque tiene permisos totales de sesion.

Rutas usadas por Fase 8:

* Scripts cargados: `RUTA_BASE_SCRIPTS`.
* Env por version: `RUTA_BASE_ENV_SCRIPTS`.
* Logs de ejecucion: `RUTA_BASE_LOGS_TAREAS`.

Los procesos se ejecutan con el interprete Python actual del entorno donde corre Flask. En Windows, levantar la app desde el entorno virtual correcto antes de ejecutar tareas.

## Configuracion Scheduler Fase 9A

Ejecutar manualmente en SSMS:

```text
database/migrations/010_crear_configuracion_scheduler.sql
database/seeds/007_permisos_scheduler.sql
```

Luego abrir:

```text
http://127.0.0.1:5000/scheduler/configuracion
```

La configuracion operativa vive en SQL Server. No se requiere agregar variables a `.env` para controlar el scheduler.

## Consideraciones de seguridad

No subir secretos, logs reales, scripts productivos ni configuraciones privadas.
