# Arquitectura

## Arquitectura general

APP Scheduler es una aplicacion Flask modular con fabrica `crear_app()`, configuracion centralizada, rutas por Blueprint, capa de repositorios, capa de servicios y proceso worker separado para ejecucion automatica.

Estado actual: Fase 14B.1 deja implementado el buffer visual limitado del worker. El roadmap formal desde esta reorganizacion queda en `docs/ROADMAP.md`.

## Capas del sistema

* Presentacion: templates HTML y assets CSS/JS.
* Aplicacion: rutas Flask y control de sesion.
* Configuracion: lectura de `.env`.
* Datos: SQL Server mediante `pyodbc` y repositorios dedicados.
* Servicios: reglas de negocio para usuarios, mantenedores, tareas, scripts, ejecuciones, programador, feriados, paneles, eventos, borrado operativo y auditoria.
* Worker: `scheduler_worker.py` como proceso separado para evaluacion automatica.
* Logging worker: `app/servicios/servicio_logging_worker.py` para salida estructurada a terminal y buffer visual acotado.
* Trazabilidad operativa: `logs_sistema`, `logs_tareas`, `ejecuciones`, `scheduler_worker_heartbeat` y `scheduler_eventos`.
* Auditoria: `auditoria_cambios`, servicio central `registrar_auditoria(...)` y modulo `/auditoria` implementados desde Fase 12A.

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
* `app/rutas_feriados.py`
* `app/seguridad.py`
* `app/database/conexion.py`
* `app/repositorios/`
* `app/servicios/`

## Frontend

HTML/CSS/JS sin Streamlit. Desde Fase 2 el layout incluye login corporativo, sidebar responsive, topbar con usuario, tarjetas de metricas, tabla base, badges de estado y panel lateral visual preparado para logs.

La capa visual mantiene el diseno de Fase 2. Desde Fase 11A.1 el panel principal consume metricas reales de SQL Server mediante repositorio y servicio dedicados; las pantallas `/usuarios`, `/clientes`, `/categorias`, `/tipos`, `/tareas`, `/ejecuciones`, `/feriados` y `/scheduler` consumen datos reales segun permisos.

## Base de datos

SQL Server sera incorporado desde Fase 3. Base objetivo: `APP_SCHEDULER_QA`, configurable por `.env`.

En Fase 3B se crearon scripts SQL versionados bajo `database/migrations/` y `database/seeds/`. Estos scripts no se ejecutan automaticamente. Desde Fase 3D Flask se conecta a SQL Server mediante `pyodbc` y desde fases posteriores la persistencia queda aislada en repositorios/servicios para evitar consultas SQL directas desde rutas Flask.

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

Fase 11F agrega borrado operativo seguro con snapshots:

* `database/migrations/016_agregar_snapshots_historial_borrado_operativo.sql`: agrega snapshots y campos `eliminado_operativo`.
* Repositorios de tareas, scripts, usuarios y mantenedores: deciden entre eliminacion fisica y retiro operativo.
* Repositorios de ejecuciones y eventos del programador: leen `COALESCE(snapshot, maestro)` para historial legible.
* Panel y scheduler: excluyen registros retirados de operacion normal.

Regla arquitectonica: las tablas historicas no deben depender solo del registro maestro para mostrar nombres. No se usan cascadas destructivas sobre `ejecuciones`, `logs_tareas`, `logs_sistema`, `scheduler_eventos` ni `auditoria_cambios`.

Fase 8 agrega capa de ejecucion manual:

* `app/rutas_ejecuciones.py`: endpoints para iniciar, ver consola, consultar log y detener.
* `app/repositorios/repositorio_ejecuciones.py`: persistencia en `ejecuciones` y `logs_tareas`.
* `app/servicios/servicio_ejecuciones.py`: validaciones, creacion de ejecucion, archivo de log y actualizacion de estado.
* `app/servicios/servicio_env_scripts.py`: carga segura de `.env` por version.
* `app/servicios/servicio_procesos.py`: inicio y detencion de procesos.

La ejecucion manual usa `subprocess` sin `shell=True`, registra PID y captura stdout/stderr hacia archivo. La consola se actualiza por polling HTTP cada 3 segundos.

Control de ejecuciones huerfanas:

* El lanzamiento de scripts ocurre en `app/servicios/servicio_procesos.py` mediante `subprocess.Popen`.
* El PID se guarda en `ejecuciones.pid_proceso`.
* El monitoreo del termino depende de un hilo en memoria iniciado desde `servicio_ejecuciones.py`.
* Si el proceso Flask se reinicia, el hilo monitor se pierde y una ejecucion puede quedar `EN_EJECUCION` aunque el proceso hijo ya no exista.
* `app/servicios/servicio_control_ejecuciones.py` permite verificar el PID y marcar como `ERROR` una ejecucion huerfana sin matar procesos.

Fase 9A agrega configuracion operativa del scheduler:

* `app/rutas_scheduler.py`: pantalla `/scheduler/configuracion`.
* `app/repositorios/repositorio_configuracion_scheduler.py`: lectura y actualizacion de configuracion activa.
* `app/servicios/servicio_configuracion_scheduler.py`: validaciones y logs.
* `app/templates/scheduler/configuracion.html`: UI administrativa.

La configuracion operativa vive en SQL Server. `.env` queda reservado para configuracion tecnica del ambiente. Desde Fase 9B el worker automatico es un proceso separado y lee estos parametros desde base de datos.

Fase 9B agrega worker automatico separado:

* `scheduler_worker.py`: proceso independiente ejecutado con `python scheduler_worker.py`.
* `app/servicios/servicio_scheduler_worker.py`: ciclo del worker, lectura de configuracion y control de concurrencia.
* `app/servicios/servicio_programador.py`: evaluacion testeable de programaciones.
* `app/repositorios/repositorio_scheduler.py`: consulta de tareas programadas activas y control de claves.
* `app/servicios/servicio_calendario.py`: consulta calendario local de feriados desde SQL Server.

La app web no levanta el worker dentro del proceso Flask. La web administra configuracion, consola y detencion; el worker evalua programaciones y reutiliza `servicio_ejecuciones.py` para ejecutar scripts.

Fase 10A agrega calendario local de feriados:

* `app/rutas_feriados.py`: modulo `/feriados`.
* `app/repositorios/repositorio_feriados.py`: persistencia de tabla `feriados`.
* `app/servicios/servicio_calendario.py`: reglas `es_feriado`, `obtener_feriado`, `validar_fecha_laboral` y administracion.
* `app/templates/feriados/`: listado y formulario.

La tabla local `feriados` es la fuente de verdad del scheduler. No se consulta API externa en tiempo real.

Fase 10B agrega sincronizacion controlada desde Nager.Date:

* `app/servicios/cliente_nager_date.py`: cliente HTTP con timeout y errores controlados.
* `app/servicios/servicio_sincronizacion_feriados.py`: preview, clasificacion y aplicacion.
* `app/repositorios/repositorio_reglas_feriados.py`: reglas locales de irrenunciables.
* `/feriados/sincronizar`: pantalla manual con vista previa antes de guardar.

La API externa solo se consulta desde el modulo de sincronizacion manual. El scheduler mantiene dependencia exclusiva de SQL Server mediante `servicio_calendario.es_feriado()`.

Fase 11A agrega panel operativo del scheduler:

* `app/repositorios/repositorio_panel_scheduler.py`: consultas de solo lectura para monitoreo.
* `app/servicios/servicio_panel_scheduler.py`: consolida configuracion, ejecuciones, errores, candidatas y feriados.
* `/scheduler/panel`: dashboard operativo.

El panel no inicia, detiene ni reinicia el worker. Solo muestra datos existentes en SQL Server.

Fase 11B agrega heartbeat del worker:

* `database/migrations/014_crear_scheduler_worker_heartbeat.sql`: tabla `scheduler_worker_heartbeat`.
* `app/repositorios/repositorio_worker_heartbeat.py`: persistencia de senal de vida.
* `app/servicios/servicio_worker_heartbeat.py`: registro de inicio, ciclo, error, detencion y clasificacion visual.
* `app/servicios/servicio_scheduler_worker.py`: integra actualizacion de heartbeat sin cambiar el modelo de ejecucion automatica.
* `/scheduler/panel`: muestra estado del worker, ultimo heartbeat, ultimo ciclo, PID, host y contadores del ultimo ciclo.

Fase 14B.1 agrega buffer visual limitado del worker:

* `app/servicios/servicio_logging_worker.py`: configura logger dedicado `app_scheduler.worker`.
* `scheduler_worker.py`: inicializa el logger antes de levantar contexto Flask.
* `app/servicios/servicio_scheduler_worker.py`: usa logging estructurado en lugar de `print()`.
* `app/servicios/servicio_worker_heartbeat.py`: agrega trazas operativas de heartbeat al mismo logger.
* `logs/worker_console.log`: archivo local unico como buffer visual reciente para futura lectura segura.

Formato vigente:

```text
YYYY-MM-DD HH:mm:ss | NIVEL | ORIGEN | mensaje
```

Politica vigente del buffer:

* archivo unico
* maximo 300 lineas
* reinicio por nueva sesion del worker
* sin backups rotativos

Fase 11D agrega eventos del programador:

* `database/migrations/015_crear_eventos_programador.sql`: tabla `scheduler_eventos`.
* `app/repositorios/repositorio_scheduler_eventos.py`: insercion y consulta de eventos recientes.
* `app/servicios/servicio_scheduler_eventos.py`: normaliza eventos de ciclo, ejecucion, omision y error sin exponer datos sensibles.
* `app/servicios/servicio_scheduler_worker.py`: registra decisiones relevantes del ciclo automatico.
* `/scheduler/panel`: muestra eventos recientes del programador.

Esta capa es solo trazabilidad operativa. Una omision no crea `ejecuciones`, no crea `logs_tareas` y no reemplaza auditoria funcional.

El heartbeat vive en una tabla dedicada porque cambia frecuentemente. `logs_sistema` solo registra eventos relevantes: inicio, detencion, error, recuperacion o fallo al actualizar heartbeat.

Distincion con Auditoria:

* `scheduler_eventos` registra decisiones automaticas del programador.
* `ejecuciones` registra intentos reales de ejecucion.
* `logs_sistema` registra eventos operativos basicos.
* Ninguno de esos componentes reemplaza `auditoria_cambios`.
* Auditoria funcional queda implementada como base en Fase 12A y debe ampliarse en Fase 12B.

La FK `scripts.id_version_activa -> scripts_versiones.id_version` se agrega en `006_crear_indices.sql` por dependencia circular entre `scripts` y `scripts_versiones`.

## Scheduler

Desde Fase 9B el scheduler automatico corre como proceso separado. Se inicia con:

```powershell
python scheduler_worker.py
```

Reglas principales:

* Lee `configuracion_scheduler` desde SQL Server.
* Si `scheduler_activo = 0`, no evalua tareas.
* Si `modo_mantenimiento = 1`, no inicia ejecuciones.
* Si `permitir_ejecucion_automatica = 0`, no ejecuta tareas.
* Respeta `intervalo_revision_segundos`.
* Respeta `max_ejecuciones_concurrentes`.
* Respeta `ejecutar_en_feriados` consultando la tabla local `feriados`.
* Evita duplicados con `clave_programacion`.
* Reutiliza el motor de Fase 8 para version activa, `.env`, PID, logs y consola.
* Desde Fase 11A puede monitorearse en `/scheduler/panel`, sin control operacional del proceso.
* Desde Fase 11B registra heartbeat en `scheduler_worker_heartbeat`.

## Operacion worker Fase 14A y 14B

Decision arquitectonica: el worker no debe ejecutarse dentro del proceso Flask.

Diseno correcto:

```text
Proceso web:    python run.py
Proceso worker: python scheduler_worker.py
```

Motivos:

* Evitar duplicidad por debug/reloader de Flask.
* Separar caidas de web y worker.
* Facilitar monitoreo y reinicio.
* Mantener operacion profesional en QA/Produccion.

Recomendacion operativa:

* Desarrollo local: ejecucion manual controlada.
* QA/Produccion: proceso worker separado.
* Preferencia: Docker Compose con servicios `web` y `worker`.
* Alternativa: `systemd` si se despliega directamente en Ubuntu sin Docker.

La app web debe monitorear al worker mediante fuentes controladas:

* `scheduler_worker_heartbeat` para estado de vida.
* `configuracion_scheduler` para estado del scheduler.
* `scheduler_eventos` para eventos importantes.
* `logs/worker_console.log` como salida operativa persistida inicial para mostrar una consola visual equivalente a terminal en fase posterior.

El panel lateral abierto desde el boton `Logs` podra evolucionar a una consola visual del worker. Esa consola no debe ser una terminal real: no debe ejecutar comandos, no debe acceder al Docker socket, no debe mostrar secretos y no debe iniciar/detener procesos en Fase 14A ni 14B.

Diseno detallado: `docs/OPERACION_WORKER.md`.

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

Fase 9C estandariza cada linea visible de log de ejecucion con:

```text
YYYY-MM-DD HH:mm:ss | NIVEL | mensaje
```

La logica vive en `app/servicios/servicio_logs_ejecucion.py` y aplica a ejecuciones manuales, automaticas, consola web, polling y archivo fisico. La salida `stderr` se combina con `stdout` desde `servicio_procesos.py`; por eso la salida normal del script queda como `INFO`, mientras errores de plataforma y estados finales fallidos quedan como `ERROR`.

## Seguridad

Fase 4 usa login hibrido:

* Primero valida el administrador inicial desde `.env`.
* Si no coincide, valida usuarios activos en SQL Server.
* Las contrasenas de base de datos usan hash de Werkzeug.
* Roles y permisos se cargan en sesion desde tablas de seguridad.
* `permiso_requerido()` protege rutas funcionales.
* `logs_sistema` registra eventos iniciales de login y administracion de usuarios.

El usuario `blizama` no se crea automaticamente en base de datos.

## Roadmap arquitectonico

Siguiente bloque recomendado: implementar Fase 14C con endpoints de solo lectura y consola visual real del worker, manteniendo web y worker separados.

Bloques posteriores:

* Fase 12: Auditoria.
* Fase 13: release, instalacion limpia y checklist de despliegue.
* Fase 14: operacion avanzada del worker, monitoreo y servicios.

La arquitectura ya evita rutas absolutas para facilitar portabilidad. Docker Compose, systemd y worker como servicio quedan pendientes de implementacion posterior; Fase 14A deja el diseno operativo formal, Fase 14B implementa una primera version y Fase 14B.1 la corrige hacia buffer visual limitado.

## Release SQL limpio

Desde Fase 13A existe `database/release/` como paquete consolidado para instalar `APP_SCHEDULER_QA` desde cero.

Contenido:

* Creacion de base de datos.
* Esquema final consolidado.
* Seeds base de roles, permisos, catalogos, configuracion inicial y reglas de feriados.
* Script de validacion solo lectura.

La carpeta `database/migrations/` conserva el historial incremental de desarrollo. Para instalaciones nuevas se debe usar `database/release/` y no repetir manualmente toda la cadena historica de migraciones salvo que se trate de una actualizacion incremental de un ambiente existente.

El release no contiene usuarios reales, credenciales, servidores, rutas locales, tareas, scripts, ejecuciones, logs historicos ni auditoria historica.

## Retencion controlada de eventos scheduler

Desde Fase 13A.1 la tabla `scheduler_eventos` se usa para hechos relevantes del programador. La capa `servicio_scheduler_eventos.py` filtra eventos ruidosos antes de persistirlos:

* `CICLO_INICIADO`.
* `CICLO_FINALIZADO`.
* `TAREA_OMITIDA` con motivo `FUERA_DE_VENTANA`.

La limpieza manual desde `/scheduler/eventos` ejecuta borrado fisico controlado solo sobre `scheduler_eventos` y solo para esos eventos informativos antiguos. No toca tablas historicas ni operativas como `ejecuciones`, `logs_tareas`, `logs_sistema`, `auditoria_cambios` o `scheduler_worker_heartbeat`.

No se agrego schema nuevo ni permiso nuevo; se reutiliza `SCHEDULER_CONFIG_EDITAR`.

Fase 13A.1B amplia esta capa con limpieza parametrizable:

* `servicio_scheduler_eventos.py` define `CATEGORIAS_LIMPIEZA` como whitelist backend.
* `repositorio_scheduler_eventos.py` recibe condiciones internas ya validadas, no valores libres del usuario.
* `/scheduler/eventos/limpiar/previsualizar` calcula conteos con la misma logica segura que la eliminacion.
* `/scheduler/eventos/limpiar` recalcula el alcance antes de ejecutar `DELETE`.
* La UI solo envia claves de categoria; el backend decide su traduccion SQL.
