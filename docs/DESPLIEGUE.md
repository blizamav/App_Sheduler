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

Pendiente para Fase 13. Debe ejecutarse con `.env` propio, SQL Server accesible, volumenes para scripts/env/logs y estrategia de arranque separada para web y worker.

## Produccion Ubuntu

Pendiente para Fase 13. Debe usar Docker Compose o systemd, volumenes persistentes, respaldo de base de datos, respaldo de scripts y respaldo de logs.

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
* La conexion Flask-SQL Server existe desde Fase 3D mediante `.env` y `pyodbc`.

## Docker

Pendiente para Fase 13E. Alternativas previstas: Docker Compose o systemd, segun decision de despliegue.

## Roadmap operativo

Pendientes de Fase 13:

* 13A Scripts operativos Windows/Linux.
* 13B Preparacion QA Linux.
* 13C Preparacion produccion.
* 13D Worker como servicio.
* 13E Docker Compose o systemd.

Pendientes de Fase 14:

* Retencion automatica.
* Backups.
* Exportaciones.
* Notificaciones.
* Reportes de operacion.

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

## Validacion manual del worker Fase 12B.2

La configuracion del Programador en la app no inicia por si sola `scheduler_worker.py`. La app solo guarda reglas operativas; el proceso worker debe levantarse manualmente o, en Fase 13, mediante servicio/proceso gestionado.

Validacion de una vuelta:

```powershell
python scheduler_worker.py --once
```

Validacion continua manual:

```powershell
python scheduler_worker.py
```

Detener con `CTRL+C` en la consola donde se ejecuto.

Estados esperados:

* Worker apagado: no ejecuta tareas aunque el Programador este activo.
* Worker encendido + Programador inactivo: no ejecuta y registra omision del ciclo.
* Worker encendido + ejecucion automatica deshabilitada: no ejecuta y registra omision del ciclo.
* Worker encendido + modo mantenimiento: no ejecuta y registra omision del ciclo.
* Worker encendido + Programador activo + ejecucion automatica habilitada: evalua tareas elegibles y puede crear ejecuciones `AUTOMATICA`.

Validaciones manuales en SSMS despues de correr el worker:

```sql
SELECT TOP 30 id_ejecucion, id_tarea, origen_ejecucion, estado_ejecucion,
       pid_proceso, codigo_salida, fecha_hora_inicio, fecha_hora_termino,
       duracion_segundos
FROM dbo.ejecuciones
ORDER BY id_ejecucion DESC;
```

```sql
SELECT TOP 50 id_evento, fecha_evento, tipo_evento, decision, motivo,
       id_tarea, nombre_tarea, nombre_worker, detalle
FROM dbo.scheduler_eventos
ORDER BY id_evento DESC;
```

```sql
SELECT TOP 20 *
FROM dbo.scheduler_worker_heartbeat
ORDER BY fecha_actualizacion DESC;
```

La configuracion operativa vive en SQL Server. No se requiere agregar variables a `.env` para controlar el scheduler.

## Worker Scheduler Fase 9B

Ejecutar manualmente en SSMS antes de levantar el worker:

```text
database/migrations/011_agregar_control_scheduler_ejecuciones.sql
```

Para Fase 11B, ejecutar tambien:

```text
database/migrations/014_crear_scheduler_worker_heartbeat.sql
```

La app web y el worker son procesos separados.

Terminal 1:

```powershell
python run.py
```

Terminal 2:

```powershell
python scheduler_worker.py
```

Para probar un solo ciclo sin dejar el worker en ejecucion continua:

```powershell
python scheduler_worker.py --once
```

Con Fase 11B, `--once` crea o actualiza `scheduler_worker_heartbeat`, registra el ultimo ciclo y deja estado `DETENIDO` por salida controlada.

Para validar heartbeat en loop:

1. Ejecutar `python scheduler_worker.py`.
2. Abrir `http://127.0.0.1:5000/scheduler/panel`.
3. Revisar la seccion `Estado del worker`.
4. Confirmar que `Ultimo heartbeat` se actualiza segun `intervalo_revision_segundos`.

Antes de activar ejecucion automatica:

1. Abrir `/scheduler/configuracion`.
2. Activar `scheduler_activo`.
3. Activar `permitir_ejecucion_automatica`.
4. Verificar que `modo_mantenimiento` este desactivado.
5. Configurar intervalo y maximo concurrentes.

El worker usa `.env` solo para conexion a SQL Server y rutas tecnicas. La configuracion operativa vive en `configuracion_scheduler`.

## Feriados locales Fase 10A

Ejecutar manualmente en SSMS:

```text
database/migrations/012_crear_calendario_feriados.sql
database/seeds/008_permisos_feriados.sql
```

Luego abrir:

```text
http://127.0.0.1:5000/feriados
```

La carga inicial de feriados es manual. No se conecta API externa ni se sincronizan feriados automaticamente en Fase 10A.

## Sincronizacion feriados Fase 10B

Ejecutar manualmente en SSMS:

```text
database/migrations/013_crear_reglas_feriados_irrenunciables.sql
database/seeds/009_reglas_irrenunciables_chile.sql
database/seeds/010_permisos_sincronizacion_feriados.sql
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Luego abrir:

```text
http://127.0.0.1:5000/feriados/sincronizar
```

La sincronizacion es manual y controlada. El scheduler no consulta Nager.Date.

## Consideraciones de seguridad

No subir secretos, logs reales, scripts productivos ni configuraciones privadas.
