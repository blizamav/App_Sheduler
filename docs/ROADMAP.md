# Roadmap APP Scheduler

## Objetivo actual

Reconstruir APP Scheduler desde una base limpia, conservando requisitos aprobados y eliminando deuda, parches y arquitectura deprecada. La implementacion actual permanece como referencia hasta el cutover validado.

Fuentes maestras:

* `docs/INVENTARIO_MAESTRO_RECONSTRUCCION.md`
* `docs/ARQUITECTURA_RECONSTRUCCION.md`

## Completado

### Hito 0 - Inventario y arquitectura

Estado: CERRADO.

* Proyecto, documentacion, SQL, configuracion, UI, pruebas e historial Git relevante inventariados.
* Funcionalidades clasificadas como conservar, reimplementar, refactorizar, deprecar o descartar.
* Contradicciones entre codigo y documentacion identificadas.
* Arquitectura objetivo, estrategia de reemplazo y limites de cada runtime definidos.
* Factory Reset blue-green confirmado como deprecado; in-place confirmado como arquitectura vigente.
* No se inicio implementacion funcional, no se ejecuto SQL y no se modificaron secretos.

### Hito 1 - Base del proyecto y configuracion

Estado: CERRADO.

* Paquete aislado `src/app_scheduler/` con fabrica Flask y bootstrap web/worker.
* Configuracion tipada y validada por capacidad para LOCAL y QA Docker.
* Errores centralizados, logging sanitizado, sesiones endurecidas y CSRF global.
* Conexion SQL Server inyectable, repositorio tecnico minimo y unidad de trabajo explicita.
* Shell visual base, tokens CSS y JavaScript modular sin migrar pantallas funcionales.
* 23 pruebas nuevas; suite completa de 49 pruebas aprobada.
* Build Docker y bootstraps efimeros web/worker aprobados sin SQL.
* Runtime historico permanece activo; no hubo cutover.

### Hito 2 - Base de datos y repositorios

Estado: CERRADO.

Inventariar el modelo limpio de 33 tablas y consolidar DTO, mapeadores, transacciones y repositorios fundacionales sobre la infraestructura de Hito 1. No activa modulos web ni consulta QA.

Validacion final: delta QA 462/bootstrap 456 reconciliado como seis columnas de auditoria reemplazadas; 22 pruebas nuevas de Hito 2 y 71 pruebas totales aprobadas.

### Hito 3 - Autenticacion, usuarios, roles y permisos

Estado: CERRADO.

Login hibrido, `SUPER_ADMIN_ENV`, usuarios SQL, sesion minima, autorizacion backend, administracion de usuarios, consulta de roles/permisos y auditoria canonica implementados y validados en `src/app_scheduler/`. La reconstruccion sigue aislada y no existe cutover.

## Pendiente

### Hito 4 - Clientes, categorias y tipos

Estado: NO INICIADO.

Reimplementar mantenedores, estados, validaciones, dependencias y auditoria.

### Hito 5 - Tareas, scripts, versiones y `.env`

Reimplementar agregado de tarea, maximo tres versiones, version activa, archivos seguros y configuracion por version.

### Hito 6 - Programaciones, scheduler y worker

Reimplementar programaciones, candidatos, heartbeat, feriados, eventos y coordinacion de mantenimiento.

### Hito 7 - Motor de ejecucion manual y automatica

Unificar ambos origenes en un motor propiedad del worker, con reclamo atomico, PID, detencion y recuperacion.

### Hito 8 - Logs, consola y evidencias

Reimplementar salida incremental, archivos, estados, contrato stdout de evidencia y trazabilidad por version.

### Hito 9 - Papelera y auditoria

Reimplementar retiro, restauracion, eliminacion permanente y auditoria transversal sin residuos fisicos.

### Hito 10 - Feriados y notificaciones Graph

Reimplementar calendario local, sincronizacion manual Nager.Date, configuracion Graph, evidencias y alertas.

### Hito 11 - Factory Reset in-place

Reimplementar prechecks, lock, cuarentena, runner transaccional, validacion SQL y recuperacion sin bases auxiliares.

### Hito 12 - UI/UX y responsive final

Conservar identidad visual y dividir CSS/JS por componentes y modulos; validar accesibilidad y viewports.

### Hito 13 - Docker QA

Validar imagen reproducible, servicios web/worker, `.env.docker`, volumenes, healthchecks, ODBC y SQLCMD.

### Hito 14 - QA integral

Ejecutar pruebas end-to-end, permisos, scheduler, worker, filesystem, Graph controlado y Factory Reset autorizado.

### Hito 15 - Documentacion y cierre

Actualizar README, modulos, operaciones, despliegue, seguridad, QA, changelog y bitacora; registrar pendientes productivos reales.

## Reglas permanentes

* Una sola base: `APP_SCHEDULER_QA`.
* `.env` para LOCAL y `.env.docker` para Docker QA.
* `database/release/` es protegido y de solo lectura.
* No ejecutar SQL destructivo ni Factory Reset sin autorizacion explicita.
* No cerrar hitos con residuos no justificados.
* No marcar QA como validado solo por compilar o pasar mocks.
* Staging Git explicito; no usar `git add -A`.
