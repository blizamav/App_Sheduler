# Roadmap APP Scheduler

## Estado Actual

El proyecto incorpora Fase 13A como consolidacion SQL de release limpio para instalar `APP_SCHEDULER_QA` desde cero y Fase 13A.1B como limpieza parametrizable de eventos del scheduler. No se avanza a Fase 13B, Fase 14 ni fases posteriores.

## Implementado

* Login hibrido: administrador desde `.env` y usuarios desde SQL Server.
* Usuarios, roles y permisos.
* Mantenedores de clientes, categorias y tipos.
* Tareas programables con programacion manual, diaria, semanal, mensual y fecha especifica.
* Scripts versionados por tarea, con hasta tres versiones.
* `.env` por version de script, guardando solo rutas y nunca contenido.
* Ejecucion manual con validacion de tarea, script, version activa, archivo fisico, `.env` requerido y ejecucion en curso.
* Cierre garantizado de ejecucion manual: `EXITOSA`, `ERROR` o `DETENIDA_MANUALMENTE`.
* Consola de ejecucion con polling y sincronizacion visual de estado sin refresh completo.
* Detencion manual de ejecuciones.
* Historial de ejecuciones agrupado, filtrable y paginado.
* Scheduler automatico mediante `scheduler_worker.py` como proceso separado.
* Configuracion operativa del programador en SQL Server.
* Heartbeat del worker.
* Feriados locales como fuente de verdad del programador.
* Sincronizacion manual controlada desde Nager.Date.
* Eventos del programador en `scheduler_eventos`.
* Resumen inteligente de eventos del programador.
* Historial filtrable de eventos del programador.
* UI/UX modernizada.
* Control de ejecuciones huerfanas por verificacion de PID.
* Borrado operativo seguro con snapshots.
* Papelera operativa en `/papelera`.
* Restauracion de registros retirados como inactivos.
* Eliminacion permanente segura desde papelera.
* Eliminacion permanente masiva segura desde papelera, item por item y con resumen auditado.
* Desacople historico para que la eliminacion permanente pueda borrar filas operativas sin borrar historia.
* Revision post-desacople para que `/ejecuciones`, consola, paneles y eventos usen snapshots y fallback historico.
* Auditoria base en `/auditoria` con filtros, paginacion, detalle y servicio central `registrar_auditoria(...)`.
* Correccion visual del detalle de auditoria y reglas criticas `SUPER_ADMIN`/`ADMIN`.
* TOP 6 ultimas ejecuciones en panel principal.
* Release SQL limpio en `database/release/` para instalacion desde cero.
* Reduccion de ruido y limpieza controlada de `scheduler_eventos`.
* Limpieza parametrizable de eventos con whitelist y previsualizacion.

## Fase 11 - Robustez Operativa Interna

Estado: parcialmente implementada. La fase concentra estabilidad, trazabilidad operativa y manejo seguro del ciclo de vida de registros antes de Auditoria y despliegue.

* 11A Panel operativo scheduler. Implementado.
* 11A.1 Panel principal real. Implementado.
* 11B Heartbeat worker. Implementado.
* 11C Modernizacion visual UI/UX. Implementado.
* 11D Eventos y omisiones del programador. Implementado.
* 11D.1 Resumen inteligente eventos. Implementado.
* 11D.2 Historial filtrable eventos. Implementado.
* 11E Control ejecuciones huerfanas. Implementado.
* 11F Borrado operativo seguro con snapshots. Implementado.
* 11G Papelera operativa, restauracion y eliminacion permanente segura. Implementado.
* 11H Desacople historico para eliminacion permanente real. Implementado.
* 11I Revision integral post-borrado. Implementado.

## Fase 12 - Auditoria

Estado: parcialmente implementada. No debe confundirse con logs operativos, ejecuciones ni eventos del programador.

* 12A Modulo Auditoria base. Implementado.
* 12A.1 Correccion visual de Auditoria y reglas criticas de roles. Implementado.
* 12B Auditoria aplicada a acciones criticas. Implementado.
* 12B.1A Cierre garantizado de ejecucion manual. Implementado.
* 12B.1B Sincronizacion visual de consola sin recarga completa. Implementado.
* 12B.1C Pruebas reales intensivas de ejecucion manual. En validacion; bloqueada en entorno Codex por login requerido y error ODBC local.
* 12B.1D Modernizacion visual general y layout responsive. Implementado en shell y componentes compartidos; validacion visual interna pendiente con sesion autenticada.
* 12B.1D-Papelera Eliminacion permanente masiva segura. Implementado como correccion funcional acotada; no cambia reglas individuales ni avanza roadmap.
* 12B.1E Rediseno visual profundo del shell y experiencia UI general. Implementado en app shell compartido sin cambios funcionales.
* 12B.1F Correccion definitiva del sidebar, eliminacion del encabezado redundante y limpieza visual de tablas. Implementado sin cambios funcionales.
* 12B.2 Validacion real del scheduler_worker / Programador automatico. En validacion; bloqueada en entorno Codex por error ODBC local. Correcciones acotadas aplicadas al cierre de ejecucion automatica y robustez de heartbeat.
* 12C Filtros, detalle y trazabilidad extendida. Pendiente.

## Fase 13 - Operacion y Despliegue

Estado: iniciada con consolidacion SQL limpia. El resto de operacion y despliegue sigue pendiente.

* 13A Consolidacion SQL release limpio e instalacion desde cero. Implementado.
* 13A.1 Optimizacion y limpieza controlada de eventos del scheduler. Implementado.
* 13A.1B Limpieza parametrizable de eventos del scheduler. Implementado.
* 13A.2 Scripts operativos Windows/Linux. Pendiente.
* 13B Preparacion QA Linux. Pendiente.
* 13C Preparacion produccion. Pendiente.
* 13D Worker como servicio. Pendiente.
* 13E Docker Compose o systemd. Pendiente.

## Fase 14 - Mantenimiento Avanzado

Estado: pendiente. Incluye automatizaciones de operacion continua y salidas de informacion.

* 14A Retencion automatica. Pendiente.
* 14B Backups. Pendiente.
* 14C Exportaciones. Pendiente.
* 14D Notificaciones. Pendiente.
* 14E Reportes de operacion. Pendiente.

## Borrado Operativo Seguro

El borrado operativo seguro retira un registro de la operacion normal sin destruir historia. Cuando una entidad tiene historial o dependencias historicas, la aplicacion marca `eliminado_operativo = 1`, desactiva el registro y guarda metadatos de retiro.

Reglas:

* `eliminado_operativo` no elimina fisicamente la fila de la base de datos.
* El registro retirado desaparece de listados operativos, selects, metricas principales y candidatos del programador.
* Las ejecuciones, logs y eventos historicos deben seguir visibles.
* Los snapshots conservan nombres y contexto historico aunque el maestro sea retirado.
* Si no hay historial y no se rompe integridad, algunas entidades pueden eliminarse fisicamente.
* Papelera operativa implementada en Fase 11G.
* Restauracion controlada implementada en Fase 11G.
* Falta implementar purga controlada.

## Fase 11G - Papelera Operativa

La papelera operativa implementada en `/papelera` muestra registros con `eliminado_operativo = 1` y permite dos acciones:

* Restaurar.
* Eliminar permanentemente.

Restaurar devuelve el registro a la operacion normal cuando sea seguro. Debe dejar `activo = 0` salvo que una regla especifica futura indique lo contrario, para que el usuario reactive manualmente si corresponde.

Eliminar permanentemente no significa borrar historial. Significa eliminar fisicamente el registro de tablas operativas o maestras cuando sea seguro y cuando no se rompan claves foraneas.

Debe desaparecer de:

* `/papelera`.
* `/tareas`.
* `/scripts`.
* `/usuarios`.
* `/clientes`.
* `/categorias`.
* `/tipos`.
* Selects operativos.
* Candidatos del scheduler.
* Paneles operativos.
* Tablas maestras si las FK lo permiten.

Nunca debe eliminar:

* `ejecuciones`.
* `logs_tareas`.
* `logs_sistema`.
* `scheduler_eventos`.
* Snapshots historicos.
* `auditoria_cambios` futura.
* Archivos de log historicos necesarios para trazabilidad.

Antes de eliminar permanentemente debe mostrarse modal corporativo fuerte con este texto base:

```text
Advertencia: esta acción eliminará permanentemente el registro de las tablas operativas. Ya no aparecerá en mantenedores, papelera, selects ni paneles operativos. El historial de ejecuciones, logs, eventos del programador y snapshots históricos se conservará. Esta acción no se puede deshacer desde la aplicación.
```

Botones:

* Cancelar.
* Eliminar permanentemente.

No se deben usar `alert()`, `window.confirm()` ni `prompt()`.

Si la eliminacion fisica es segura:

* Ejecutar `DELETE` solo sobre tablas operativas o maestras correspondientes.
* No usar `DELETE CASCADE` destructivo.
* No borrar registros historicos.
* No borrar logs.
* No borrar ejecuciones.
* No borrar `scheduler_eventos`.
* No borrar snapshots.
* El registro debe dejar de aparecer en `/papelera`.

Si la eliminacion fisica no es segura:

* No forzar `DELETE`.
* No romper FK.
* Mantener `eliminado_operativo = 1`.
* Mostrar mensaje claro:

```text
No fue posible eliminar permanentemente este registro porque aún existen dependencias operativas no históricas. El registro seguirá en papelera y oculto de la operación normal.
```

## Fase 11H - Desacople Historico Para Eliminacion Permanente

Implementado. La causa tecnica que impedia la eliminacion permanente real era que `ejecuciones` y `logs_tareas` mantenian claves foraneas historicas contra `tareas`, `scripts` y `scripts_versiones`. Esas relaciones bloqueaban el borrado fisico de registros ya retirados aunque existieran snapshots.

Decision aplicada:

* `ejecuciones.id_tarea`, `ejecuciones.id_script`, `ejecuciones.id_version` y `logs_tareas.id_tarea` pasan a ser referencias historicas anulables.
* Se eliminan las FKs historicas desde `ejecuciones` hacia `tareas`, `scripts` y `scripts_versiones`.
* Se elimina la FK historica desde `logs_tareas` hacia `tareas`.
* Se mantiene la FK `logs_tareas.id_ejecucion -> ejecuciones.id_ejecucion`.
* Se mantienen las FKs operativas entre `programaciones`, `scripts`, `scripts_versiones` y sus maestros mientras las filas existan.
* La app nulifica referencias historicas antes de borrar fisicamente filas operativas desde `/papelera`.

Archivos agregados:

* `database/migrations/017_desacople_historico_papelera.sql`.
* `database/diagnostics/003_diagnostico_desacople_historico.sql`.

La migracion debe ejecutarse manualmente en SSMS despues de la migracion 016 y del seed 011. Codex no ejecuto SQL.

## Auditoria

## Fase 11I - Revision Integral Post-Borrado

Implementado. Se revisaron las consultas historicas posteriores al desacople de Fase 11H para evitar que ejecuciones con `id_tarea`, `id_script` o `id_version` en `NULL` desaparezcan de listados o detalle.

Cambios aplicados:

* `/ejecuciones` y `/ejecuciones/<id>` usan `LEFT JOIN`, snapshots y fallback explicito para tarea, cliente, categoria, tipo, script, archivo, version y usuario.
* La consola muestra indicador discreto `Snapshot historico` y estado de maestro cuando la tarea/script/version ya no existe.
* `/panel`, panel del programador y `/scheduler/eventos` usan fallback `Tarea eliminada` cuando el maestro operativo no existe.
* Se agrega diagnostico manual `database/diagnostics/004_validacion_post_desacople_historico.sql`.

No se crean migraciones nuevas, no se ejecuta SQL desde Codex. Auditoria fue implementada posteriormente en Fase 12A.

Distinciones obligatorias:

* `scheduler_eventos` registra decisiones automaticas del programador.
* `ejecuciones` registra intentos reales de ejecutar scripts.
* `logs_sistema` registra eventos operativos basicos.
* Ninguno de los anteriores reemplaza Auditoria.
* `auditoria_cambios` registra acciones humanas relevantes desde Fase 12A, con valores antes/despues, usuario, fecha, modulo e identificador afectado cuando aplica.

## Checklist Pendiente

Pendiente critico inmediato:

* Fase 12C Auditoria extendida.

Pendiente operativo:

* Scripts para levantar web y worker.
* Worker como servicio.
* Preparacion QA/produccion.
* Estrategia de backups.
* Estrategia de retencion automatica.

Pendiente mejora:

* Exportacion de eventos.
* Notificaciones.
* Reportes.
* Dashboard avanzado.

## Proxima Fase Recomendada

La proxima fase recomendada es Fase 12C: trazabilidad extendida de Auditoria, solo cuando se autorice explicitamente.
