# Programaciones y scheduler reconstruidos

## Estado

Hitos 6 y 7 estan cerrados. El motor consume las reservas `PENDIENTE` sin duplicarlas; el runtime historico sigue activo y no existe cutover.

El worker ejecuta primero el ciclo scheduler, luego reclama capacidad disponible
y continua revisando la cola cada segundo entre ciclos. El claim registra el
worker real y conserva la version congelada por Hito 6. Una nueva version activa
solo afecta futuros disparos.

## Contrato demostrado

`dbo.programaciones` contiene tarea, tipo, modo diario, horas, intervalo, dias, dia de mes, fecha o fechas especificas, feriados, zona horaria, vigencia, auditoria tecnica y estado. No contiene version ni usuario ejecutor.

La automatica usa la version activa al momento del disparo. El join obtiene `scripts.id_version_activa`; la reserva congela `id_script` e `id_version` en `ejecuciones`. Cambiar despues la version activa no altera el historial reservado.

`ejecuciones.usuario_ejecucion` identifica al ejecutor aplicativo real cuando corresponda. Una automatica no posee uno aprobado, por lo que queda `NULL`. `nombre_worker` y `clave_programacion` conservan el solicitante tecnico. No se reutilizan usuarios de auditoria, JSON o campos descriptivos. No fue necesaria migracion.

### Correspondencia SQL, DTO y formulario

El contrato se verifico directamente en `database/release/002_schema_final.sql`, que el bootstrap incluye sin alterar. `configuracion_json` existe por compatibilidad y Hito 6 lo mantiene `NULL`; `proxima_ejecucion` pertenece a `dbo.tareas`, no a `dbo.programaciones`.

| Columna SQL | DTO `Programacion` | Formulario/caso de uso |
| --- | --- | --- |
| `id_programacion` | `id_programacion` | IDENTITY/ruta; no se acepta del formulario |
| `id_tarea` | `id_tarea` | segmento de ruta; no se acepta del formulario |
| `tipo_programacion` | `tipo_programacion` | `tipo_programacion` con allowlist |
| `modo_ejecucion_dia` | `modo_ejecucion_dia` | `modo_ejecucion_dia` con allowlist |
| `hora_inicio`, `hora_termino` | campos homologos | solo modo `INTERVALO` |
| `hora_ejecucion` | `hora_ejecucion` | solo modo `UNA_VEZ` |
| `intervalo_minutos` | `intervalo_minutos` | entero 1-1440 para `INTERVALO` |
| `dias_semana` | `dias_semana` | lista cerrada, normalizada en orden semanal |
| `dia_mes` | `dia_mes` | entero 1-31 para `MENSUAL` |
| `fecha_especifica` | `fecha_especifica` | fecha ISO para `FECHA_ESPECIFICA` |
| `fechas_especificas` | `fechas_especificas` | lista de fechas, persistida como JSON |
| `configuracion_json` | no expuesto | siempre `NULL` en Hito 6 |
| `ejecutar_en_feriados` | `ejecutar_en_feriados` | checkbox booleano |
| `zona_horaria` | `zona_horaria` | nombre IANA validado por `zoneinfo` |
| `fecha_inicio_vigencia`, `fecha_fin_vigencia` | campos homologos | fechas opcionales ordenadas |
| `fecha_creacion`, `fecha_actualizacion` | campos homologos | derivados por SQL, no editables |
| `usuario_creacion`, `usuario_actualizacion` | no expuestos en DTO | actor autenticado, no formulario |
| `activo` | `activo` | checkbox; cambio de estado con permiso dedicado |

PK: `PK_programaciones(id_programacion)`. FK: tarea y catalogo de tipo. CHECK: intervalo positivo, dia 1-31 y modo `UNA_VEZ`/`INTERVALO`. Indices: `IX_programaciones_tarea_activo(id_tarea, activo)` e `IX_programaciones_tipo_modo(tipo_programacion, modo_ejecucion_dia, activo)`.

## Tipos y calculo temporal

Tipos soportados por el catalogo final: `DIARIA`, `SEMANAL`, `MENSUAL`, `FECHA_ESPECIFICA` y `FECHAS_ESPECIFICAS`. Los modos son `UNA_VEZ` e `INTERVALO`. La validacion exige combinaciones completas, rangos, vigencia ordenada y una zona IANA valida.

| Tipo | Campos requeridos | Campos no aplicables | Calculo |
| --- | --- | --- | --- |
| `DIARIA` | modo y horas del modo | dias, dia de mes y fechas | cada dia aplicable |
| `SEMANAL` | modo, horas y uno o mas `dias_semana` | dia de mes y fechas | siguientes dias seleccionados |
| `MENSUAL` | modo, horas y `dia_mes` | dias y fechas | siguiente mes que contenga ese dia |
| `FECHA_ESPECIFICA` | modo, horas y `fecha_especifica` | dias, dia de mes y lista de fechas | una fecha exacta |
| `FECHAS_ESPECIFICAS` | modo, horas y lista `fechas_especificas` | dias, dia de mes y fecha unica | siguiente fecha de la lista normalizada |

El calculo central recibe programacion y referencia. Interpreta referencias naive en `programaciones.zona_horaria`; una referencia aware se convierte a esa zona. El resultado se persiste naive como hora civil local en `datetime2(0)`, que es el contrato SQL historico. UI y scheduler no duplican el calculo.

Politica DST: una hora inexistente durante el salto hacia adelante se omite; una hora ambigua durante el retroceso se considera una sola vez y usa el primer `fold`. La proxima fecha siempre se recompone desde calendario + hora civil, por lo que una programacion diaria no deriva progresivamente. La clave idempotente usa esa identidad civil unica.

Una ocurrencia atrasada solo se acepta dentro de `intervalo_revision_segundos`. Una ocurrencia mas antigua se registra como omitida y se avanza al siguiente disparo. Esta politica conserva el comportamiento historico y evita una rafaga al reiniciar el worker.

## Flujo operativo

1. El web crea, edita o cambia estado de una programacion dentro de la tarea.
2. El caso de uso valida backend, bloquea la tarea y mantiene una unica programacion activa.
3. Recalcula `tareas.tipo_tarea` y `tareas.proxima_ejecucion` en la misma UoW que auditoria.
4. El worker consulta configuracion y lock de Factory Reset.
5. Selecciona solo tarea/programacion activas y vencidas.
6. Respeta concurrencia, ventana de atraso y feriado local.
7. Resuelve script y version activa; si faltan, omite y avanza.
8. Construye una `SolicitudEjecucion` con origen `AUTOMATICA`.
9. El despachador inserta `ejecuciones.PENDIENTE` y avanza la proxima fecha en una transaccion.
10. El worker reclama esa fila y ejecuta el script mediante el motor unico de Hito 7.

## Idempotencia y concurrencia

La clave es `PROGRAMACION_<id_programacion>_<AAAAMMDDTHHMMSS>`. El indice filtrado `UX_ejecuciones_clave_programacion_automatica` impide dos reservas de la misma ocurrencia aunque dos workers compitan. Un error 2601/2627 se trata como duplicado ya procesado y la fecha derivada avanza dentro de la transaccion.

El indice real es `UNIQUE (clave_programacion) WHERE origen_ejecucion = 'AUTOMATICA' AND clave_programacion IS NOT NULL`. Por tanto, la identidad exacta es `id_programacion + fecha/hora civil programada`, codificada en la clave; no depende de un `SELECT` previo.

Antes del `INSERT`, el despachador adquiere un `sp_getapplock` exclusivo con owner `Transaction` y revalida `max_ejecuciones_concurrentes`. Asi dos workers tampoco pueden superar el limite al reservar tareas distintas. El lock se libera con commit/rollback y no requiere privilegios globales de servidor.

El recurso es el literal deterministico y acotado `APP_SCHEDULER_SCHEDULER_DESPACHO`, `LockMode='Exclusive'`, `LockOwner='Transaction'` y `LockTimeout=0`. La llamada y el conteo ocurren en la misma conexion/UoW. Cualquier retorno negativo bloquea la reserva; commit o rollback libera el lock. Dos workers sobre una misma ocurrencia terminan en una sola fila por la UNIQUE, y dos ocurrencias distintas revalidan capacidad dentro de la seccion serializada.

No se agregan locks de servidor ni privilegios elevados. La administracion de programaciones usa `UPDLOCK,HOLDLOCK` sobre la tarea y la busqueda de otra activa. Hito 7 agrego la ejecucion real sin modificar esta decision temporal.

## Worker y heartbeat

`src/app_scheduler/worker/aplicacion.py` mantiene `--check`, agrega `--once` y arranque continuo. `ServicioWorker` registra inicio, `EN_CICLO`, resultado, error recuperable, espera y detencion ordenada. El intervalo proviene de `configuracion_scheduler`; la espera usa `Event.wait`, sin busy-loop.

El lock `runtime_control/factory_reset.lock` se lee sin modificarlo. Archivo invalido o ilegible bloquea nuevos despachos. Scheduler apagado, automaticas deshabilitadas, mantenimiento y limite concurrente producen resultados controlados.

`--once` inicia heartbeat, ejecuta exactamente un ciclo sin threads residuales ni espera, registra el resultado, marca `DETENIDO` y sale. El modo continuo usa un `Event.wait(intervalo_revision_segundos)`, admite interrupcion por `SIGINT`/`SIGTERM` y no hace busy-loop. El heartbeat se actualiza al inicio, cambio de estado, fin de ciclo, error recuperable y detencion; `scheduler_worker_heartbeat` es consumido por monitoreo operativo.

## Contrato `SolicitudEjecucion`

| Campo | Origen | Obligatorio | Resuelve | Consume |
| --- | --- | --- | --- | --- |
| `id_tarea` | programacion/tarea | si | scheduler o flujo manual | persistencia y motor Hito 7 |
| `id_script`, `id_version` | version activa al reservar | si | scheduler o flujo manual | reserva y motor; quedan congelados |
| `origen` | `AUTOMATICA`/`MANUAL` | si | productor de solicitud | persistencia y Hito 7 |
| `actor` | identidad tecnica/humana | si | productor | trazabilidad operativa |
| `id_programacion`, `fecha_programada`, `clave_programacion` | regla automatica | automaticas | scheduler | idempotencia/persistencia |
| `usuario_ejecucion` | identidad aplicativa | usuario APP en manual; `NULL` automatica | productor de la reserva | `ejecuciones` |
| `nombre_worker` | identidad tecnica | automatica | worker scheduler | `ejecuciones`/eventos |
| `proxima_ejecucion` | calculo temporal | automatica | scheduler | avance de `tareas` |

Hito 6 decide cuando, valida elegibilidad, resuelve/congela version y crea la unica fila `PENDIENTE`. El motor Hito 7 reclama esa misma fila y la ejecuta sin crear otra ejecucion para la ocurrencia.

## Permisos

| Modulo | Accion | Permiso existente | Ruta |
| --- | --- | --- | --- |
| Tareas | Listar programaciones | `TAREAS_VER` | `GET /tareas/<id>/programaciones/` |
| Tareas | Crear programacion | `TAREAS_EDITAR` | `GET/POST .../nueva` |
| Tareas | Editar programacion | `TAREAS_EDITAR` | `GET/POST .../<id_programacion>/editar` |
| Tareas | Activar/desactivar | `TAREAS_ESTADO` | `POST .../<id_programacion>/estado` |

No se inventaron permisos. `SUPER_ADMIN`, `ADMIN` y `TI` reciben edicion/estado en bootstrap; `TERCERO` recibe solo `TAREAS_VER`.

Los POST de nueva, editar y estado exigen CSRF global y permiso backend. Sin token se rechazan; token valido sin permiso tambien produce 403. Los GET no modifican estado.

## Auditoria y eventos

Acciones humanas: `PROGRAMACION_CREADA`, `PROGRAMACION_EDITADA`, `PROGRAMACION_ACTIVADA` y `PROGRAMACION_DESACTIVADA` en `auditoria_cambios`, dentro de la UoW funcional. El polling normal no llena auditoria.

Despachos y omisiones relevantes usan `scheduler_eventos` con tipos permitidos `TAREA_EJECUTADA` y `TAREA_OMITIDA`. No se crean ejecuciones para omisiones.

## Limites y deuda legitima

Hito 10 no cambia el loop ni la decision temporal: el worker consulta
exclusivamente `dbo.feriados`. Nager.Date se usa solo desde la accion manual de
sincronizacion web; nunca se consulta Internet desde el scheduler. El despacho
Graph ocurre despues del cierre de una ejecucion y no puede crear, omitir ni
reprogramar candidatos.

* Hito 7 agrega claim, PID, detencion, stdout/stderr y cierre sin alterar la reserva del scheduler.
* La manual usa el mismo contrato persistente y registra al usuario APP Scheduler; la automatica conserva `usuario_ejecucion = NULL`.
* No se probo SQL Server/QA ni se modificaron datos reales en Hito 6.
* Validacion acumulada al cierre Hito 7: 205 pruebas reconstruidas y 231 totales aprobadas; `test_almacen_rechaza_symlink_que_escapa` se omite cuando Windows no permite crear el enlace y se valido en Linux.
* La revision visual manual del gate produjo correcciones desktop, movil y orientacion horizontal; el pulido visual global corresponde a Hito 12.
* El runtime historico continua siendo el productivo hasta cutover autorizado.
