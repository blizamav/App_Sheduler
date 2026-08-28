# Seguridad APP Scheduler v1.0.0

## Alcance

Este documento enumera controles implementados y validados durante QA. No es
una certificacion externa, no declara cumplimiento integral OWASP ni garantiza
ausencia de vulnerabilidades.

## Identidad y autorizacion

* autenticacion hibrida: `SUPER_ADMIN_ENV` y usuarios SQL;
* sesion minima sin roles/permisos completos serializados en cookie;
* cookie HttpOnly, SameSite configurable y Secure por ambiente;
* autorizacion backend por permiso en cada ruta sensible;
* CSRF global en mutaciones;
* errores de login genericos y registro auditable sin contrasenas.

La visibilidad de un boton no reemplaza la autorizacion del endpoint.

## Presentacion

* Jinja autoescape activo;
* contenido externo se trata como datos, no como HTML confiable;
* errores publicos no exponen SQL, connection strings o traceback;
* cabeceras defensivas configuradas por la aplicacion;
* no se usan dialogs nativos para confirmar acciones criticas.

## SQL Server

* valores mediante parametros `?` de pyodbc;
* identificadores dinamicos solo desde allowlists internas;
* unidades de trabajo con commit/rollback explicitos;
* cuenta ordinaria separada de mantenimiento;
* base permitida unica `APP_SCHEDULER_QA`;
* Factory Reset usa una cuenta dedicada con `db_owner` solo en esa base.

## Filesystem y subprocess

* roots de scripts, env y logs configuradas por ambiente;
* validacion canonica contra traversal y enlaces;
* upload `.py`/`.env` limitado por extension y tamano;
* descarga solo de archivos autorizados;
* subprocess con lista de argumentos y `shell=False`;
* `.env` de script se carga en memoria y su contenido no se muestra ni audita.

La salida stdout/stderr pertenece al script. Los scripts administrados no deben
imprimir secretos.

## Secretos

`.env` y `.env.docker` no se versionan ni se sobrescriben automaticamente. Las
plantillas contienen placeholders. Passwords SQL, admin, client secret y tokens
Graph no deben persistirse en BD, HTML, auditoria o logs.

Tenant/client ID y remitente no son secretos equivalentes al client secret,
pero la UI evita reproducir identificadores innecesariamente y permite
reemplazo controlado.

## Auditoria y logs

Acciones humanas relevantes se registran en `auditoria_cambios`; decisiones
automaticas en `scheduler_eventos`; ejecuciones y salida en sus tablas/logs
propios. Auditoria, ejecuciones y logs historicos no se borran desde Papelera.
La sanitizacion del logger conoce los secretos cargados por configuracion.

## Notificaciones

Graph usa endpoint fijo, timeout, TLS y client credentials del entorno. La
reserva at-most-once ocurre antes del HTTP y no existe retry automatico. El
correo evita stdout completo, stack trace, rutas privadas y variables de
entorno. Un fallo de notificacion no cambia el estado de ejecucion.

## Factory Reset

El reset requiere permiso dedicado, CSRF, preview firmado, doble confirmacion,
allowlist de target, lock, mantenimiento, SQLCMD, transaccion y cuarentena
filesystem. Es in-place y no tiene privilegios globales de servidor. Ante un
estado no confirmable falla cerrado.

## Validacion QA

Hito 14 cubrio login invalido, permisos/IDOR, CSRF, XSS, inyecciones,
confinamiento, symlinks, concurrencia, at-most-once, rollback Factory Reset y
Graph real controlado. No se conocen bloqueos criticos abiertos para v1.0.0.

## Limitacion operativa

Una caida abrupta del Worker durante `EN_EJECUCION` no produce auto-retry. La
restriccion evita duplicidad potencial y exige diagnostico antes de intervenir.
