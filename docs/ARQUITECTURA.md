# Arquitectura

## Arquitectura general

La Fase 1 define una aplicacion Flask modular con fabrica `crear_app()`, configuracion centralizada y rutas separadas en Blueprint.

## Capas del sistema

* Presentacion: templates HTML y assets CSS/JS.
* Aplicacion: rutas Flask y control de sesion.
* Configuracion: lectura de `.env`.
* Datos: SQL Server mediante `pyodbc` y repositorios dedicados.
* Servicios: reglas de negocio iniciales para usuarios, roles, permisos y logs de sistema.

## Flujo de datos inicial

1. Usuario accede a `/login`.
2. Flask valida credenciales contra variables de entorno.
3. Se crea sesion segura con `APP_SECRET_KEY`.
4. Usuario entra a `/panel`.

## Backend

Backend Python Flask con estructura inicial y modulos Fase 4:

* `app/__init__.py`
* `app/config.py`
* `app/rutas.py`
* `app/rutas_usuarios.py`
* `app/rutas_mantenedores.py`
* `app/rutas_tareas.py`
* `app/rutas_scripts.py`
* `app/rutas_ejecuciones.py`
* `app/rutas_scheduler.py`
* `app/seguridad.py`
* `app/database/conexion.py`
* `app/repositorios/`
* `app/servicios/`

## Frontend

HTML/CSS/JS sin Streamlit. Desde Fase 2 el layout incluye login corporativo, sidebar responsive, topbar con usuario, tarjetas de metricas, tabla base, badges de estado y panel lateral visual preparado para logs.

La capa visual mantiene el diseno de Fase 2. El panel principal conserva placeholders; las pantallas `/usuarios`, `/clientes`, `/categorias`, `/tipos` y `/tareas` consumen datos reales de SQL Server.

## Base de datos

SQL Server sera incorporado desde Fase 3. Base objetivo: `APP_SCHEDULER_QA`, configurable por `.env`.

En Fase 3B se crearon scripts SQL versionados bajo `database/migrations/` y `database/seeds/`. Estos scripts no se ejecutan automaticamente y Flask aun no se conecta a SQL Server. La capa de datos futura debe aislarse en repositorios/servicios para evitar consultas SQL directas desde rutas Flask.

En Fase 3D se agrego la capa inicial de conexion en `app/database/conexion.py`. Esta capa lee `DB_SERVER`, `DB_DATABASE`, `DB_USER`, `DB_PASSWORD` y `DB_DRIVER` desde `.env`, construye la cadena ODBC sin quemar credenciales, permite probar `SELECT 1` y retorna errores amigables sin exponer password.

La ruta temporal `/diagnostico/bd` valida conectividad solo en ambientes `LOCAL` o `QA`, requiere sesion iniciada y no esta disponible en `PRODUCCION`.

Entidades principales propuestas: usuarios, roles, permisos, clientes, categorias, tipos, tareas, programaciones, scripts, scripts_versiones, ejecuciones, logs_tareas, logs_sistema, auditoria_cambios y configuracion_sistema.

Fase 6 agrega repositorio y servicio de tareas:

* `app/repositorios/repositorio_tareas.py`: consultas SQL y persistencia de tareas/programaciones.
* `app/servicios/servicio_tareas.py`: validaciones de negocio, resumen legible de programacion y logs de sistema.
* `app/rutas_tareas.py`: endpoints protegidos por permisos para listado, formulario, estado y eliminacion.

La programacion de Fase 6 es declarativa. No existe proceso scheduler ni ejecucion real de scripts en esta fase.

Fase 7 agrega capa de scripts:

* `app/rutas_scripts.py`: endpoints de scripts, versiones y env.
* `app/repositorios/repositorio_scripts.py`: persistencia de scripts y versiones.
* `app/servicios/servicio_scripts.py`: reglas de negocio.
* `app/servicios/servicio_archivos.py`: validacion y guardado seguro de archivos.

Los archivos cargados viven fuera del codigo fuente operativo bajo `scripts/` y `env_scripts/`, ambos excluidos de Git.

Para versionamiento controlado, `scripts` representa el contenedor de script de una tarea y `scripts_versiones` representa los archivos Python disponibles. Las ejecuciones registran `id_script` e `id_version` para saber exactamente que archivo fue ejecutado. Los logs de tarea continuan asociados a `id_ejecucion`.

Fase 8 agrega capa de ejecucion manual:

* `app/rutas_ejecuciones.py`: endpoints para iniciar, ver consola, consultar log y detener.
* `app/repositorios/repositorio_ejecuciones.py`: persistencia en `ejecuciones` y `logs_tareas`.
* `app/servicios/servicio_ejecuciones.py`: validaciones, creacion de ejecucion, archivo de log y actualizacion de estado.
* `app/servicios/servicio_env_scripts.py`: carga segura de `.env` por version.
* `app/servicios/servicio_procesos.py`: inicio y detencion de procesos.

La ejecucion manual usa `subprocess` sin `shell=True`, registra PID y captura stdout/stderr hacia archivo. La consola se actualiza por polling HTTP cada 3 segundos.

Fase 9A agrega configuracion operativa del scheduler:

* `app/rutas_scheduler.py`: pantalla `/scheduler/configuracion`.
* `app/repositorios/repositorio_configuracion_scheduler.py`: lectura y actualizacion de configuracion activa.
* `app/servicios/servicio_configuracion_scheduler.py`: validaciones y logs.
* `app/templates/scheduler/configuracion.html`: UI administrativa.

La configuracion operativa vive en SQL Server. `.env` queda reservado para configuracion tecnica del ambiente. El worker automatico sera un proceso separado en fase posterior y leera estos parametros desde base de datos.

La FK `scripts.id_version_activa -> scripts_versiones.id_version` se agrega en `006_crear_indices.sql` por dependencia circular entre `scripts` y `scripts_versiones`.

## Scheduler

Pendiente para fase posterior. Debe ejecutarse como servicio separado dentro de la aplicacion.

Fase 9A no implementa worker. Solo deja preparada la configuracion que usara Fase 9B.

Cuando se implemente, la ejecucion automatica debera resolver siempre `scripts.id_version_activa`. La ejecucion manual podra recibir una version especifica disponible, previa confirmacion si no coincide con la activa.

## Ejecucion segura de scripts

Fase 4.3 define que la ejecucion futura debe aislar tres responsabilidades:

* Codigo Python cargado por usuarios en `scripts/`.
* Variables sensibles por script/version en `env_scripts/`.
* Salida y trazabilidad en `logs_tareas/`.

El servicio de ejecucion debera:

1. Resolver tarea, script logico y version exacta.
2. Validar estado y ruta del archivo `.py`.
3. Validar si la version requiere `.env`.
4. Cargar variables del `.env` de script sin guardar ni mostrar secretos.
5. Iniciar el proceso y registrar `pid_proceso`.
6. Actualizar estados, logs y auditoria.

## Detencion manual de ejecuciones

Cuando una ejecucion esta `EN_EJECUCION`, la interfaz muestra accion `Detener ejecucion` solo a usuarios autorizados. La accion usa modal corporativo, intenta termino controlado, fuerza termino si no responde y registra resultado en `ejecuciones`, `logs_tareas` y `logs_sistema`.

## Logs

Fase 8 implementa archivo de log por ejecucion manual bajo `logs_tareas/`. Rutas configurables por `.env`: `logs_tareas` y `logs_sistema`.

Los logs de tarea no deben incluir secretos provenientes del `.env` de script. La salida capturada debe filtrarse cuando sea posible y el sistema debe documentar que los scripts cargados no deben imprimir credenciales.

## Seguridad

Fase 4 usa login hibrido:

* Primero valida el administrador inicial desde `.env`.
* Si no coincide, valida usuarios activos en SQL Server.
* Las contrasenas de base de datos usan hash de Werkzeug.
* Roles y permisos se cargan en sesion desde tablas de seguridad.
* `permiso_requerido()` protege rutas funcionales.
* `logs_sistema` registra eventos iniciales de login y administracion de usuarios.

El usuario `blizama` no se crea automaticamente en base de datos.

## Docker

Pendiente para Fase 11. La arquitectura ya evita rutas absolutas para facilitar portabilidad.
