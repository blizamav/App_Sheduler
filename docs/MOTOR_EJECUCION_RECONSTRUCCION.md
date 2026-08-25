# Motor de ejecucion reconstruido

## Estado

Hito 7 esta CERRADO. El motor vive solo en
`src/app_scheduler/`; `app/`, `run.py` y `scheduler_worker.py` permanecen sin
cutover. Hito 8 cerro observabilidad y configuracion sin alterar este motor ni
ejecutar scripts operativos. No se modifico el esquema SQL.

## Flujo unico

```text
Manual: HTTP autorizado -> reserva PENDIENTE -> worker -> claim -> motor
Automatica: scheduler Hito 6 -> PENDIENTE existente -> claim -> mismo motor
Motor -> Python -u -> stdout/stderr -> log -> evidencia -> estado final -> notificacion
```

La request manual no inicia procesos. Usa la version activa, la congela antes de
responder y guarda como `usuario_ejecucion` al usuario autenticado de APP
Scheduler. La automatica no crea una segunda fila, no resuelve nuevamente la
version, conserva `usuario_ejecucion = NULL` y registra ownership tecnico en
`nombre_worker`.

## Contrato de `dbo.ejecuciones`

| Columna | Tipo SQL | Proposito/escritor | Manual | Automatica |
| --- | --- | --- | --- | --- |
| `id_ejecucion` | `bigint IDENTITY` | Identidad SQL | Generada | Ya reservada por scheduler |
| `id_tarea` | `int NULL` | Referencia historica | Tarea validada | Tarea candidata |
| `id_script` | `int NULL` | Script congelado | Activo al reservar | Congelado por Hito 6 |
| `id_version` | `int NULL` | Version exacta | Activa al reservar | Nunca se recalcula |
| `origen_ejecucion` | `varchar(20)` | `MANUAL`/`AUTOMATICA` | `MANUAL` | `AUTOMATICA` |
| `estado_ejecucion` | `varchar(30)` | Ciclo del motor | Comun | Comun |
| `fecha_hora_inicio` | `datetime2(0)` | Reserva y luego claim real | Motor actualiza | Motor actualiza |
| `fecha_hora_termino` | `datetime2(0) NULL` | Cierre | Motor | Motor |
| `duracion_segundos` | `int NULL` | Duracion SQL | Motor | Motor |
| `codigo_salida` | `int NULL` | Return code real | Motor | Motor |
| `mensaje_error` | `nvarchar(max) NULL` | Diagnostico controlado | Motor | Motor |
| `usuario_ejecucion` | `nvarchar(100) NULL` | Solicitante aplicativo | Usuario de sesion | `NULL` |
| `pid_proceso` | `int NULL` | PID posterior a `Popen` | Motor | Motor |
| campos detencion | varios | Solicitud humana y cierre | Web/worker | Web/worker |
| `fecha_programada`/`clave_programacion` | fecha/varchar | Idempotencia automatica | `NULL` | Scheduler |
| `nombre_worker` | `varchar(100) NULL` | Ownership tecnico | Worker al claim | Worker al claim |
| snapshots | varios | Trazabilidad aun con maestros retirados | Reserva | Reserva scheduler |

No existen `id_programacion`, columna de timeout ni estado `TIMEOUT`. El ID de
programacion queda representado por la clave automatica ya aprobada. El timeout
global proviene del ambiente y finaliza como `ERROR`, sin inventar estado SQL.

## Estados y transiciones

| Desde | Hacia | Actor/condicion |
| --- | --- | --- |
| nuevo | `PENDIENTE` | Web manual o scheduler automatico reserva una fila |
| `PENDIENTE` | `EN_EJECUCION` | Claim atomico del worker |
| `EN_EJECUCION` | `EXITOSA` | Proceso termina con codigo 0 |
| `EN_EJECUCION` | `ERROR` | Codigo no cero, arranque fallido, timeout o detencion del worker |
| `EN_EJECUCION` | `DETENIDA_MANUALMENTE` | Solicitud autorizada persistida y atendida por el worker propietario |

`CANCELADA` existe en catalogo por compatibilidad, pero el contrato historico de
detencion vigente usa `DETENIDA_MANUALMENTE`. La UI no cambia estados de forma
arbitraria.

## Claim, concurrencia y crash

El claim usa `sp_getapplock`, limite concurrente, `UPDLOCK`, `READPAST` y
`ROWLOCK` dentro de la misma UoW. Dos workers no pueden obtener la misma fila y
el cambio a `EN_EJECUCION` registra inicio y worker antes de ejecutar.

La garantia es at-most-once despues del claim, no exactly-once. Una
`PENDIENTE` sobrevive al reinicio y puede ser reclamada. Una
`EN_EJECUCION` abandonada no se relanza automaticamente: PID puede reciclarse y
el esquema no posee lease. Debe diagnosticarse como incierta y cerrarse mediante
el control operativo autorizado; nunca se marca exitosa ni se duplica.

## Subprocess y filesystem

* Comando fijo: `[sys.executable, "-u", ruta_script]`.
* `shell=False`, stdin cerrado, cwd igual a la carpeta de la version.
* Ruta fisica validada dentro de `RUTA_BASE_SCRIPTS`; symlinks quedan rechazados.
* Grupo/sesion de proceso nuevo. Timeout, detencion o shutdown terminan el grupo,
  esperan gracia y fuerzan solo el arbol propio si es necesario.
* Windows usa `CREATE_NEW_PROCESS_GROUP` y `taskkill /T /F` solo para el PID
  creado; Linux usa `start_new_session` y `killpg`.

## Entorno

El child recibe una allowlist minima de variables OS necesarias, mas
`PYTHONUNBUFFERED=1`, `PYTHONIOENCODING=utf-8` y el `.env` de su version. No
hereda credenciales SQL, Factory Reset, Graph, sesiones ni secretos internos.
`dotenv_values(..., interpolate=False)` carga una copia aislada y nunca modifica
`os.environ`.

Variables de control:

* `EJECUCION_TIMEOUT_SEGUNDOS`, default 3600, rango 10-86400.
* `EJECUCION_GRACIA_TERMINACION_SEGUNDOS`, default 5, rango 1-60.

## Logs y evidencia

`stdout` y `stderr` se leen en hilos acotados e independientes. Cada linea recibe
timestamp, nivel y canal y se escribe inmediatamente bajo
`logs_tareas/AAAA/MM/DD/ejecucion_ID.log`. El archivo conserva salida completa;
la API visual retorna los ultimos 120 KB. Stderr no convierte por si solo una
ejecucion en error: manda el return code.

Si `notificaciones_config_tarea.enviar_evidencia = 1`, el capturador observa solo
stdout, exige un unico bloque, valida el contrato 1.0 y comprueba que cada
adjunto obligatorio declarado exista dentro de la carpeta de la version. Persiste en
`evidencias_ejecucion` solo estado, metadata, hash y contadores; un archivo
ausente o fuera del root controlado queda `ADJUNTO_FALTANTE`. El JSON completo
permanece disponible solo durante el cierre del motor y no se guarda en BD.

Hito 10 agrega el paso posterior al cierre: con una ejecucion `EXITOSA` y
evidencia `VALIDADA` puede reservar `EVIDENCIA_CLIENTE`; con ejecucion `ERROR` o
evidencia requerida invalida puede reservar `ALERTA_INTERNA`. El envio Graph
ocurre fuera de la transaccion de ejecucion, se finaliza por separado y no
cambia su estado ante fallos HTTP. Los adjuntos declarados se revalidan bajo el
root de la version antes de codificarlos. No hay retry automatico.

## Rutas y permisos

| Ruta | Metodo | Permiso |
| --- | --- | --- |
| `/ejecuciones/` | GET | `EJECUCIONES_VER` |
| `/ejecuciones/<id>` | GET | `EJECUCIONES_VER` |
| `/ejecuciones/<id>/log` | GET | `EJECUCIONES_LOG_VER` |
| `/tareas/<id>/ejecutar` | POST | `EJECUCIONES_EJECUTAR` + CSRF |
| `/ejecuciones/<id>/detener` | POST | `EJECUCIONES_DETENER` + CSRF |

Las acciones humanas se auditan. Cada request acepta IDs de ruta y motivo; no
acepta comando, PID, ruta, worker, usuario ni version desde el cliente.

## Mantenimiento y operacion

Factory Reset y modo mantenimiento bloquean reservas manuales y nuevos claims.
Las ejecuciones ya tomadas no se duplican. Al detener el worker, el evento
compartido termina su arbol y cierra como `ERROR` antes de apagar el pool.

El worker revisa la cola despues del scheduler y una vez por segundo entre ciclos.
El pool tiene un maximo tecnico de 20, pero nunca reclama por encima de
`configuracion_scheduler.max_ejecuciones_concurrentes`.

## Deuda legitima

No existe lease/epoch persistente para recuperar automaticamente un
`EN_EJECUCION` tras crash duro. Agregarlo requeriria cambio SQL formal. Hito 7
mantiene at-most-once y deja esas filas para verificacion operativa, sin ocultar
datos en logs, JSON u observaciones.

## Validacion tecnica

* Motor Hito 7: 25 pruebas aprobadas.
* Reconstruccion: 205 aprobadas y 1 omitida por symlink en Windows.
* Suite completa: 231 aprobadas y 1 omitida.
* `compileall`, 17 templates y JavaScript: OK.
* Compose, build `web`/`worker`, checks Linux y subprocess Linux: OK usando
  configuracion ficticia aislada y sin SQL.
* Revision visual manual: aplicada en escritorio, movil vertical y movil
  horizontal; se corrigieron sidebar, Offcanvas, dropdowns, formularios y uso
  del ancho disponible. El pulido visual global permanece planificado para
  Hito 12.
