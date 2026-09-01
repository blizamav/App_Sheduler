# Factory Reset v1.0.0

## Contrato

El Factory Reset es **in-place** y actua exclusivamente sobre
`APP_SCHEDULER_QA`. No crea, elimina ni renombra bases; no usa esquemas
blue-green ni deja NEW/OLD/FAILED.

Permanece deshabilitado por defecto y requiere permiso backend, CSRF, preview
vigente y doble confirmacion.

## Cuenta de mantenimiento

La cuenta configurada en `FACTORY_RESET_DB_USER` es una cuenta SQL Server
distinta del usuario de APP Scheduler. Requiere `db_owner` solo en
`APP_SCHEDULER_QA`. No requiere ni debe recibir `sysadmin`, `CREATE ANY
DATABASE`, `ALTER ANY DATABASE` o `CONTROL SERVER`.

## Flujo

1. preview de target, lock, Worker, bootstrap, filesystem y cuenta;
2. confirmacion firmada y revalidacion antes del lock;
3. lock de aplicacion y modo mantenimiento;
4. detencion/verificacion de actividad;
5. cuarentena reversible de scripts, env y logs operativos;
6. SQLCMD ejecuta `000_reset_in_place.sql`;
7. `sp_getapplock`, `XACT_ABORT ON` y transaccion;
8. eliminacion controlada de las 33 tablas conocidas;
9. inclusion de bootstrap 002..011 y validacion 100;
10. commit SQL, limpieza de cuarentena y salida a estado NORMAL.

Si existe una tabla desconocida o FK cruzada, el reset se bloquea antes de
modificar. `database/release/` y `database/bootstrap/` son fuentes protegidas de
solo lectura.

## Opciones SQLCMD

El runner declara explicitamente las opciones de sesion necesarias para crear
indices filtrados:

* `QUOTED_IDENTIFIER ON`;
* `ANSI_NULLS ON`;
* `ANSI_PADDING ON`;
* `ANSI_WARNINGS ON`;
* `CONCAT_NULL_YIELDS_NULL ON`;
* `ARITHABORT ON`;
* `NUMERIC_ROUNDABORT OFF`.

La ausencia de estas opciones provoco el primer fallo real del Hito 14. SQL y
filesystem revirtieron integramente; la regresion impide omitirlas de nuevo.

## Rollback y fail-closed

Antes del commit SQL, cualquier error revierte la transaccion y restaura el
filesystem desde cuarentena. Si la recuperacion no puede confirmarse, el estado
permanece `ERROR`, conserva los recursos necesarios y bloquea nuevas
operaciones. No declara exito ni elimina evidencia de recuperacion a ciegas.

## Validacion real

El segundo y ultimo intento autorizado del Hito 14 finalizo correctamente:

* una unica `APP_SCHEDULER_QA`;
* 33 tablas y marca `BOOTSTRAP_SQL=19C.0`;
* Scheduler y Graph apagados por defecto;
* SQL y filesystem validados;
* sin lock o cuarentena residual;
* runtime funcional validado posteriormente.

El bootstrap canonico posterior queda en `19C.1`: conserva la misma estructura
general y aplica directamente la separacion de destinatarios y canales definida
por la migracion incremental 023. Un futuro Factory Reset validara esa marca.

Factory Reset no se repite durante Hito 15 ni como healthcheck. Su uso futuro
requiere respaldo, ventana, autorizacion explicita y plan de recuperacion.
