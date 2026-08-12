# Factory Reset

## Estado

Fase 19D implementa el orquestador real de Factory Reset con defensa fail-closed. El endpoint destructivo existe, pero permanece inutilizable mientras `FACTORY_RESET_HABILITADO=false` o falte cualquier prerrequisito administrativo.

Fase 19D.1 valido el flujo contra SQL Server real exclusivamente sobre bases `APP_SCHEDULER_FACTORY_*` y roots de `%TEMP%`. Se comprobaron dos resets consecutivos, blue-green, conservacion `OLD`, auditoria inicial, login `SUPER_ADMIN_ENV`, rollback post intercambio, fallo bootstrap aislado y rechazo de una sesion ajena sin cerrarla. `APP_SCHEDULER_QA` y `APP_SCHEDULER` no fueron targets ni se modificaron. La validacion tecnica no reemplaza una autorizacion operativa explicita para QA o produccion.

## Autorización y confirmaciones

Solo `SUPER_ADMIN` o `SUPER_ADMIN_ENV` con `FACTORY_RESET_EJECUTAR` o permiso global `*` puede acceder. El backend exige:

* sesión privilegiada vigente;
* CSRF válido y consumible;
* preview firmado vigente y perteneciente al usuario actual;
* hash del preview coincidente;
* frase exacta `RESTABLECER APP SCHEDULER`;
* lock disponible;
* manifiesto sin cambios desde el preview;
* `SUPER_ADMIN_ENV` disponible;
* cero ejecuciones y procesos de scripts activos;
* credencial SQL administrativa y SQLCMD disponibles;
* target administrativo idéntico a `DB_DATABASE`.

Rutas:

* `GET /administracion/factory-reset`.
* `POST /administracion/factory-reset/preview`.
* `POST /administracion/factory-reset/ejecutar`.
* `GET /administracion/factory-reset/estado`.

No existe variante GET del endpoint destructivo.

## Kill switch y credencial administrativa

La conexión normal de APP Scheduler no requiere permisos `CREATE DATABASE`, `ALTER DATABASE` ni `DROP DATABASE`. El orquestador usa SQLCMD con una credencial externa separada. La contraseña se entrega al proceso exclusivamente mediante `SQLCMDPASSWORD`; no aparece en argumentos, logs, UI, token ni BD.

```env
FACTORY_RESET_HABILITADO=false
FACTORY_RESET_DB_TARGET=
FACTORY_RESET_DB_SERVER=
FACTORY_RESET_DB_USER=
FACTORY_RESET_DB_PASSWORD=
FACTORY_RESET_DB_ENCRYPT=no
FACTORY_RESET_DB_TRUST_SERVER_CERTIFICATE=yes
FACTORY_RESET_SQLCMD=sqlcmd
FACTORY_RESET_SQLCMD_TIMEOUT_SEGUNDOS=900
FACTORY_RESET_APP_NAME_PREFIX=APP_SCHEDULER
```

`FACTORY_RESET_DB_TARGET` debe coincidir exactamente con `DB_DATABASE`. No configurar ni habilitar estas variables hasta disponer de una base desechable y una autorización específica.

## Lock y estados

El lock externo continúa en `RUTA_CONTROL_RUNTIME/factory_reset.lock` y se comparte entre web y worker. Registra estado, fase, progreso, PID, host, origen y `operation_id`, sin secretos.

Fases del orquestador:

1. `PRECHECK`.
2. `LOCK_ADQUIRIDO`.
3. `BLOQUEANDO_ACTIVIDAD`.
4. `CREANDO_BD_TEMPORAL`.
5. `EJECUTANDO_BOOTSTRAP`.
6. `VALIDANDO_BD_TEMPORAL`.
7. `PREPARANDO_INTERCAMBIO`.
8. `INTERCAMBIANDO_BD`.
9. `LIMPIANDO_FILESYSTEM`.
10. `VALIDANDO_RESULTADO`.
11. `REGISTRANDO_RESET`.
12. `COMPLETADO`, `ROLLBACK` o `ERROR`.

El worker no inicia tareas con lock. Durante intercambio, limpieza, validación y rollback tampoco consulta heartbeat SQL. El middleware web responde `503` a rutas ajenas al control de Factory Reset mientras exista lock.

Un lock dudoso, expirado o en error nunca se libera automáticamente.

## Bootstrap

`database/bootstrap/manifest.json` es la única fuente de orden. Python no mantiene una lista duplicada. El preview y el recálculo final verifican:

* versión y orden;
* orden inicial 1 y validación 100 al final;
* rutas confinadas al repositorio;
* archivos SQL existentes;
* ausencia de duplicados;
* hash SHA-256 conjunto del manifiesto y todos sus scripts.

El token firmado incluye ese hash. Si cualquier script cambia después del preview, el reset se rechaza.

## Blue-green SQL

El reset no destruye primero la base actual. Para un `operation_id` genera nombres únicos:

* `<ACTUAL>__FACTORY_NEW_<ID>`.
* `<ACTUAL>__FACTORY_OLD_<ID>`.
* `<ACTUAL>__FACTORY_FAILED_<ID>` para rollback.

Secuencia:

1. confirmar que la base actual existe y que NEW/OLD/FAILED no existen;
2. ejecutar todos los scripts del manifiesto sobre NEW;
3. ejecutar y validar el script 100 sobre NEW;
4. rechazar cualquier sesión SQL ajena a APP Scheduler;
5. cerrar únicamente sesiones identificadas por `DB_APPLICATION_NAME=APP_SCHEDULER`;
6. renombrar ACTUAL a OLD y NEW al nombre oficial;
7. conservar OLD;
8. validar nuevamente script 100 sobre el nombre oficial.

No se implementó `DROP DATABASE`. NEW fallida, OLD y FAILED se conservan para diagnóstico o rollback controlado.

## Filesystem y rollback

Roots operativos:

* `scripts/`;
* `env_scripts/`;
* `logs/`;
* `logs_tareas/`;
* `logs_sistema/`.

Cada árbol se valida sin symlinks, traversal, roots duplicados ni contención entre roots. Antes de limpiar se copia a:

`RUTA_CONTROL_RUNTIME/factory_backups/<OPERATION_ID>/<ROOT>`

La copia y el origen se comparan mediante SHA-256 de rutas y contenido. Solo después se elimina el contenido interno confinado. Los roots permanecen creados y vacíos. La cuarentena se conserva en 19D para rollback y no se elimina automáticamente.

Si falla filesystem o una validación posterior, el orquestador restaura la cuarentena y recupera OLD como nombre oficial. Si el rollback no puede confirmarse, el lock queda `FACTORY_RESET_ERROR` y exige intervención manual.

## Log externo y auditoría nueva

Durante la operación se generan archivos sin secretos:

* `factory_reset_<ID>.jsonl` con transiciones;
* `factory_reset_<ID>.estado.json` con último estado;
* `factory_reset_last_success.json` con la marca global de sesión.

Después de validar BD y filesystem, la nueva instalación recibe sus primeros registros `FACTORY_RESET_COMPLETADO` en `logs_sistema` y `auditoria_cambios`. Se registra identidad segura, origen ENV/BD, `operation_id` y versión de app.

La marca externa invalida todas las sesiones creadas antes del reset en su siguiente request. La sesión iniciadora se limpia inmediatamente y se redirige a `/login`.

## Pruebas Fase 19D

La suite `tests/test_factory_reset_19d.py` cubre con roots temporales y motor SQL simulado:

* reset completo y segundo reset;
* ejecución activa;
* lock concurrente;
* fallo bootstrap sin tocar la original;
* fallo de intercambio con rollback;
* fallo filesystem con rollback SQL;
* path traversal;
* autorización, CSRF, frase y token vencido;
* worker sin SQL durante intercambio;
* contraseña fuera de argumentos SQLCMD;
* rechazo de sesión SQL ajena;
* bloqueo web e invalidación de sesiones;
* estado externo de progreso.

Resultado local aislado: 14 pruebas aprobadas, incluida restauracion ante limpieza filesystem parcial y contrato POST exclusivo con invalidacion de sesion.

Resultado SQL real Fase 19D.1:

* `sqlcmd` (Go) oficial Microsoft `v1.10.0`, ejecutado de forma portatil desde `%TEMP%` y con SHA-256 verificado;
* bootstrap `19C.0` y validacion 100 correctos;
* primer y segundo reset correctos sobre `APP_SCHEDULER_FACTORY_SOURCE_TEST`;
* dos bases `OLD` conservadas y online;
* roots temporales vacios tras ambos resets;
* `FACTORY_RESET_COMPLETADO` como primer registro de auditoria en cada instalacion nueva;
* login `SUPER_ADMIN_ENV` correcto;
* rollback real con datos y archivos restaurados;
* fallo bootstrap antes del intercambio con `SOURCE` intacta y `NEW` aislada;
* sesion SQL ajena conservada y operativa despues del aborto del intercambio.

## Riesgos pendientes y Fase 19E

* Probar timeout/reinicio del proceso web durante el reset.
* Definir retención y eliminación autorizada de OLD/FAILED y cuarentenas.
* Crear procedimiento operativo de recuperación de lock `ERROR`.
* Revisar y retirar de forma autorizada las bases desechables conservadas por Fase 19D.1.
* Evaluar por separado una autorizacion explicita para `APP_SCHEDULER_QA`; no queda implicita por esta prueba.
