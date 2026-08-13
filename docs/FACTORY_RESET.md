# Factory Reset

## Arquitectura vigente

Desde Fase 19F, Factory Reset opera **in-place** y de forma transaccional dentro de la unica base autorizada: `APP_SCHEDULER_QA`.

El diseno blue-green de Fases 19C-19E queda **DEPRECADO**. Ya no se crean, renombran ni eliminan bases `NEW`, `OLD` o `FAILED`; esas denominaciones solo describen el historial anterior y no pertenecen al flujo operativo vigente.

## Seguridad y autorizacion

La cuenta operativa normal es `user_scheduler`. Factory Reset utiliza una cuenta SQL separada de mantenimiento, configurada mediante `FACTORY_RESET_DB_USER`, que debe:

* poder conectarse al target autorizado;
* pertenecer a `db_owner` en `APP_SCHEDULER_QA`;
* no requiere `sysadmin`, `CREATE ANY DATABASE`, `ALTER ANY DATABASE`, `ALTER ANY CONNECTION` ni `processadmin`.

La cuenta SQL de mantenimiento no corresponde al usuario que inicia sesion en APP Scheduler. La password se entrega a SQLCMD solo mediante `SQLCMDPASSWORD`; no se incluye en argumentos, UI, logs ni tokens.

El precheck exige, antes de adquirir el lock externo:

* `FACTORY_RESET_HABILITADO=true`;
* SQLCMD disponible;
* `FACTORY_RESET_DB_TARGET` igual a `DB_DATABASE`;
* target incluido exactamente en `FACTORY_RESET_DB_ALLOWED_TARGETS`;
* conexion directa a la base objetivo;
* `DB_NAME()` coincidente, base `READ_WRITE` y cuenta miembro de `db_owner`;
* cero ejecuciones o procesos de scripts activos;
* lock externo disponible;
* roots filesystem seguros;
* `SUPER_ADMIN_ENV` disponible;
* manifiesto y runner in-place validos y sin cambios desde el preview.

## Runner SQL in-place

La fuente de orden es `database/factory_reset/manifest.json`. El runner unico es `database/factory_reset/000_reset_in_place.sql` y SQLCMD lo ejecuta en una sola conexion contra el target.

Secuencia SQL:

1. `:on error exit`, `SET XACT_ABORT ON` y timeout de locks.
2. Validar contexto, `READ_WRITE` y `db_owner`.
3. Abrir `BEGIN TRANSACTION`.
4. Adquirir `sp_getapplock` exclusivo con propietario `Transaction`.
5. Ejecutar `001_eliminar_esquema_aplicativo.sql`.
6. Reutilizar `002..011` del bootstrap oficial.
7. Ejecutar `100_validacion_bootstrap_actual.sql`.
8. Registrar `FACTORY_RESET_COMPLETADO` en log y auditoria de la instalacion nueva.
9. Ejecutar `COMMIT TRANSACTION` y emitir `FACTORY_IN_PLACE_COMMIT_OK`.

`database/release/001_crear_base_datos.sql` esta excluido. El runner no contiene `CREATE DATABASE`, `DROP DATABASE`, renombre de base, `KILL` ni conexion a `master`.

Los `GO` separan lotes dentro de la misma sesion SQLCMD; no crean conexiones nuevas. Ante error, `sqlcmd -b`, `:on error exit`, `XACT_ABORT` y el cierre de la conexion impiden declarar exito y revierten la transaccion no confirmada.

## Esquema reconstruido

`database/factory_reset/001_eliminar_esquema_aplicativo.sql` declara expresamente las 33 tablas conocidas. Antes de modificar, bloquea el reset si encuentra una tabla `dbo` desconocida o una FK que cruza el modelo conocido con un objeto desconocido.

El script elimina las FK conocidas y luego las 33 tablas en orden controlado. Indices, defaults, checks y constraints desaparecen con sus tablas. Se conservan:

* la base `APP_SCHEDULER_QA`;
* usuarios y roles de base;
* permisos de conexion;
* el esquema `dbo`;
* cualquier objeto desconocido, que provoca bloqueo en vez de eliminacion automatica.

Los scripts 002..011 reconstruyen las 33 tablas y seeds base. La validacion 100 exige `BOOTSTRAP_SQL=19C.0`, scheduler deshabilitado, Mail Graph inactivo y los conteos base esperados.

## Orquestacion y locks

El flujo vigente es:

1. `PRECHECK`.
2. `LOCK_ADQUIRIDO`.
3. `BLOQUEANDO_ACTIVIDAD`.
4. `CUARENTENA_FILESYSTEM`.
5. `ADQUIRIENDO_APPLOCK`.
6. `EJECUTANDO_RESET_IN_PLACE`.
7. `CONFIRMANDO_COMMIT`.
8. `VALIDANDO_RESULTADO`.
9. `LIMPIANDO_CUARENTENA`.
10. `COMPLETADO` o `ERROR`.

El lock externo en `RUTA_CONTROL_RUNTIME/factory_reset.lock` bloquea nuevas tareas en web y worker. El `sp_getapplock` protege la transaccion dentro de la base. No se cierran conexiones con `KILL`: una conexion que bloquee DDL provoca timeout, error y rollback.

## Filesystem y fallos

Antes de iniciar SQL, los roots `scripts`, `env_scripts`, `logs_tareas`, `logs_sistema` y `logs_worker` se copian a una cuarentena confinada y verificada por SHA-256. Luego los roots quedan creados y vacios.

* Fallo antes o durante SQL, sin marcador de commit: SQL Server revierte la transaccion y el orquestador restaura el filesystem anterior.
* Caida de SQLCMD antes del commit: el cierre de la unica sesion revierte la transaccion abierta.
* Commit confirmado: no se intenta restaurar SQL ni reintroducir archivos antiguos.
* Fallo posterior al commit: el lock queda en `FACTORY_RESET_ERROR` y exige revision manual.
* Exito completo: se valida la instalacion, se elimina la cuarentena y se libera el lock.

## UI y endpoints

Se mantienen doble confirmacion, frase exacta `RESTABLECER APP SCHEDULER`, CSRF, preview firmado, overlay, progreso real y polling.

Rutas:

* `GET /administracion/factory-reset`.
* `POST /administracion/factory-reset/preview`.
* `POST /administracion/factory-reset/ejecutar`.
* `GET /administracion/factory-reset/estado`.

La UI identifica el modo `IN_PLACE`, aclara que no se crean otras bases y distingue la cuenta SQL de mantenimiento del usuario de APP Scheduler.

## Diagnostico

Ante fallo SQLCMD se conserva, de forma sanitizada:

* script exacto alcanzado;
* return code;
* extracto de stdout/stderr.

Passwords, usuarios y servidor configurados se sustituyen antes de registrar o devolver el error.

## Validacion previa a uso real

La implementacion se valida con pruebas simuladas; estas no ejecutan SQL ni Factory Reset. Antes de habilitar QA se requiere una prueba controlada y respaldo externo de `APP_SCHEDULER_QA`, porque despues de un commit correcto no existe rollback automatico de datos.
