# Arquitectura oficial APP Scheduler v1.0.0

## Decision de cutover

El cutover concluyo en v1.0.0. `src/app_scheduler/` es el unico runtime
operativo. Docker Compose inicia `app_scheduler.web` y
`app_scheduler.worker.aplicacion`; el arbol `app/`, `run.py` y
`scheduler_worker.py` queda preservado como legado historico no operativo.

## Vista general

```text
Navegador
   |
   v
Web Flask ---- SQL Server APP_SCHEDULER_QA ---- Worker
                  ^             |                 |
                  |             v                 v
              Scheduler     auditoria         subprocess Python
                                                |   |   |
                                               log env evidencia
                                                    |
                                               Microsoft Graph
```

Web y Scheduler solo solicitan trabajo. El Worker es el ejecutor unico de
manuales y automaticas. SQL Server coordina cola, configuracion, estados,
heartbeat, calendario y trazabilidad.

## Componentes

### Web

Fabrica Flask modular con sesiones minimas, autenticacion hibrida, autorizacion
por permiso, CSRF global, templates Jinja autoescaped y blueprints por dominio.
Las rutas no contienen SQL y delegan en casos de uso.

### Scheduler

Forma parte del proceso Worker. Evalua solo si la configuracion SQL permite
Scheduler y ejecucion automatica, respeta mantenimiento y feriados locales, y
reserva una fila `PENDIENTE` con clave idempotente. No consulta Nager.Date ni
ejecuta scripts.

### Worker y cola

El Worker mantiene heartbeat, reclama filas `PENDIENTE` mediante operacion
atomica y aplica el limite de concurrencia. `--queue-only` omite por completo la
evaluacion del Scheduler; `--once` limita el proceso a un ciclo controlado.

### Motor

Ejecuta la version congelada con el interprete Python actual, `shell=False`,
directorio y entorno controlados. Captura stdout/stderr incrementalmente,
persiste PID, timeout, detencion y estado final. El `.env` de la version se
carga en memoria y nunca se presenta ni registra por la plataforma.

### Persistencia

`ProveedorConexionesSQLServer` crea conexiones desde variables tipadas. La
unidad de trabajo controla commit/rollback y los repositorios usan SQL
parametrizado. La cuenta ordinaria opera la app; la cuenta de mantenimiento se
usa solo por Factory Reset y tiene `db_owner` unicamente sobre
`APP_SCHEDULER_QA`.

Contrato bootstrap 19C.0 validado en Hito 14:

* 33 tablas `dbo`;
* 457 columnas;
* 25 FK;
* 39 CHECK;
* 118 DEFAULT;
* 120 indices;
* sin vistas, procedures, funciones o triggers propios.

### Filesystem

Scripts, `.env` de scripts, logs y control runtime viven bajo roots configuradas
y volumenes Docker. Las operaciones validan ruta canonica, traversal y enlaces.
Los secretos reales permanecen fuera de Git.

### Notificaciones

La configuracion por tarea separa exito, error y Evidencia 1.0. El Worker
reserva at-most-once en SQL antes de obtener token o enviar. Graph usa endpoint
fijo, client credentials del entorno, timeout y sin retry automatico. Un fallo
de correo no cambia el resultado de la ejecucion.

## Flujos

Manual:

```text
POST Web -> valida permiso/CSRF -> INSERT PENDIENTE -> Worker claim -> motor
```

Automatico:

```text
Scheduler -> candidato/calendario -> reserva idempotente PENDIENTE -> Worker
```

Observabilidad:

```text
Worker -> heartbeat SQL
Web -> heartbeat + configuracion + cola -> semaforo operativo
```

## Factory Reset

El reset es in-place sobre la unica base autorizada. El runner usa SQLCMD,
`XACT_ABORT`, opciones SET requeridas por indices filtrados, transaccion y
`sp_getapplock`. Antes del commit pone el filesystem en cuarentena; ante error
revierte SQL y restaura archivos. No usa `CREATE DATABASE`, `DROP DATABASE`,
renames ni bases NEW/OLD/FAILED.

## Seguridad arquitectonica

Controles implementados y validados durante QA:

* autenticacion hibrida y autorizacion backend;
* CSRF, cookie HttpOnly, SameSite y sesion minima;
* Jinja autoescape y cabeceras defensivas;
* SQL parametrizado y transacciones explicitas;
* filesystem confinado y upload/download controlado;
* subprocess con `shell=False`;
* logs y auditoria sin secretos conocidos;
* credenciales separadas para operacion, mantenimiento y Graph.

No se declara certificacion OWASP ni ausencia absoluta de vulnerabilidades.

## Limite operativo conocido

Una solicitud `PENDIENTE` se recupera al reiniciar Worker. Una caida abrupta
despues del claim puede dejar una ejecucion `EN_EJECUCION`; v1.0.0 no la
relanza automaticamente para evitar efectos duplicados. Requiere diagnostico
operacional.
