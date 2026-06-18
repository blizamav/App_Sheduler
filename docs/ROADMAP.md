# Roadmap APP Scheduler

## Estado Actual

El proyecto se encuentra en Fase 11F con robustez operativa interna avanzada. APP Scheduler ya no es un prototipo: cuenta con autenticacion, seguridad por permisos, mantenedores, tareas programables, scripts versionados, ejecucion manual, ejecucion automatica, consola, historial, calendario de feriados, paneles operativos, eventos del programador, control de ejecuciones huerfanas y borrado operativo seguro con snapshots.

## Implementado

* Login hibrido: administrador desde `.env` y usuarios desde SQL Server.
* Usuarios, roles y permisos.
* Mantenedores de clientes, categorias y tipos.
* Tareas programables con programacion manual, diaria, semanal, mensual y fecha especifica.
* Scripts versionados por tarea, con hasta tres versiones.
* `.env` por version de script, guardando solo rutas y nunca contenido.
* Ejecucion manual con validacion de tarea, script, version activa, archivo fisico, `.env` requerido y ejecucion en curso.
* Consola de ejecucion con polling.
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
* TOP 6 ultimas ejecuciones en panel principal.

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
* 11G Papelera operativa y restauracion. Pendiente.
* 11H Purga controlada. Pendiente.
* 11I Revision integral post-borrado. Pendiente.

## Fase 12 - Auditoria

Estado: pendiente. No debe confundirse con logs operativos, ejecuciones ni eventos del programador.

* 12A Modulo Auditoria base. Pendiente.
* 12B Auditoria aplicada a acciones criticas. Pendiente.
* 12C Filtros, detalle y trazabilidad extendida. Pendiente.

## Fase 13 - Operacion y Despliegue

Estado: pendiente. Debe abordarse despues de cerrar la robustez interna y definir Auditoria base.

* 13A Scripts operativos Windows/Linux. Pendiente.
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
* Falta implementar papelera operativa.
* Falta implementar restauracion.
* Falta implementar purga controlada.

## Auditoria Pendiente

Auditoria funcional sigue pendiente para Fase 12.

Distinciones obligatorias:

* `scheduler_eventos` registra decisiones automaticas del programador.
* `ejecuciones` registra intentos reales de ejecutar scripts.
* `logs_sistema` registra eventos operativos basicos.
* Ninguno de los anteriores reemplaza Auditoria.
* `auditoria_cambios` debe registrar acciones humanas relevantes en una fase posterior, con valores antes/despues, usuario, fecha, modulo e identificador afectado.

## Checklist Pendiente

Pendiente critico inmediato:

* Fase 11G Papelera operativa y restauracion.
* Fase 11H Purga controlada.
* Fase 11I Revision integral post-borrado.
* Fase 12A Auditoria.

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

La proxima fase recomendada es Fase 11G: Papelera operativa y restauracion. Debe permitir consultar registros retirados operativamente, revisar su contexto y restaurarlos de forma controlada cuando sea seguro. No debe implementar Auditoria ni purga fisica.
