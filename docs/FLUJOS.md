# Flujos

## Flujo Fase 13A.1B - Limpieza parametrizable de eventos

La limpieza de eventos del programador permite seleccionar periodo y categorias concretas antes de eliminar registros antiguos.

Flujo:

1. Usuario autorizado abre `/scheduler/eventos`.
2. Selecciona periodo: 20, 30, 60 o 90 dias.
3. Selecciona una o varias categorias permitidas, o usa `Seleccionar todas`.
4. Puede usar `Limpiar solo ruido operativo` para marcar `CICLO_INICIADO`, `CICLO_FINALIZADO` y `TAREA_OMITIDA/FUERA_DE_VENTANA`.
5. Presiona `Previsualizar limpieza`.
6. Frontend llama `POST /scheduler/eventos/limpiar/previsualizar`.
7. Backend valida permiso, periodo y categorias contra whitelist.
8. Backend retorna fecha limite, total y detalle por categoria.
9. La vista habilita `Limpiar eventos seleccionados` solo si existe conteo previo mayor a cero.
10. Al confirmar, el modal muestra periodo, fecha limite, categorias, total, detalle y advertencia.
11. El usuario marca checkbox obligatorio.
12. Backend recalcula filtros seguros y elimina solo de `scheduler_eventos`.
13. Se registra auditoria y log de sistema.

La limpieza no acepta `tipo_evento` o `motivo` libres desde frontend. Las claves seleccionadas se traducen en backend a condiciones SQL controladas.

## Flujo Fase 13A.1 - Eventos del programador y limpieza controlada

Problema detectado: `scheduler_eventos` podia crecer rapido porque cada ciclo normal del worker registraba inicio, fin y omisiones por `FUERA_DE_VENTANA`.

Nueva politica de persistencia:

* No se guardan por defecto `CICLO_INICIADO`.
* No se guardan por defecto `CICLO_FINALIZADO`.
* No se guarda por defecto `TAREA_OMITIDA` con motivo `FUERA_DE_VENTANA`.
* Si se guardan eventos relevantes: `TAREA_EJECUTADA`, `ERROR_SCHEDULER`, omisiones por `FERIADO`, `DUPLICADO_SLOT`, `LIMITE_CONCURRENCIA`, `EJECUCION_EN_CURSO`, `MODO_MANTENIMIENTO`, `SCHEDULER_INACTIVO`, `EJECUCION_AUTOMATICA_DESHABILITADA` y errores de validacion.

Flujo de limpieza:

1. Usuario autorizado abre `/scheduler/eventos`.
2. La pantalla muestra la seccion `Limpieza de eventos`.
3. El usuario selecciona 20, 30, 60 o 90 dias.
4. La UI muestra conteo previo de eventos informativos antiguos por opcion.
5. Al presionar `Limpiar eventos antiguos`, se abre modal corporativo danger.
6. El usuario debe marcar el checkbox obligatorio.
7. Backend valida permiso `SCHEDULER_CONFIG_EDITAR`.
8. Backend elimina solo de `scheduler_eventos` los eventos antiguos permitidos.
9. Se registra auditoria y log de sistema de la accion humana administrativa.
10. La pantalla muestra resumen con cantidad eliminada y fecha limite.

La limpieza no afecta ejecuciones, logs, auditoria, heartbeat, tareas, scripts, usuarios, configuraciones, papelera ni snapshots.

## Roadmap de flujos pendiente

Los flujos implementados llegan hasta Fase 12B.2 en validacion operativa del worker. El roadmap formal se mantiene en `docs/ROADMAP.md`.

Pendiente critico inmediato:

* Fase 12C: trazabilidad extendida, exportaciones futuras y mejoras avanzadas de consulta.

## Protocolo de validacion operativa 12B.2 - scheduler_worker

La Fase 12B.2 valida el Programador automatico real mediante `scheduler_worker.py`. La configuracion del Programador en la app no enciende por si sola el proceso worker; solo define que debe hacer el worker cuando ya esta corriendo.

Estados esperados:

* Worker apagado: no ejecuta tareas aunque el Programador este activo.
* Worker encendido + Programador inactivo: registra/respeta inactividad y no ejecuta.
* Worker encendido + Programador activo + ejecucion automatica permitida: puede ejecutar tareas elegibles.
* Worker encendido + modo mantenimiento: registra/respeta mantenimiento y no ejecuta.

Comandos de validacion:

```powershell
python scheduler_worker.py --once
```

```powershell
python scheduler_worker.py
```

Matriz minima:

1. Worker una sola vuelta: debe leer configuracion, actualizar heartbeat/eventos si SQL Server esta disponible y finalizar sin romper.
2. Programador inactivo: no debe crear ejecuciones y debe registrar omision `SCHEDULER_INACTIVO`.
3. Ejecucion automatica deshabilitada: no debe crear ejecuciones y debe registrar `EJECUCION_AUTOMATICA_DESHABILITADA`.
4. Modo mantenimiento: no debe crear ejecuciones y debe registrar `MODO_MANTENIMIENTO`.
5. Tarea elegible: debe crear ejecucion `AUTOMATICA`, `logs_tareas`, evento `TAREA_EJECUTADA` y cierre `EXITOSA` o `ERROR`.
6. No duplicar slot: un segundo ciclo sobre la misma ventana debe registrar `DUPLICADO_SLOT` o equivalente y no crear otra ejecucion.
7. Concurrencia: no debe superar `max_ejecuciones_concurrentes`; debe registrar `LIMITE_CONCURRENCIA` cuando aplique.
8. Feriado: si la tarea no permite feriados, debe omitir y registrar `FERIADO`.
9. Worker continuo breve: debe actualizar heartbeat, registrar eventos, no duplicar y detenerse sin dejar inconsistencias.

Consultas manuales sugeridas para SSMS. Codex no debe ejecutarlas automaticamente:

```sql
SELECT TOP 30
id_ejecucion,
id_tarea,
origen_ejecucion,
estado_ejecucion,
pid_proceso,
codigo_salida,
fecha_hora_inicio,
fecha_hora_termino,
duracion_segundos
FROM dbo.ejecuciones
ORDER BY id_ejecucion DESC;
```

```sql
SELECT TOP 50
id_evento,
fecha_evento,
tipo_evento,
decision,
motivo,
id_tarea,
nombre_tarea,
nombre_worker,
detalle
FROM dbo.scheduler_eventos
ORDER BY id_evento DESC;
```

```sql
SELECT TOP 20 *
FROM dbo.scheduler_worker_heartbeat
ORDER BY fecha_actualizacion DESC;
```

```sql
SELECT
id_ejecucion,
estado_ejecucion,
pid_proceso,
fecha_hora_inicio,
fecha_hora_termino
FROM dbo.ejecuciones
WHERE estado_ejecucion = 'EN_EJECUCION'
ORDER BY id_ejecucion DESC;
```

Resultado de esta ejecucion en Codex:

* `python scheduler_worker.py --once` corrio sin romper, pero no pudo conectar a SQL Server por error ODBC local de cifrado/credenciales.
* El arranque continuo breve de `python scheduler_worker.py` informo el mismo error controlado y entro al ciclo de espera; fue detenido desde wrapper de prueba.
* No se obtuvieron IDs reales de tarea, ejecucion, eventos ni heartbeat porque SQL Server no estuvo accesible.
* Se detecto y corrigio un riesgo real: la ejecucion automatica usaba hilo daemon y podia quedar sin cierre en modo `--once`.
* Se detecto y corrigio robustez de heartbeat: los fallos de registro/log de heartbeat ya no deben tumbar el worker cuando SQL Server no esta disponible.

## Flujo consolidado de Auditoria

1. Usuario realiza una accion humana critica desde la UI.
2. El servicio ejecuta la accion principal y prepara valores antes/despues cuando corresponde.
3. Si la accion se completa, registra auditoria con resultado `OK`.
4. Si una regla de seguridad o negocio bloquea la accion, registra resultado `BLOQUEADO`.
5. Si ocurre un error controlado de aplicacion, registra resultado `ERROR`.
6. `registrar_auditoria(...)` normaliza `accion`, `entidad`, `resultado` y `modulo`.
7. La sanitizacion reemplaza claves sensibles por `***` antes de persistir valores.
8. Si auditoria falla, la accion principal no se rompe; se intenta dejar evidencia tecnica en `logs_sistema`.
9. Los errores repetitivos del worker automatico siguen en `scheduler_eventos` o `logs_sistema`, no en auditoria funcional.

Acciones cubiertas en Fase 12B:

* Usuarios, mantenedores, tareas, scripts y versiones.
* `.env` por version sin valores secretos.
* Papelera, restauracion y eliminacion permanente.
* Ejecucion manual, detencion y verificacion de huerfanas.
* Configuracion del programador.
* Feriados y sincronizacion manual.
* Bloqueos por permisos, duplicados y reglas de negocio.

## Flujo de eliminacion permanente masiva en Papelera

1. Usuario autorizado abre `/papelera`.
2. La vista muestra el total filtrado, el total real de Papelera y el boton `Eliminar permanentemente todo` si la sesion tiene `PAPELERA_ELIMINAR_PERMANENTE` o permisos totales.
3. Al presionar el boton, el modal corporativo muestra advertencia fuerte, resumen por entidad y checkbox obligatorio.
4. Si el usuario cancela, no se envia el formulario y no se ejecuta ninguna eliminacion.
5. Si confirma, el backend lista los registros con `eliminado_operativo = 1`.
6. El servicio ordena el procesamiento para intentar primero versiones de scripts, scripts, tareas, maestros y usuarios.
7. Cada registro se procesa con `eliminar_registro_permanente(...)`, reutilizando las mismas validaciones de la accion individual.
8. Si un item se elimina, desaparece de las tablas operativas y de Papelera; el historial se conserva.
9. Si un item queda bloqueado por regla de seguridad, dependencia o integridad, permanece en Papelera y el proceso continua.
10. Los errores tecnicos por item se transforman en mensaje seguro, sin `pyodbc`, constraints ni traceback.
11. Al finalizar, se muestra resumen de encontrados, eliminados, no eliminados, errores y motivos seguros.
12. La accion masiva registra auditoria `ELIMINAR_PERMANENTE_TODO_PAPELERA`; cada item mantiene la auditoria individual existente.

Reglas:

* No usar `DELETE` masivo bruto sobre Papelera.
* No usar `DELETE CASCADE` destructivo.
* No borrar `ejecuciones`, `logs_tareas`, `logs_sistema`, `scheduler_eventos`, `auditoria_cambios` ni snapshots.
* No modificar reglas individuales de restauracion o eliminacion permanente.
* No avanzar a purga automatica ni retencion programada.

## Flujo transversal de duplicados con Papelera Operativa

1. Usuario intenta crear o editar usuarios, mantenedores, tareas, scripts o versiones.
2. El servicio valida campos obligatorios y normaliza la clave de negocio correspondiente.
3. Antes de guardar, consulta duplicados incluyendo registros con `eliminado_operativo = 1`.
4. Si el duplicado esta activo, bloquea con mensaje de registro activo existente.
5. Si el duplicado esta inactivo, bloquea indicando que se puede activar o editar el registro existente.
6. Si el duplicado esta en Papelera Operativa, bloquea indicando que se debe restaurar o eliminar permanentemente antes de crear otro.
7. Si SQL Server igualmente devuelve una violacion unica, el servicio captura solo ese caso y muestra mensaje seguro sin detalle tecnico.
8. Cada bloqueo registra auditoria `BLOQUEO_DUPLICADO` con resultado `BLOQUEADO` cuando la tabla de auditoria esta disponible.
9. No se ejecutan restauraciones ni eliminaciones automaticas desde este flujo.

Claves validadas:

* Usuarios: `usuario` y `email`.
* Mantenedores: `nombre_normalizado`.
* Tareas: `nombre_tarea + cliente + categoria + tipo`.
* Scripts: un contenedor por `id_tarea`.
* Versiones: `id_script + numero_version`, contando tambien versiones en Papelera para `v1`, `v2` y `v3`.

## Flujo de disponibilidad de ejecucion manual en tareas

1. Usuario autorizado abre `/tareas`.
2. El backend lista tareas operativas no borradas.
3. Para cada tarea consulta estado de tarea, script asociado, version activa y ejecuciones `EN_EJECUCION`.
4. El servicio clasifica la tarea como `Ejecutable` solo si la tarea esta activa, no esta borrada operativamente, el script esta activo y no borrado, la version activa existe y esta disponible, y no hay ejecucion en curso.
5. Si falta alguna condicion, el listado muestra `No ejecutable: motivo`; si no existe fila en `scripts`, el motivo es `Sin script asociado`.
6. El boton `Ejecutar ahora` usa la misma clasificacion del servicio.
7. Una tarea no ejecutable conserva visible `Editar`, `Scripts`, cambio de estado y borrado segun permisos.

## Flujo de cierre garantizado de ejecucion manual

1. Usuario presiona `Ejecutar ahora`.
2. El backend valida tarea, script, version, archivo fisico, `.env` requerido y ejecucion en curso.
3. Se crea `ejecuciones` en `EN_EJECUCION` y `logs_tareas` en `EN_EJECUCION`.
4. Se inicia un hilo monitor no daemon para la ejecucion manual.
5. El monitor entra con `app_context`, lanza `subprocess.Popen`, guarda `pid_proceso` y lee stdout/stderr combinado.
6. Al terminar el proceso, `process.wait()` entrega returncode.
7. Si returncode es `0`, se cierra como `EXITOSA`.
8. Si returncode es distinto de `0`, se cierra como `ERROR`.
9. Si el usuario detiene desde UI, el estado queda `DETENIDA_MANUALMENTE` y el monitor no lo sobrescribe.
10. Si falla el monitor, se intenta terminar el proceso hijo y se cierra como `ERROR` con mensaje controlado.
11. En `finally`, si la ejecucion manual sigue `EN_EJECUCION`, se cierra como `ERROR`.
12. El boton `Verificar ejecucion` queda como recuperacion excepcional para procesos realmente huerfanos.

## Flujo de sincronizacion visual de consola

1. Usuario abre `/ejecuciones/<id_ejecucion>`.
2. El render inicial muestra el estado real almacenado en base de datos.
3. Si la ejecucion sigue en curso, la consola consulta `/ejecuciones/<id_ejecucion>/log` cada 3 segundos.
4. El endpoint devuelve log, `estado_actual`, `estado_es_final`, fecha de termino, alias `fecha_hora_fin`, duracion, codigo de salida y mensaje de error cuando existen.
5. El frontend actualiza sin recargar pagina el titulo de estado, badge superior, indicador de consola, termino, duracion y codigo de salida.
6. Mientras la ejecucion esta `EN_EJECUCION`, se mantienen visibles las acciones operativas aplicables.
7. Cuando el estado pasa a `EXITOSA`, `ERROR` o `DETENIDA_MANUALMENTE`, se ocultan o deshabilitan las acciones de ejecucion en curso.
8. Al detectar una transicion desde estado no final a final, se muestra un toast no bloqueante una sola vez.
9. `EXITOSA` muestra toast de finalizacion correcta; `ERROR` muestra toast de error; `DETENIDA_MANUALMENTE` muestra toast de detencion.
10. Si la ejecucion ya estaba finalizada al abrir la pagina, se muestra su estado final desde el inicio, no se repite toast de termino y el polling se corta despues de la primera sincronizacion.
11. La detencion y la verificacion desde consola pueden enviarse por `fetch`; la respuesta se sincroniza con el mismo contrato JSON y no requiere refresh completo.

## Protocolo de validacion operativa 12B.1C

La fase 12B.1C es de validacion, no de desarrollo funcional. Debe ejecutarse desde la app real con usuario autenticado y SQL Server accesible.

Matriz minima:

1. Ejecutar 5 veces un script rapido exitoso: debe terminar `EXITOSA`, `codigo_salida = 0`, con termino y duracion poblados, sin usar `Verificar`.
2. Ejecutar 2 veces un script exitoso con espera de 20 a 30 segundos: logs progresivos, cierre `EXITOSA` y sin huerfanas.
3. Ejecutar 2 veces un script con error controlado: cierre `ERROR`, codigo distinto de cero o `mensaje_error`.
4. Ejecutar 1 script largo y detenerlo desde consola: cierre `DETENIDA_MANUALMENTE`, sin PID vivo y sin sobreescritura posterior a `ERROR`.
5. Abrir una ejecucion ya finalizada: debe cargar con estado final, no mostrar `EN_EJECUCION` ni toast repetitivo.
6. Presionar `Verificar ejecucion` sobre una ejecucion finalizada: no debe cambiar estado ni marcar `ERROR`.

Consultas manuales sugeridas para SSMS, ajustadas a los nombres reales del esquema:

```sql
SELECT TOP 30
    id_ejecucion,
    estado_ejecucion,
    pid_proceso,
    codigo_salida,
    fecha_hora_inicio,
    fecha_hora_termino,
    duracion_segundos,
    mensaje_error
FROM dbo.ejecuciones
ORDER BY id_ejecucion DESC;
```

```sql
SELECT
    id_ejecucion,
    estado_ejecucion,
    pid_proceso,
    fecha_hora_inicio,
    fecha_hora_termino
FROM dbo.ejecuciones
WHERE estado_ejecucion = 'EN_EJECUCION'
ORDER BY id_ejecucion DESC;
```

```sql
SELECT *
FROM dbo.logs_tareas
WHERE id_ejecucion = <ID_EJECUCION>
ORDER BY id_log ASC;
```

Estado de ejecucion desde Codex: bloqueado por login requerido y error local ODBC de cifrado/credenciales. No se ejecuto SQL automaticamente.

## Flujo de panel principal general

1. Usuario autenticado abre `/panel`.
2. El backend consulta metricas reales de tareas, scripts, ejecuciones, scheduler y feriados.
3. Si la base responde correctamente, el panel muestra resumen ejecutivo operativo.
4. Si una consulta falla, el panel carga con advertencia controlada y no expone credenciales ni detalle sensible.
5. Los accesos rapidos se muestran segun permisos de la sesion.
6. Las ultimas ejecuciones permiten abrir la consola de cada ejecucion.
7. El estado general muestra modulos operativos y estado de heartbeat del worker cuando existe registro.
8. El panel no inicia, detiene ni controla el proceso `scheduler_worker.py`.

## Flujo de heartbeat del worker

1. Se ejecuta `python scheduler_worker.py` o `python scheduler_worker.py --once`.
2. El worker obtiene `nombre_worker_principal` desde `configuracion_scheduler`; si no existe usa `worker_default`.
3. Al iniciar, crea o actualiza un registro activo en `scheduler_worker_heartbeat`.
4. Antes de cada ciclo marca estado `EN_CICLO` y actualiza `fecha_ultimo_heartbeat`.
5. Al terminar un ciclo correcto marca `ESPERANDO`, registra resultado `OK`, incrementa `ciclos_ejecutados` y guarda contadores del ultimo ciclo.
6. Si ocurre un error controlado, marca estado `ERROR`, registra `ultimo_error` resumido y actualiza heartbeat.
7. Si el worker termina por `--once` o interrupcion controlada, marca estado `DETENIDO`.
8. `/scheduler/panel` lee el heartbeat y clasifica el estado visual segun el tiempo desde la ultima senal y el intervalo configurado.
9. `logs_sistema` no se usa para cada heartbeat; solo registra inicio, detencion, error, recuperacion o fallo al actualizar heartbeat.
10. La app no inicia ni detiene el worker desde el panel.

## Flujo de eventos del programador

1. El proceso `scheduler_worker.py` inicia un ciclo automatico.
2. El servicio del programador registra un evento de ciclo iniciado en `scheduler_eventos`.
3. Por cada decision relevante registra si una tarea se envia a ejecucion o se omite.
4. Si la tarea se ejecuta, se crea una ejecucion real mediante el flujo existente y se registra evento `TAREA_EJECUTADA`.
5. Si la tarea se omite, no se crea registro en `ejecuciones` ni `logs_tareas`.
6. Si se omite por feriado, el evento guarda `es_feriado`, `nombre_feriado` y el valor de `ejecutar_en_feriados`.
7. Si se omite por ejecucion en curso, duplicado de slot o limite de concurrencia, el evento guarda motivo y detalle operativo.
8. Si el scheduler esta inactivo, en mantenimiento o con ejecucion automatica deshabilitada, se registra omision de ciclo con motivo operativo.
9. Al finalizar el ciclo se registra evento de ciclo finalizado con resumen de evaluadas, ejecutadas y omitidas.
10. `/scheduler/panel` muestra los eventos recientes como monitoreo de solo lectura.

Reglas:

* `scheduler_worker_heartbeat` sigue registrando senal de vida en tabla separada.
* `logs_sistema` no se usa para cada omision del programador.
* Los eventos del programador no reemplazan la auditoria funcional.

## Flujo de resumen inteligente de eventos del programador

1. Usuario abre `/scheduler/panel`.
2. El backend consulta `scheduler_eventos` con `activo = 1`.
3. El panel calcula conteos del dia: eventos, ejecutadas, omitidas y errores.
4. El panel agrupa omisiones del dia por motivo.
5. El panel muestra solo ultimos eventos relevantes para evitar ruido operativo.
6. Son relevantes `ERROR_SCHEDULER`, `TAREA_EJECUTADA` y omisiones por `FERIADO`, `EJECUCION_EN_CURSO`, `DUPLICADO_SLOT` y `LIMITE_CONCURRENCIA`.
7. `CICLO_INICIADO`, `CICLO_FINALIZADO` y `FUERA_DE_VENTANA` repetitivo se reflejan en conteos, no como filas dominantes.
8. Si no hay eventos relevantes se muestra `Sin eventos relevantes recientes`.
9. No se crea una ruta completa `/scheduler/eventos` en esta fase.
10. La retencion manual futura usa `limpiar_eventos_antiguos(dias_retencion=90)` y marca `activo = 0`, sin borrar fisicamente.

## Flujo de historial filtrable de eventos del programador

1. Usuario autorizado abre `/scheduler/eventos`.
2. La ruta reutiliza permiso `SCHEDULER_CONFIG_VER`.
3. El backend consulta `scheduler_eventos` con condicion obligatoria `activo = 1`.
4. El usuario puede filtrar por fecha desde, fecha hasta, tarea, tipo evento, decision, motivo, proceso y texto libre.
5. La consulta usa paginacion server-side con `OFFSET / FETCH`.
6. Las opciones de pagina son 10, 25, 50 y 100 registros.
7. La tabla muestra fecha, proceso, tarea, tipo evento, decision, motivo, fecha programada y detalle breve.
8. Si no hay registros se muestra `Sin eventos del programador para los filtros seleccionados.`
9. La vista no muestra eventos inactivos por defecto.
10. Esta vista no crea ejecuciones, no modifica eventos y no reemplaza Auditoria.

## Flujo de control de ejecuciones huerfanas

1. Una ejecucion se inicia desde la app o desde el programador.
2. El backend crea la fila en `ejecuciones` con estado `EN_EJECUCION`.
3. El proceso Python se lanza con `subprocess.Popen` y se guarda `pid_proceso`.
4. Un hilo en memoria del proceso Flask espera el termino del proceso y actualiza estado final.
5. Si Flask se cierra o reinicia durante la ejecucion, el hilo monitor desaparece.
6. Si el proceso hijo termina y no existe un monitor activo, la base puede quedar en `EN_EJECUCION`.
7. En consola, el usuario puede presionar `Verificar ejecucion`.
8. Si el PID existe, se informa `La ejecucion sigue activa.` y no se modifica nada.
9. Si el PID no existe, se marca `ERROR` y se completa termino/duracion/mensaje.
10. Si la ejecucion ya estaba finalizada, no se modifica.
11. El control no mata procesos automaticamente.

## Flujo de borrado operativo seguro

1. El usuario presiona `Borrar` en tareas, scripts, versiones, usuarios, clientes, categorias o tipos.
2. La UI muestra modal corporativo indicando que el registro se retirara de la operacion normal y que el historial se conservara.
3. El backend valida bloqueos estrictos: ejecucion `EN_EJECUCION`, usuario actual, ultimo administrador activo o integridad sin snapshot suficiente.
4. Si no existe historial, se elimina fisicamente el registro y sus dependencias operativas directas cuando corresponde.
5. Si existe historial, se rellenan snapshots historicos antes de retirar el registro.
6. El registro maestro queda con `eliminado_operativo = 1`, `activo = 0` y metadatos de retiro.
7. Los mantenedores, selects, candidatos del scheduler y metricas operativas excluyen registros retirados.
8. `/ejecuciones`, `/ejecuciones/<id>`, logs y eventos del programador siguen mostrando nombres legibles mediante snapshots.
9. No se borran ejecuciones, logs historicos, eventos del programador ni `auditoria_cambios`.
10. La accion queda trazada por Auditoria desde Fase 12A cuando aplica.
11. Papelera operativa, restauracion y eliminacion permanente segura fueron implementadas en Fase 11G.
12. Desacople historico para eliminacion permanente real implementado en Fase 11H.

## Flujo de papelera operativa

Implementado en Fase 11G:

1. Usuario autorizado abre una vista de registros retirados operativamente.
2. El sistema lista entidades con `eliminado_operativo = 1`.
3. El usuario revisa contexto, historial y motivo de retiro.
4. El usuario puede elegir `Restaurar` o `Eliminar permanentemente`.
5. Si corresponde restaurar, el backend valida integridad, duplicados y dependencias.
6. Si la restauracion es segura, el registro vuelve a operacion normal con `activo = 0`.
7. Si la restauracion no es segura, se informa el bloqueo con motivo.

## Flujo de eliminacion permanente desde papelera

Implementado en Fase 11G:

1. Usuario autorizado presiona `Eliminar permanentemente` desde `/papelera`.
2. La UI muestra modal corporativo fuerte.
3. El texto debe advertir que el registro desaparecera de tablas operativas, mantenedores, papelera, selects y paneles, pero que historial de ejecuciones, logs, eventos del programador y snapshots se conservaran.
4. Si el usuario cancela, no se ejecuta ninguna accion.
5. Si confirma, el backend valida que la eliminacion fisica sea segura.
6. Si es segura, ejecuta `DELETE` solo sobre tablas operativas o maestras correspondientes.
7. No usa `DELETE CASCADE` destructivo.
8. No borra `ejecuciones`, `logs_tareas`, `logs_sistema`, `scheduler_eventos`, snapshots, `auditoria_cambios` ni archivos de log historicos necesarios.
9. El registro desaparece de `/papelera` y de la operacion normal.
10. Si no es segura, no fuerza `DELETE`, mantiene `eliminado_operativo = 1` y muestra: `No fue posible eliminar permanentemente este registro porque aún existen dependencias operativas no históricas. El registro seguirá en papelera y oculto de la operación normal.`

### Caso tarea

Una tarea retirada puede eliminarse permanentemente solo si no tiene ejecucion `EN_EJECUCION`, las ejecuciones y eventos ya tienen snapshots suficientes, no se rompen claves foraneas y no se requiere borrar historial.

Nunca se eliminan ejecuciones, logs, eventos del programador ni snapshots de esa tarea. Las ejecuciones historicas deben seguir visibles usando snapshots.

### Caso script

Un script o version retirada puede eliminarse permanentemente solo si no queda como version activa de un script vigente, no rompe FK, las ejecuciones ya tienen snapshot de script/version y no se borran logs historicos.

Las ejecuciones antiguas deben seguir mostrando nombre de script, archivo y version desde snapshot.

### Caso usuario

Un usuario retirado no puede eliminarse permanentemente si es el usuario actual o el ultimo administrador. Si se elimina permanentemente de la tabla operativa, no puede iniciar sesion y el historial conserva usuario como texto o snapshot.

## Flujo de desacople historico para eliminacion permanente

Implementado en Fase 11H:

1. La migracion 017 rellena snapshots existentes en `ejecuciones` y `scheduler_eventos`.
2. La migracion 017 elimina FKs historicas desde `ejecuciones` hacia `tareas`, `scripts` y `scripts_versiones`.
3. La migracion 017 elimina la FK historica desde `logs_tareas` hacia `tareas`.
4. `ejecuciones.id_tarea`, `ejecuciones.id_script`, `ejecuciones.id_version` y `logs_tareas.id_tarea` quedan anulables.
5. `/papelera` valida que el desacople exista antes de permitir eliminacion permanente de tareas, scripts o versiones.
6. Antes de borrar, la app vuelve a asegurar snapshots del registro afectado.
7. La app nulifica IDs historicos que apuntan al registro operativo que se borrara.
8. Luego borra solo `programaciones`, `scripts_versiones`, `scripts` o `tareas` operativas segun corresponda.
9. `logs_tareas.id_ejecucion` se mantiene como vinculo hacia la ejecucion historica.
10. `/ejecuciones`, consola, logs y eventos siguen leyendo snapshots o texto historico.

## Flujo de revision post desacople historico

Implementado en Fase 11I:

1. Una ejecucion historica puede quedar con `id_tarea`, `id_script` e `id_version` en `NULL`.
2. `/ejecuciones` lista la ejecucion usando snapshot de tarea, script, archivo, version y usuario.
3. Si el snapshot no existe, intenta mostrar maestro operativo.
4. Si tampoco existe maestro, muestra fallback claro como `Tarea eliminada`, `Script eliminado` o `Archivo historico`.
5. `/ejecuciones/<id>` y la consola cargan por `id_ejecucion`, no por maestro operativo.
6. Los logs se consultan por `logs_tareas.id_ejecucion`; `logs_tareas.id_tarea` puede ser `NULL`.
7. `/scheduler/eventos` muestra nombre desde snapshots del evento o fallback si la tarea fue eliminada.
8. `/panel` y panel del programador no fallan si una ultima ejecucion ya no tiene tarea maestra.
9. Las vistas operativas `/tareas` y gestion de scripts siguen mostrando solo registros operativos existentes.
10. La revision no borra historial ni modifica snapshots.

## Flujo futuro de purga controlada

Pendiente para fase posterior:

1. Usuario autorizado solicita una purga controlada fuera del flujo normal de papelera.
2. El sistema exige confirmacion fuerte y validaciones de seguridad.
3. Debe existir criterio explicito de retencion y respaldo.
4. La purga elimina fisicamente solo registros permitidos por regla.
5. La accion debe quedar trazada por Auditoria.

## Flujo de Auditoria

Implementado como base en Fase 12A:

1. Una accion humana critica llega al backend.
2. El servicio registra valor anterior y valor nuevo.
3. Se guarda usuario, modulo, tabla afectada, id de registro, accion, fecha, IP y user-agent cuando aplique.
4. Auditoria se consulta desde un modulo dedicado.
5. `scheduler_eventos`, `ejecuciones`, `logs_tareas` y `logs_sistema` no reemplazan este flujo.

## Flujo de gestion de scripts por tarea

1. Usuario autorizado abre `/tareas`.
2. Selecciona `Scripts` en una tarea.
3. El sistema muestra datos de la tarea, archivo activo real y tabla de versiones.
4. Si no existe contenedor de script, el boton dice `Asociar script` y el modal informa que se creara v1 activa.
5. Si ya existe v1 o v2, el modal informa que se creara v2 o v3.
6. Si ya existen v1, v2 y v3, no se ofrece crear v4; se indica reemplazar una version existente.
7. Usuario carga archivo `.py`.
8. El backend valida extension, tamano, nombre y ruta segura.
9. Si no existe contenedor de script, lo crea con nombre `Script de {nombre_tarea}` y registra v1 activa.
10. Si ya existe, crea la siguiente version disponible hasta v3.
11. Si ya existen v1, v2 y v3, bloquea la carga directa y solicita reemplazar una version.
12. El archivo queda guardado bajo `scripts/CATEGORIA/TIPO/CLIENTE/TAREA/vX/`.
13. Solo se guardan rutas y hash en base de datos; no se ejecuta el archivo.

## Diferencia entre contenedor y archivo activo

1. `scripts.nombre_script` representa un contenedor descriptivo asociado a la tarea.
2. El archivo activo se obtiene desde la version activa en `scripts_versiones`.
3. El bloque superior muestra como protagonista `scripts_versiones.nombre_archivo` de la version activa.
4. El nombre interno del contenedor se conserva en base de datos, pero no se muestra por defecto en la vista principal.
5. Si se reemplaza la version activa, el bloque superior cambia al nuevo archivo de esa version.
6. Si se reemplaza una version no activa, el bloque superior no cambia porque la version activa sigue siendo la misma.
7. La tabla de versiones sigue mostrando el detalle completo de cada version.
8. El nombre del primer archivo cargado no define el nombre del contenedor principal.

## Flujo de version activa

1. Usuario selecciona activar una version disponible.
2. Se muestra modal corporativo.
3. Al confirmar, todas las versiones del script dejan de ser activas.
4. La version seleccionada queda `ACTIVA`.
5. `scripts.id_version_activa` apunta a esa version.
6. Futuras ejecuciones usaran esa version, cuando exista Fase 8.

## Flujo de eliminacion de script completo y version

1. El boton superior `Eliminar script completo` representa la eliminacion del contenedor de script asociado a la tarea.
2. Esa accion afecta a todo el conjunto de versiones solo si el usuario la confirma explicitamente.
3. Si el script completo no tiene historial, se eliminan registros y archivos asociados de todas sus versiones.
4. Si el script completo tiene historial, se bloquea la eliminacion fisica y se sugiere desactivarlo.
5. En la tabla de versiones, `Eliminar version` intenta eliminar solo la version de esa fila.
6. Eliminar una version nunca elimina el script completo ni las demas versiones.
7. Si la version es activa, se bloquea la eliminacion y se pide activar otra version primero.
8. Si es la unica version del script, se bloquea la eliminacion individual y se indica usar `Eliminar script completo`.
9. Si la version tiene historial, se bloquea la eliminacion fisica y se muestra mensaje amigable.
10. Todo bloqueo o eliminacion confirmada se registra en `logs_sistema` sin exponer contenido de `.env`.

## Flujo de env por version

1. Usuario abre panel `.env` de una version.
2. Marca si la version requiere `.env`.
3. Puede subir archivo `.env`.
4. Si no existe `.env`, el modal dice `Asociar archivo .env`.
5. Si ya existe `.env`, el modal dice `Reemplazar archivo .env`.
6. El backend valida tamano, nombre y ruta segura.
7. El archivo queda guardado bajo `env_scripts/CATEGORIA/TIPO/CLIENTE/TAREA/vX/.env`.
8. La base guarda solo rutas, nunca contenido.
9. Si una version requiere `.env` y no lo tiene, se muestra `Pendiente .env`.

## Estandar futuro para scripts

1. El script cargado debe leer variables usando `os.getenv()`.
2. No debe tener credenciales quemadas.
3. No debe ejecutar `load_dotenv()` con ruta fija.
4. En Fase 8 la aplicacion carga el `.env` correspondiente a la version que se ejecute.

## Flujo de login

1. Usuario abre `/login`.
2. Ingresa usuario y contrasena.
3. El backend valida primero contra `.env`.
4. Si coincide, crea sesion `SUPER_ADMIN_ENV` con permisos totales y redirige a `/panel`.
5. Si no coincide, valida contra la tabla `usuarios`.
6. Si el usuario de base de datos esta activo, no bloqueado y la contrasena coincide con el hash, carga roles/permisos y redirige a `/panel`.
7. Si falla, muestra mensaje amigable y registra evento en `logs_sistema` cuando la base de datos esta disponible.

## Flujo de administracion de usuarios

1. Usuario con `USUARIOS_ADMIN` o administrador `.env` abre `/usuarios`.
2. El sistema lista usuarios de base de datos con rol y estado.
3. Puede filtrar por estado, rol o busqueda general por usuario, nombre y correo.
4. Para crear usuario, se exige usuario unico, nombre, rol, contrasena y confirmacion.
5. Para editar usuario, se permite cambiar nombre, email, rol, estado y contrasena opcional.
6. Si cambia el rol, el formulario muestra una advertencia de permisos.
7. Si ingresa nueva contrasena, el formulario advierte que sera actualizada.
8. Para activar o desactivar usuario, se abre un modal corporativo de confirmacion antes de enviar el cambio.
9. Si el administrador cancela la confirmacion, no se ejecuta accion ni se registra log.
10. Desde Fase 11F existe borrado operativo seguro; si el usuario tiene historial, se retira de operacion y no puede iniciar sesion.
11. Cada creacion, edicion o cambio confirmado registra evento en `logs_sistema`.

## Flujo de mantenedores base

1. Usuario autorizado abre `/clientes`, `/categorias` o `/tipos`.
2. El sistema lista registros con filtros por estado y busqueda por nombre o descripcion.
3. Para crear, el usuario ingresa nombre y descripcion opcional.
4. Antes de guardar, se muestra modal corporativo de confirmacion.
5. El servicio normaliza el nombre y valida duplicados.
6. Para editar, se repite confirmacion y validacion de duplicados excluyendo el registro actual.
7. Para activar o desactivar, se solicita confirmacion por modal.
8. Para borrar, se solicita confirmacion fuerte por modal.
9. El backend valida dependencias contra `tareas`.
10. Si no tiene dependencias ni historial, elimina fisicamente y registra `logs_sistema`.
11. Si tiene dependencias o historial, asegura snapshots, marca `eliminado_operativo = 1` y registra el retiro.
12. Cada cambio confirmado registra evento en `logs_sistema`.

## Flujo de confirmacion critica

1. Usuario presiona un boton marcado como accion critica.
2. El frontend evita el envio inmediato del formulario.
3. Se abre el modal reutilizable del sistema con titulo, mensaje, tipo visual y botones configurados por `data-*`.
4. Si el usuario cancela, se cierra el modal y no se envia el formulario.
5. Si el usuario confirma, el formulario original se envia por POST al backend.
6. El backend mantiene la logica existente y registra logs solo cuando recibe una accion confirmada.

## Flujo de confirmacion al guardar usuario

1. Usuario presiona guardar en creacion o edicion de usuario.
2. El frontend intercepta el submit del formulario.
3. En creacion se muestra modal `Crear usuario`.
4. En edicion sin cambios criticos se muestra modal `Guardar cambios del usuario`.
5. Si el rol cambio, se muestra modal `Confirmar cambio de rol`.
6. Si se ingreso nueva contrasena, se muestra modal `Confirmar cambio de contrasena`.
7. Si cambia rol y contrasena al mismo tiempo, se muestra modal `Confirmar cambios criticos`.
8. Si cancela, no se envia el formulario.
9. Si confirma, se envia el POST normal y el backend guarda cambios.

## Flujo de creacion de tarea

1. Usuario autorizado abre `/tareas/nueva`.
2. Ingresa nombre, descripcion, cliente, categoria, tipo y observacion tecnica opcional.
3. Define tipo de programacion: manual, diaria, semanal, mensual o fecha especifica.
4. Si la programacion no es manual, selecciona modo `UNA_VEZ` o `INTERVALO`.
5. El formulario muestra solo los campos necesarios para el tipo y modo seleccionados.
6. Antes de guardar, el frontend valida los campos requeridos de la programacion.
7. Si la informacion esta completa, se muestra modal corporativo con resumen de la tarea.
8. El resumen muestra nombres visibles de cliente, categoria y tipo, no IDs.
9. Si el usuario cancela, no se envia el formulario.
10. Si confirma, el backend valida campos obligatorios, duplicados y reglas de programacion.
11. Si es valido, crea la tarea y una programacion activa.
12. Registra eventos en `logs_sistema`.

## Flujo de edicion de tarea

1. Usuario autorizado abre `/tareas/<id>/editar`.
2. Modifica datos base o programacion.
3. Al presionar guardar, el frontend compara el estado original contra el estado actual.
4. Si no hay cambios reales, no muestra modal, no envia el formulario y muestra `No hay cambios para guardar.`.
5. Si hay cambios, valida los campos requeridos de la programacion.
6. Se muestra modal corporativo con el resumen final de como quedara la tarea.
7. Si el usuario cancela, no se envia el formulario.
8. Si confirma, el backend valida reglas y duplicados excluyendo la tarea actual.
9. El backend vuelve a comparar datos actuales contra datos enviados.
10. Si no hay cambios, no ejecuta `UPDATE`, no registra logs y muestra `No hay cambios para guardar.`.
11. Si hay cambios, inactiva la programacion activa anterior.
12. Crea una nueva programacion activa con los cambios.
13. Registra eventos en `logs_sistema`.

## Flujo de confirmacion con resumen de tarea

1. El formulario de tarea usa el modal global reutilizable.
2. El JS toma los valores actuales del formulario antes de enviarlo.
3. Para cliente, categoria y tipo lee el texto visible de la opcion seleccionada.
4. Genera un resumen legible de programacion: manual, diaria, semanal, mensual o fecha especifica.
5. Muestra datos generales, programacion, feriados y estado.
6. El contenido del resumen se genera con nodos DOM y texto, no con HTML libre.
7. Cancelar cierra el modal sin guardar.
8. Confirmar envia el formulario y mantiene las validaciones backend existentes.

## Flujo de deteccion de cambios reales en tarea

1. Al cargar formulario de edicion, el frontend guarda una fotografia normalizada del formulario.
2. Antes de guardar compara textos normalizados, selects, checkboxes, tipo de programacion, modo, horarios, intervalo, fecha, dia de mes y dias de semana.
3. Los dias de semana se comparan como conjunto ordenado.
4. Si no hay diferencias, se muestra un mensaje inline y se detiene el envio.
5. Si hay diferencias, continua el modal de resumen de Fase 6.1.
6. El backend aplica una comparacion equivalente antes de actualizar para evitar cambios innecesarios si el JS fue omitido.

## Flujo de estado y eliminacion de tarea

1. Para activar o desactivar, el usuario confirma por modal.
2. El backend actualiza `activo` y `estado_tarea`.
3. Para borrar, el usuario confirma por modal `danger`.
4. El backend bloquea solo si existe ejecucion `EN_EJECUCION`.
5. Si no existe historial, elimina programaciones, scripts/versiones operativas y tarea.
6. Si existe historial, asegura snapshots, marca la tarea como `eliminado_operativo = 1` y la oculta de operacion normal.
7. Cada accion confirmada o intento bloqueado se registra en `logs_sistema`.

## Flujo de reglas de programacion

1. `MANUAL`: no exige hora ni calendario.
2. `DIARIA`: exige hora si es `UNA_VEZ`, o intervalo con inicio/fin si es `INTERVALO`.
3. `SEMANAL`: exige al menos un dia de semana.
4. `MENSUAL`: exige dia del mes entre 1 y 31.
5. `FECHA_ESPECIFICA`: exige fecha valida.
6. `INTERVALO`: exige intervalo mayor a 0 y hora inicio menor a hora fin.
7. `ejecutar_en_feriados` queda guardado en la programacion y desde Fase 10A el worker lo valida contra la tabla local `feriados`.

## Flujo de ejecucion automatica

Implementado en Fase 9B mediante proceso separado `scheduler_worker.py`.

1. Operador levanta la app web con `python run.py`.
2. Operador levanta el worker con `python scheduler_worker.py`.
3. Worker lee `configuracion_scheduler`.
4. Si no existe configuracion activa, registra advertencia y duerme 60 segundos.
5. Si `scheduler_activo = 0`, no evalua tareas.
6. Si `modo_mantenimiento = 1`, no inicia ejecuciones.
7. Si `permitir_ejecucion_automatica = 0`, no ejecuta tareas.
8. Si la configuracion permite ejecutar, lista tareas activas con programacion activa.
9. Evalua `DIARIA`, `SEMANAL`, `MENSUAL` y `FECHA_ESPECIFICA`.
10. `MANUAL` nunca se ejecuta automaticamente.
11. Crea `clave_programacion` por tarea, tipo, fecha y hora slot.
12. Si la clave ya existe, omite el slot.
13. Si la tarea ya tiene ejecucion `EN_EJECUCION`, la omite.
14. Si se alcanza `max_ejecuciones_concurrentes`, no inicia mas ejecuciones.
15. Si corresponde, llama al motor de Fase 8 para ejecutar version activa.
16. La ejecucion queda con `origen_ejecucion = AUTOMATICA`, `fecha_programada`, `clave_programacion` y `nombre_worker`.
17. La consola se ve en `/ejecuciones/<id_ejecucion>` y puede detenerse desde la web.

## Flujo de configuracion scheduler

Validacion local Fase 9A:

* La migracion `010_crear_configuracion_scheduler.sql` fue ejecutada correctamente en SQL Server local.
* El seed `007_permisos_scheduler.sql` fue ejecutado correctamente en SQL Server local.
* La pantalla `/scheduler/configuracion` carga correctamente.
* La edicion muestra modal corporativo con resumen de cambios.
* Guardar sin cambios muestra toast.
* Las validaciones bloquean valores fuera de rango.
* Los cambios quedan registrados en `logs_sistema`.
* No se implemento worker automatico, no se ejecutan tareas automaticas y no se conecto API de feriados.

1. Usuario autorizado abre `/scheduler/configuracion`.
2. El sistema lee la configuracion activa desde `configuracion_scheduler`.
3. Si no existe registro activo, crea un default seguro con scheduler apagado.
4. Usuario edita parametros operativos.
5. Frontend compara valores originales contra actuales.
6. Si no hay cambios, muestra toast `No hay cambios para guardar.` y no envia formulario.
7. Si hay cambios, abre modal corporativo con resumen de diferencias.
8. Backend valida intervalo entre 10 y 3600 segundos.
9. Backend valida maximo concurrentes entre 1 y 20.
10. Backend guarda cambios y registra `logs_sistema`.
11. Fase 9A no inicia worker ni ejecuta tareas automaticas.

## Uso de configuracion por worker

1. Fase 9B lee la configuracion activa desde SQL Server.
2. Si `scheduler_activo = 0`, el worker no evaluara tareas.
3. Si `modo_mantenimiento = 1`, el worker no iniciara ejecuciones nuevas.
4. Si `permitir_ejecucion_automatica = 0`, el worker podra revisar pero no ejecutar.
5. `intervalo_revision_segundos` definira cada cuanto revisa.
6. `max_ejecuciones_concurrentes` limitara ejecuciones automaticas simultaneas.
7. `nombre_worker_principal` identificara el worker.

## Flujo de panel operativo scheduler

Fase 11A agrega monitoreo de solo lectura en `/scheduler/panel`.

1. Usuario autorizado con `SCHEDULER_CONFIG_VER` abre `/scheduler/panel`.
2. El sistema lee configuracion activa desde `configuracion_scheduler`.
3. Consulta resumen de ejecuciones automaticas desde `ejecuciones`.
4. Lista ultimas ejecuciones automaticas.
5. Lista errores y advertencias recientes del modulo `SCHEDULER` en `logs_sistema`.
6. Lista tareas programadas activas candidatas.
7. Muestra estado del calendario local de feriados.
8. El panel no inicia, detiene ni reinicia el worker.
9. El panel no consulta Nager.Date ni otras APIs externas.
10. La configuracion se sigue editando solo desde `/scheduler/configuracion`.

## Ventana de tolerancia y anti-duplicados

El worker evalua una ventana entre `ahora - intervalo_revision_segundos` y `ahora`. Si un slot programado cae dentro de esa ventana, se considera ejecutable.

Ejemplos de clave:

* `TAREA_15_DIARIA_2026-06-16_08:00`.
* `TAREA_15_DIARIA_INTERVALO_2026-06-16_08:30`.

La base evita duplicados con indice unico filtrado para ejecuciones automaticas.

## Feriados

Fase 10A implementa calendario local de feriados en SQL Server. No se conecta API externa.

Validacion local Fase 10A:

* `012_crear_calendario_feriados.sql` fue ejecutada correctamente en SQL Server local.
* `008_permisos_feriados.sql` fue ejecutado correctamente en SQL Server local.
* `/feriados` carga correctamente.
* Crear, editar, activar y desactivar feriados funciona.
* No se permite duplicar fecha + pais activa.
* `es_feriado` retorna `True` con feriado activo y `False` cuando no existe feriado activo.
* El scheduler omite o permite ejecucion automatica segun `ejecutar_en_feriados`.
* La ejecucion manual no se bloquea por feriados.

1. Usuario autorizado abre `/feriados`.
2. Puede filtrar por ano, mes, pais y estado.
3. Para crear, ingresa fecha, nombre, tipo, pais, irrenunciable, activo y observacion.
4. Para editar, el sistema valida cambios y evita duplicar fecha + pais activa.
5. Si no hay cambios al editar, muestra `No hay cambios para guardar.`.
6. Activar, desactivar y eliminar usan modal corporativo.
7. Los cambios se registran en `logs_sistema`.
8. El servicio `es_feriado(fecha, pais)` consulta solo la tabla local `feriados`.
9. El scheduler consulta el feriado local antes de iniciar una ejecucion automatica.
10. Si `ejecutar_en_feriados = 0` y la fecha es feriado activo, omite la tarea y registra `WORKER_TAREA_OMITIDA_FERIADO`.
11. Si `ejecutar_en_feriados = 1`, permite la ejecucion aunque sea feriado.
12. La ejecucion manual no se bloquea por feriados.

## Flujo de sincronizacion Nager.Date

Fase 10B agrega sincronizacion controlada y manual. El scheduler no consulta internet.

1. Usuario con `FERIADOS_SINCRONIZAR` abre `/feriados/sincronizar`.
2. Selecciona ano y pais, por defecto ano actual y `CL`.
3. Presiona `Consultar feriados`.
4. La app consulta `https://date.nager.at/api/v3/PublicHolidays/{anio}/{pais}` con timeout controlado.
5. Cada feriado se normaliza hacia `fecha`, `nombre`, `pais`, `tipo`, `origen = API_NAGER`, `activo = 1` y observacion.
6. El campo `irrenunciable` se calcula usando `reglas_feriados_irrenunciables`, no desde Nager.Date.
7. Se compara contra feriados locales existentes por fecha + pais.
8. Si no existe local, la accion propuesta es `Nuevo`.
9. Si existe local `MANUAL`, se omite y no se sobrescribe.
10. Si existe local `API_NAGER` activo y cambio nombre/tipo/irrenunciable/observacion, se propone actualizar.
11. Si existe local `API_NAGER` sin cambios, queda `Sin cambios`.
12. Si existe local inactivo, se marca como revision y no se reactiva automaticamente.
13. Usuario confirma con modal corporativo `Aplicar sincronizacion de feriados`.
14. Backend revalida contra estado local antes de insertar o actualizar.
15. Se registra resultado en `logs_sistema`.
16. La tabla `feriados` sigue siendo fuente final para `servicio_calendario.es_feriado()`.

## Flujo de ejecucion manual

Validacion local Fase 8:

* El seed `006_permisos_ejecuciones.sql` fue ejecutado correctamente en SQL Server local.
* Se valido ejecucion manual con script activo, consola, polling, estado `EXITOSA`, detencion `DETENIDA_MANUALMENTE`, PID y archivo de log.
* Se probo ejecucion sin `.env` y con `.env` de prueba cargado mediante `os.getenv()`.
* No se mostraron secretos, no se implemento scheduler automatico y no se conecto API de feriados.

1. Usuario autorizado presiona `Ejecutar ahora` desde `/tareas` o desde la pantalla de scripts.
2. Se muestra modal corporativo indicando tarea, script activo, version activa y que no se usara scheduler.
3. Al confirmar, el servicio valida tarea activa, script activo, version activa y archivo `.py` fisico.
4. Si la version requiere `.env`, valida que exista archivo `.env` asociado.
5. Si ya existe una ejecucion `EN_EJECUCION` para la misma tarea, bloquea la nueva ejecucion.
6. Crea registro en `ejecuciones` con origen `MANUAL` y estado `EN_EJECUCION`.
7. Crea archivo de log en `logs_tareas/AAAA/MM/DD/`.
8. Crea registro en `logs_tareas` con rutas del log.
9. Ejecuta el script con el interprete Python actual y `subprocess` sin `shell=True`.
10. Registra `pid_proceso`.
11. Redirige a `/ejecuciones/<id_ejecucion>`.
12. La consola consulta `/ejecuciones/<id_ejecucion>/log` cada 3 segundos.
13. Si el proceso termina con codigo 0, marca `EXITOSA`.
14. Si termina con codigo distinto de 0 o error controlado, marca `ERROR`.
15. No se muestran secretos ni contenido del `.env`.

## Formato de logs de ejecucion

Desde Fase 9C cada linea del archivo de log y de la consola usa:

```text
YYYY-MM-DD HH:mm:ss | NIVEL | mensaje
```

Reglas:

1. Inicio, origen, tarea, script, version, `.env`, PID, codigo de salida y estado final usan timestamp.
2. Cada linea emitida por el script se escribe con timestamp.
3. La salida stdout/stderr se captura combinada; se marca como `INFO` por defecto.
4. Errores de plataforma y codigo de salida distinto de cero se registran como `ERROR`.
5. La detencion manual registra lineas `WARN` e incluye usuario, PID y si fue forzada.
6. La plataforma no muestra contenido de `.env`; si un script imprime secretos por su cuenta, debe corregirse el script.
7. Si el script ya imprime timestamp propio, Fase 9C igualmente antepone timestamp de plataforma para estandarizar la trazabilidad.

## Historial de ejecuciones agrupado

Fase 9D cambia `/ejecuciones` a una vista historica agrupada:

1. Usuario autorizado con `EJECUCIONES_VER` abre `/ejecuciones`.
2. Backend valida filtros GET y corrige valores invalidos con defaults seguros.
3. SQL Server ejecuta consulta paginada con `OFFSET/FETCH`.
4. La consulta trae solo la pagina actual.
5. SQL Server ejecuta `COUNT` con los mismos filtros.
6. SQL Server calcula resumen por estado con los mismos filtros.
7. Python agrupa solo los registros de la pagina actual por ano, mes y dia.
8. La vista muestra ano, mes `MM - Nombre`, dia y ejecuciones compactas.
9. La paginacion conserva filtros en la URL.

Orden default:

```text
fecha_hora_inicio DESC, id_ejecucion DESC
```

Filtros disponibles: ID ejecucion, tarea, origen, estado, ano, mes, dia, fecha desde, fecha hasta, usuario y worker.

## Flujo de ejecucion con env por script

1. Servicio resuelve tarea, contenedor de script y version exacta.
2. Valida que el archivo `.py` exista y pertenezca a rutas permitidas.
3. Revisa `scripts_versiones.requiere_env`.
4. Si no requiere `.env`, continua ejecucion normal.
5. Si requiere `.env`, valida `ruta_env_fisica` y `ruta_env_relativa`.
6. Si falta el `.env`, marca ejecucion como `ERROR` controlado antes de iniciar proceso.
7. Si existe, carga variables en el entorno del proceso sin guardar ni imprimir secretos.
8. Inicia proceso, registra `pid_proceso` y estado `EN_EJECUCION`.
9. Captura salida hacia `logs_tareas`.
10. Al terminar, actualiza estado final, duracion, codigo de salida y logs.

## Flujo de detencion manual de ejecucion

1. Usuario autorizado visualiza una ejecucion `EN_EJECUCION`.
2. Interfaz muestra boton `Detener ejecucion`.
3. Usuario presiona detener y el sistema muestra modal corporativo de confirmacion.
4. Si cancela, no se ejecuta accion ni se registran cambios.
5. Si confirma, el backend valida permisos y estado actual.
6. Servicio intenta detener el proceso de forma controlada usando `pid_proceso`.
7. Si el proceso no responde, se fuerza termino y se marca `fue_detencion_forzada = 1`.
8. Se actualiza `ejecuciones` con usuario, fecha/hora y motivo de detencion.
9. Se registra evento en `logs_tareas`.
10. Se registra evento en `logs_sistema`.
11. La consola muestra estado detenido y mensaje amigable.

## Flujo de reemplazo de script

Propuesta documental Fase 3A; implementacion pendiente para Fase 7.

## Flujo de carga de primera version

1. Usuario crea o edita una tarea.
2. El sistema crea el contenedor en `scripts` con nombre `Script de {nombre_tarea}`.
3. Usuario carga archivo `.py`.
4. Servicio valida extension, nombre seguro, ruta permitida y hash.
5. Se crea `scripts_versiones` con `numero_version = 1`, `estado_version = ACTIVA`, `es_activa = 1`.
6. `scripts.id_version_activa` queda apuntando a la version 1.
7. Se registra evento en `logs_sistema` y `auditoria_cambios`.

## Flujo de carga de segunda o tercera version

1. Usuario selecciona una tarea con contenedor de script existente.
2. Servicio cuenta versiones disponibles del `id_script`.
3. Si existen menos de 3, permite cargar nueva version.
4. Se asigna el siguiente `numero_version` disponible.
5. La nueva version queda `DISPONIBLE` por defecto, salvo que el usuario confirme activarla.
6. Si se activa, la version anterior pasa a `DISPONIBLE`, y solo una queda `ACTIVA`.
7. Se registra auditoria con hash, usuario, fecha y rutas.

## Flujo cuando ya existen 3 versiones

1. Usuario intenta cargar otra version.
2. Servicio detecta 3 versiones disponibles.
3. Sistema impide carga directa.
4. Sistema solicita seleccionar una version existente para reemplazar.
5. Si cancela, no se modifica nada.
6. Si confirma, se ejecuta flujo de reemplazo de version.

## Flujo para seleccionar version activa

1. Usuario visualiza versiones disponibles del script.
2. Selecciona una version como activa.
3. Sistema muestra confirmacion indicando version actual y version nueva.
4. Servicio desmarca `es_activa` en las demas versiones.
5. Servicio marca la version seleccionada como `ACTIVA` y actualiza `scripts.id_version_activa`.
6. Se registra auditoria con valor anterior y valor nuevo.

## Flujo para ejecucion automatica con version activa

1. Scheduler selecciona tareas activas segun programacion.
2. Servicio obtiene `scripts.id_version_activa`.
3. Valida que la version exista, este activa/disponible y el archivo exista.
4. Crea registro en `ejecuciones` con `id_script` e `id_version`.
5. Ejecuta el archivo de `scripts_versiones.ruta_fisica`.
6. Registra resultado y log asociado a `id_ejecucion`.

## Flujo para ejecucion manual seleccionando version

1. Usuario abre tarea.
2. Sistema muestra version activa y versiones disponibles.
3. Usuario elige version activa o una version especifica.
4. Si elige una version distinta a la activa, sistema muestra advertencia y pide confirmacion.
5. Si cancela, no ejecuta.
6. Si confirma, crea `ejecuciones` con `id_script` e `id_version`.
7. Se ejecuta la version elegida y se registra log.

## Flujo de reemplazo de version

1. Usuario selecciona version existente a reemplazar.
2. Sistema muestra advertencia con numero de version, hash actual y fecha de carga.
3. Usuario carga nuevo archivo `.py`.
4. Servicio valida archivo, ruta, nombre seguro y hash.
5. Servicio registra auditoria del valor anterior.
6. Version anterior cambia a `REEMPLAZADA`; no se elimina fisicamente desde la app.
7. Nueva informacion de version queda registrada en `scripts_versiones`.
8. Si la version reemplazada era activa, el sistema debe confirmar si la nueva queda activa.

## Flujo para deshabilitar version

1. Usuario selecciona una version disponible.
2. Sistema muestra confirmacion indicando que no se borrara fisicamente el archivo.
3. Si confirma, servicio cambia `estado_version` a `INACTIVA`.
4. Si la version era activa, el sistema debe exigir seleccionar otra version activa antes de completar la operacion.
5. Se registra evento en `logs_sistema`.
6. Se registra cambio en `auditoria_cambios` con estado anterior y nuevo.
7. El archivo fisico permanece disponible para trazabilidad y revision historica.

## Flujo de auditoria de cambios de version

1. Toda carga, activacion, inactivacion o reemplazo genera registro en `auditoria_cambios`.
2. `tabla_afectada` debe ser `scripts` o `scripts_versiones`.
3. `valor_anterior` debe guardar numero de version, hash, ruta, estado y usuario previo cuando aplique.
4. `valor_nuevo` debe guardar numero de version, hash, ruta, estado y usuario nuevo.
5. Tambien se registra evento operativo en `logs_sistema`.

## Flujo de logs

Pendiente para Fase 9.

## Flujo de auditoria

Pendiente para Fase 12. Ver `Flujo futuro de Auditoria`.
