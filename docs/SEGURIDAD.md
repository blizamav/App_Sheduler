# Seguridad

## Manejo de sesiones

Fase 1 usa sesiones Flask protegidas por `APP_SECRET_KEY`.

## Roles y permisos

Fase 4 incorpora control inicial de roles y permisos desde SQL Server sin eliminar el acceso inicial desde `.env`.

Flujo vigente:

1. El login valida primero `USUARIO_ADMIN_DEFECTO` y `PASSWORD_ADMIN_DEFECTO` desde `.env`.
2. Si coincide, la sesion queda como `SUPER_ADMIN_ENV` con permisos totales.
3. Si no coincide, se valida contra la tabla `usuarios`.
4. Solo pueden iniciar sesion usuarios activos, no bloqueados y con contrasena valida.
5. Los permisos se cargan desde `usuarios_roles`, `roles`, `roles_permisos` y `permisos`.

El permiso funcional inicial para administrar usuarios es `USUARIOS_ADMIN`.

## Contrasenas

Las contrasenas de usuarios de base de datos se guardan usando hash seguro de Werkzeug:

* `generate_password_hash()` al crear o cambiar contrasena.
* `check_password_hash()` al iniciar sesion.

La aplicacion no muestra contrasenas en formularios ni respuestas.

## Administracion de usuarios

Fase 4 habilita `/usuarios` para usuarios con `USUARIOS_ADMIN` o administrador de `.env`.

Permitido:

* Listar usuarios.
* Filtrar usuarios por estado, rol y busqueda general.
* Crear usuarios.
* Editar nombre, email, rol, estado y contrasena opcional.
* Activar o desactivar usuarios.

No permitido:

* Eliminacion fisica de usuarios desde la app.
* Crear automaticamente el usuario `blizama` en base de datos.
* Exponer credenciales o hashes en pantalla.

Fase 4.2 usa modal corporativo propio antes de activar o desactivar usuarios. Si el administrador cancela, no se envia el formulario y no se registra evento como cambio realizado.

El formulario de edicion advierte cuando se cambia el rol o se ingresa una nueva contrasena. Estas advertencias no bloquean la accion, pero refuerzan claridad antes de guardar.

Las acciones criticas deben usar confirmacion explicita del sistema. No se deben usar `alert()`, `confirm()` ni `prompt()` nativos del navegador para acciones operativas.

Cambios de usuario que requieren confirmacion explicita:

* Crear usuario.
* Editar usuario.
* Cambiar rol.
* Cambiar estado activo/inactivo.
* Cambiar contrasena.
* Activar usuario.
* Deshabilitar usuario.

El cambio de contrasena se registra como evento sin guardar ni mostrar el valor de la contrasena ni su hash.

## Mantenedores base

Clientes, categorias y tipos usan permisos especificos por modulo:

* `CLIENTES_VER`, `CLIENTES_CREAR`, `CLIENTES_EDITAR`, `CLIENTES_ESTADO`
* `CATEGORIAS_VER`, `CATEGORIAS_CREAR`, `CATEGORIAS_EDITAR`, `CATEGORIAS_ESTADO`
* `TIPOS_VER`, `TIPOS_CREAR`, `TIPOS_EDITAR`, `TIPOS_ESTADO`

Desde Fase 5.1 existe eliminacion fisica controlada solo para registros sin dependencias en `tareas`.

Reglas:

* Si el registro no tiene dependencias, puede eliminarse definitivamente con modal `danger`.
* Si tiene dependencias, se bloquea la eliminacion y se sugiere desactivar.
* La eliminacion confirmada se registra en `logs_sistema`.
* El intento bloqueado tambien se registra en `logs_sistema` con nivel `WARNING`.
* Se usan permisos existentes de estado: `CLIENTES_ESTADO`, `CATEGORIAS_ESTADO`, `TIPOS_ESTADO`.
* No se modifican usuarios, tareas, scripts ni trazabilidad historica.

## Tareas

Fase 6 agrega permisos especificos:

* `TAREAS_VER`
* `TAREAS_CREAR`
* `TAREAS_EDITAR`
* `TAREAS_ESTADO`
* `TAREAS_ELIMINAR`

Reglas:

* Solo usuarios autorizados pueden acceder al modulo `/tareas`.
* Crear, editar, activar, desactivar y eliminar usan confirmacion por modal corporativo.
* La eliminacion fisica solo se permite si la tarea no tiene scripts, ejecuciones ni logs asociados.
* Si hay dependencias, se bloquea y se recomienda desactivar.
* No se ejecutan scripts ni procesos desde Fase 6.
* No se manipulan secretos ni `.env` de scripts desde Fase 6.

## Variables de entorno

Credenciales, servidores, rutas y secret keys deben vivir en `.env`. El archivo real se excluye con `.gitignore`.

Reglas obligatorias:

* `.env` contiene credenciales sensibles y configuracion privada por ambiente.
* `.env` nunca debe subirse a Git.
* `.env` nunca debe sobrescribirse automaticamente si ya existe.
* `.env.example` es solo una plantilla sin credenciales reales.
* Las credenciales reales deben configurarse manualmente por ambiente.
* No usar `copy .env.example .env` sobre un archivo `.env` existente.
* Usar comandos seguros, por ejemplo PowerShell: `if (!(Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host ".env ya existe. No se sobrescribe." }`.
* Si faltan variables criticas, la app debe mostrar advertencia controlada sin exponer valores.

## Scripts y versiones

Fase 7 agrega permisos especificos:

* `SCRIPTS_VER`
* `SCRIPTS_CREAR`
* `SCRIPTS_EDITAR`
* `SCRIPTS_VERSIONAR`
* `SCRIPTS_ACTIVAR_VERSION`
* `SCRIPTS_DESACTIVAR`
* `SCRIPTS_ELIMINAR`
* `SCRIPTS_ENV_GESTIONAR`

Reglas:

* Solo se aceptan archivos `.py` para scripts.
* Solo se aceptan archivos `.env` para variables por version.
* Se valida tamano maximo con `MAX_SCRIPT_SIZE_MB` y `MAX_ENV_SIZE_KB`.
* Los archivos se guardan solo bajo `scripts/` y `env_scripts/`.
* No se permiten rutas absolutas ni path traversal.
* No se ejecutan scripts en Fase 7.
* No se muestra contenido de `.env`.
* No se guardan secretos en base de datos.
* `scripts.nombre_script` es solo un nombre descriptivo de contenedor; no debe contener secretos ni rutas.
* Los nombres reales de archivos `.py` se guardan en `scripts_versiones.nombre_archivo`.
* La eliminacion fisica de versiones se bloquea si la version esta activa o tiene historial.
* La eliminacion de una version unica se bloquea para evitar dejar el contenedor de script sin versiones.
* El boton `Eliminar script completo` es la unica accion visual que puede afectar todo el conjunto de versiones.
* El boton `Eliminar version` solo puede afectar la version de su fila; no elimina otras versiones ni el script completo.
* Todo bloqueo por version activa, version unica o historial se registra en `logs_sistema` con nivel `WARNING`.

## Ejecucion manual

Fase 8 agrega permisos:

* `EJECUCIONES_VER`.
* `EJECUCIONES_EJECUTAR`.
* `EJECUCIONES_DETENER`.
* `EJECUCIONES_LOG_VER`.

Reglas:

* La ejecucion manual usa siempre la version activa.
* No se usa `shell=True`.
* Se ejecuta con el interprete Python actual.
* Se bloquea una segunda ejecucion si la misma tarea ya esta `EN_EJECUCION`.
* Si la version requiere `.env`, el archivo debe existir antes de iniciar.
* El `.env` se carga al entorno del proceso sin mostrar ni registrar contenido.
* El log de consola puede contener lo que imprima el script; los scripts no deben imprimir secretos.
* La detencion requiere permiso `EJECUCIONES_DETENER` y modal corporativo.
* La detencion registra usuario, fecha, motivo y si fue forzada.

Validacion local:

* `006_permisos_ejecuciones.sql` fue ejecutado correctamente en SQL Server local.
* Se valido que la ejecucion con `.env` de prueba carga variables mediante `os.getenv()` sin mostrar contenido sensible.
* La consola mostro stdout del script y no expuso secretos.
* La detencion manual registro estado `DETENIDA_MANUALMENTE` y PID asociado.
* No se implemento scheduler automatico ni API de feriados.

## Configuracion scheduler

Fase 9A agrega permisos:

* `SCHEDULER_CONFIG_VER`.
* `SCHEDULER_CONFIG_EDITAR`.

Reglas:

* La configuracion operativa vive en SQL Server.
* `.env` queda para configuracion tecnica del ambiente y secretos minimos.
* Scheduler queda apagado por defecto.
* La ejecucion automatica queda deshabilitada por defecto.
* Cambios requieren modal corporativo.
* Cambios se registran en `logs_sistema`.
* No se inicia worker automatico en Fase 9A.
* No se ejecutan tareas automaticas en Fase 9A.
* No se conecta API de feriados.

Validacion local:

* `010_crear_configuracion_scheduler.sql` y `007_permisos_scheduler.sql` fueron ejecutados correctamente en SQL Server local.
* La configuracion inicia con defaults seguros: scheduler apagado y ejecucion automatica deshabilitada.
* La pantalla `/scheduler/configuracion` exige permisos `SCHEDULER_CONFIG_VER` y `SCHEDULER_CONFIG_EDITAR`.
* Los cambios se confirman con modal corporativo y se registran en `logs_sistema`.
* Las validaciones bloquean intervalos y maximos concurrentes fuera de rango.

## Panel operativo scheduler

Fase 11A reutiliza permiso:

* `SCHEDULER_CONFIG_VER`.

Reglas:

* `/scheduler/panel` es solo lectura.
* No permite iniciar, detener ni reiniciar el worker.
* No edita configuracion operativa.
* No consulta APIs externas.
* No muestra secretos ni rutas sensibles de scripts.
* La configuracion sigue editandose en `/scheduler/configuracion` con `SCHEDULER_CONFIG_EDITAR`.

Fase 11B agrega heartbeat del worker:

* El panel muestra estado de `scheduler_worker.py` desde `scheduler_worker_heartbeat`.
* No permite iniciar, detener ni reiniciar el worker.
* No expone credenciales, `.env`, rutas privadas ni contenido de scripts.
* `logs_sistema` no recibe un registro por cada heartbeat para evitar crecimiento innecesario.
* `logs_sistema` solo registra inicio, detencion, error, recuperacion o fallo al actualizar heartbeat.

## Worker automatico

Fase 9B agrega ejecucion automatica con estas reglas de seguridad:

* El worker corre separado de Flask con `python scheduler_worker.py`.
* Usa `.env` solo para conexion BD y rutas tecnicas.
* La configuracion operativa se lee desde `configuracion_scheduler`.
* No muestra secretos de `.env` principal ni `.env` de scripts.
* Reutiliza ejecucion segura de Fase 8 con `subprocess` sin `shell=True`.
* Las ejecuciones automaticas guardan `clave_programacion` para evitar duplicados.
* El worker respeta `max_ejecuciones_concurrentes`.
* Si una tarea ya tiene ejecucion `EN_EJECUCION`, no inicia otra.
* Las ejecuciones automaticas pueden detenerse desde la consola web con permisos existentes.
* No se conecta API de feriados en Fase 9B.
* No se implementan notificaciones en Fase 9B.
* El heartbeat de Fase 11B no cambia permisos ni permite control operativo del proceso desde la app.

## Logs de ejecucion con timestamp

Fase 9C agrega formato unico por linea en logs de ejecucion:

```text
YYYY-MM-DD HH:mm:ss | NIVEL | mensaje
```

Reglas de seguridad:

* No se muestra contenido de `.env`.
* No se registran credenciales desde la plataforma.
* La salida stdout/stderr del script se conserva, pero los scripts no deben imprimir secretos.
* Errores de plataforma se registran como `ERROR`.
* Detenciones manuales se registran como `WARN`.
* Si el script imprime un timestamp propio, se antepone timestamp de plataforma para asegurar trazabilidad real de captura.

## Historial de ejecuciones

Fase 9D mantiene permisos existentes:

* `EJECUCIONES_VER` para ver `/ejecuciones`.
* `EJECUCIONES_LOG_VER` para polling de log.
* `EJECUCIONES_DETENER` para detener ejecuciones.

Reglas:

* Filtros se aplican con parametros SQL, sin concatenar valores de usuario.
* La paginacion se hace en SQL Server con `OFFSET/FETCH`.
* La agrupacion se hace solo sobre la pagina actual.
* No se muestran rutas fisicas internas en el historial.
* No se muestra contenido de `.env`.

## Feriados locales

Fase 10A agrega permisos:

* `FERIADOS_VER`.
* `FERIADOS_CREAR`.
* `FERIADOS_EDITAR`.
* `FERIADOS_ESTADO`.
* `FERIADOS_ELIMINAR`.

Reglas:

* La tabla local `feriados` es la fuente de verdad para el scheduler.
* No se consume API externa ni se sincronizan datos externos en Fase 10A.
* Los filtros y guardado usan parametros SQL desde repositorio.
* Crear, editar, activar/desactivar y eliminar usan permisos especificos.
* Los cambios e intentos relevantes se registran en `logs_sistema`.
* La ejecucion manual no se bloquea por feriados.
* El worker omite tareas automaticas en feriado solo cuando `ejecutar_en_feriados = 0`.

Validacion local:

* Migracion 012 y seed 008 ejecutados correctamente en SQL Server local.
* Permisos `FERIADOS_*` insertados.
* Acceso `/feriados` validado.
* Crear, editar, activar/desactivar y bloqueo de duplicado fecha + pais activa validados.
* No se conecto API externa ni sincronizacion automatica.

## Sincronizacion Nager.Date

Fase 10B agrega permiso:

* `FERIADOS_SINCRONIZAR`.

Reglas:

* Solo usuarios autorizados pueden abrir `/feriados/sincronizar`.
* La consulta externa usa timeout y errores controlados.
* El scheduler no consulta Nager.Date ni internet.
* La API externa no sobrescribe feriados `MANUAL`.
* Feriados inactivos no se reactivan automaticamente.
* La aplicacion muestra vista previa antes de insertar o actualizar.
* La confirmacion usa modal corporativo; no se usan `alert()`, `confirm()` ni `prompt()`.
* Los cambios se registran en `logs_sistema`.
* No se registran secretos.

## Variables sensibles por script

Fase 4.3 define que cada script/version podra tener un `.env` propio bajo `env_scripts/`.

Reglas:

* No mostrar secretos en pantalla.
* No guardar secretos en base de datos.
* No registrar secretos en logs.
* No subir `.env` principal ni `.env` de scripts a Git.
* Separar `.env` principal de la app y `.env` de scripts.
* Guardar en base solo rutas fisicas/relativas del `.env` de script.
* Validar rutas para evitar path traversal.
* Solo usuarios autorizados podran cargar o modificar `.env` de scripts.
* Si una version requiere `.env` y falta el archivo, la ejecucion debe fallar controladamente antes de iniciar el proceso.

## Detencion de ejecuciones

Solo usuarios autorizados podran detener ejecuciones. Toda detencion debe:

* Pedir confirmacion mediante modal corporativo.
* Registrar usuario, fecha/hora y motivo cuando aplique.
* Registrar evento en `logs_sistema`.
* Registrar resultado en `logs_tareas`.
* Actualizar `ejecuciones`.
* No exponer datos sensibles del proceso ni variables de entorno.

## Eliminacion controlada de scripts

La eliminacion fisica desde la app solo se permite de forma controlada cuando no existe historial operativo asociado.

Reglas:

* `Eliminar script completo` afecta el contenedor de script y todas sus versiones, solo si no tienen historial.
* `Eliminar version` afecta solo una version especifica y no toca las demas.
* Si una version esta activa, se debe activar otra antes de eliminarla.
* Si una version es la unica del script, se debe usar `Eliminar script completo`.
* Si existe historial en ejecuciones o logs, se bloquea la eliminacion fisica y se recomienda desactivar.
* Al eliminar una version sin historial se eliminan tambien su archivo `.py` y `.env` asociado, si existen.
* No se muestra ni registra contenido de `.env`.

Los estados vigentes para versiones siguen siendo:

* `ACTIVA`
* `DISPONIBLE`
* `REEMPLAZADA`
* `INACTIVA`

Toda eliminacion, inactivacion, reemplazo o bloqueo debe registrarse en logs de sistema.

## Validacion de rutas

No se deben quemar rutas absolutas. Toda ruta operativa debe venir desde `.env`.

## Logs seguros

Fase 4 agrega registro inicial en `logs_sistema` para:

* Login exitoso.
* Login fallido.
* Login bloqueado por usuario inactivo o bloqueado.
* Creacion de usuario.
* Edicion de usuario.
* Activacion o desactivacion de usuario.
* Cambio de rol de usuario.

Los logs no deben exponer passwords, hashes ni credenciales de conexion.

## Recomendaciones

Cambiar `APP_SECRET_KEY` y `PASSWORD_ADMIN_DEFECTO` antes de ejecutar en entornos compartidos.
