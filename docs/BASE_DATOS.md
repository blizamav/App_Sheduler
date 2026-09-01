# Base de datos APP Scheduler v1.0.1

## Contrato canonico

La unica base de la aplicacion es `APP_SCHEDULER_QA`. El contrato limpio vigente
es el bootstrap 19C.1, derivado del bootstrap 19C.0 validado en el Hito 14 y del
contrato incremental 023, con:

* 33 tablas `dbo`;
* 457 columnas;
* 25 claves foraneas;
* 38 restricciones CHECK;
* 118 restricciones DEFAULT;
* 120 indices, incluidos PK y UNIQUE;
* sin vistas, procedures, funciones o triggers propios.

La validacion ejecutable es
`database/bootstrap/100_validacion_bootstrap_actual.sql`. El inventario por
tabla vive en `docs/PERSISTENCIA_RECONSTRUCCION.md`.

## Canales SQL

* `database/release/`: release publicado y protegido; no modificar.
* `database/bootstrap/`: instalacion limpia 002..011 y validacion 100;
  protegido y de solo lectura durante operacion.
* `database/factory_reset/`: runner in-place que consume el bootstrap.
* `database/migrations/`: correctivos incrementales historicos.
* `database/legacy_pre_release_13B/`: referencia historica no ejecutable.

## Migracion 023 aplicada en QA

`database/migrations/023_separar_destinatarios_exito_evidencia.sql` desacopla
Evidencia de la notificacion de exito y habilita el tipo de destinatario
`EXITO`. No borra historial: copia destinatarios legacy al grupo operacional,
desactiva la asignacion `EVIDENCIA` ambigua y apaga ese envio hasta que se
configure explicitamente el cliente. Debe revisarse y ejecutarse manualmente
antes de desplegar el runtime v1.0.1 sobre cualquier otra base existente.

El 2026-09-01 se ejecuto y valido sobre `APP_SCHEDULER_QA`. Se retiro
`CK_notif_config_evidencia_requiere_exito` y `CK_notif_dest_tipo` quedo activo,
confiable y limitado a `EXITO`, `EVIDENCIA` y `ALERTA`. La migracion convirtio
tres configuraciones legacy: creo sus destinatarios operacionales `EXITO`,
desactivo las asignaciones `EVIDENCIA` ambiguas y no elimino filas.

`database/bootstrap/` representa directamente este contrato final desde la
version 19C.1. Una instalacion limpia o Factory Reset futuro crea separados los
grupos `EXITO`, `EVIDENCIA` y `ALERTA`, sin requerir que Evidencia active Exito.

## Conexion

Web y Worker leen desde el entorno:

* `DB_SERVER`, `DB_DATABASE`, `DB_USER`, `DB_PASSWORD`, `DB_DRIVER`;
* `DB_ENCRYPT`, `DB_TRUST_SERVER_CERTIFICATE`, `DB_TIMEOUT`;
* `DB_APPLICATION_NAME`.

La cadena se construye en backend, no se registra completa y
`DB_DATABASE` se valida contra `APP_SCHEDULER_QA`. Los repositorios usan
parametros `?` de pyodbc y unidad de trabajo explicita.

## Cuentas

* cuenta ordinaria: operacion Web/Worker con privilegio minimo;
* cuenta mantenimiento: Factory Reset con `db_owner` solo en
  `APP_SCHEDULER_QA`;
* no se requieren permisos globales para crear, renombrar o eliminar bases.

## Datos y trazabilidad

Las entidades principales cubren identidad, catalogos, tareas, scripts y tres
versiones, programaciones, ejecuciones, logs, Scheduler/heartbeat, feriados,
auditoria, Papelera, evidencias y notificaciones. Ejecuciones congelan snapshots
de tarea/script/version para conservar historia aunque una entidad operativa se
retire o elimine de forma permitida.

No se guarda el contenido completo de evidencia ni secretos `.env`/Graph en la
base. `notificaciones_envios` conserva metadata y reserva at-most-once.

## Compatibilidad historica

La QA previa contenia seis aliases antiguos de `auditoria_cambios`. La
instalacion limpia no los necesita: usa las columnas canonicas. El contrato
post-ajuste de notificacion de exito es de 457 columnas; referencias anteriores
a 456 describen el estado previo a ese ajuste y no son el contrato v1.0.0.

## Operacion

No ejecutar migraciones historicas sobre una base ya reconstruida ni cambiar
estados operativos mediante SQL manual. Factory Reset solo se usa con respaldo,
ventana y autorizacion explicita.
