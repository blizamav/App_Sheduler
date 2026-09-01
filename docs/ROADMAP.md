# Roadmap APP Scheduler

## Estado final

**RECONSTRUCCION COMPLETADA - v1.0.1.** El runtime oficial es
`src/app_scheduler/`; Docker, Web y Worker usan exclusivamente los entrypoints
reconstruidos. El runtime historico se conserva como referencia y no forma
parte de la operacion oficial.

## Hitos

| Hito | Alcance | Estado |
|---:|---|---|
| 0 | Inventario, reglas, arquitectura objetivo y estrategia de reemplazo | CERRADO |
| 1 | Paquete base, configuracion tipada, logging, CSRF y shell visual | CERRADO |
| 2 | Contrato SQL, DTO, mapeadores, repositorios y unidad de trabajo | CERRADO |
| 3 | Autenticacion hibrida, usuarios, roles y permisos | CERRADO |
| 4 | Clientes, categorias y tipos | CERRADO |
| 5 | Tareas, scripts, versiones y `.env` por version | CERRADO |
| 6 | Programaciones, Scheduler, reserva automatica y heartbeat | CERRADO |
| 7 | Cola, claim atomico, motor unico, logs, consola y evidencia base | CERRADO |
| 8 | Observabilidad y configuracion operativa | CERRADO |
| 9 | Auditoria y Papelera | CERRADO |
| 10 | Feriados, Nager.Date, notificaciones y Microsoft Graph | CERRADO |
| 11 | Factory Reset in-place seguro | CERRADO |
| 12 | UI/UX responsive final | CERRADO |
| 13 | Docker QA con runtime reconstruido | CERRADO |
| 14 | QA integral real: reset, manual, automatica, Graph y seguridad | CERRADO |
| 15 | Cutover documental, versionado y release v1.0.0 | CERRADO |

## Resultado v1.0.0

* Web oficial: `python -m app_scheduler.web`.
* Worker oficial: `python -m app_scheduler.worker.aplicacion`.
* Modo diagnostico de cola: `--queue-only` y `--queue-only --once`.
* Docker Compose ejecuta solo Web y Worker reconstruidos y carga
  `.env.docker` de forma explicita.
* Base unica: `APP_SCHEDULER_QA`.
* Factory Reset: in-place, transaccional, con lock y rollback.
* Contrato bootstrap: 33 tablas, 457 columnas, 25 FK, 39 CHECK, 118 DEFAULT y
  120 indices; marca `BOOTSTRAP_SQL=19C.0`.
* QA Hito 14: Factory Reset real, flujos manual/automatico, recuperacion de
  cola, Papelera, seguridad, UI responsive y un unico envio Graph at-most-once.
* Estado operativo posterior al gate: Scheduler OFF, Graph efectivo OFF y sin
  ejecuciones pendientes o en curso.

## Post v1.0.0 / futuro

El parche `v1.0.1` cierra la deuda UX de Microsoft Graph y corrige el modelo de
comunicaciones: disponibilidad contextual, advertencia no bloqueante,
trazabilidad segura, refresh completo y separacion entre exito, alerta y
Evidencia cliente. No modifica el motor Graph ni el Worker/Scheduler. La
migracion incremental `023` aplica el desacople en bases existentes y el
bootstrap canonico `19C.1` lo crea directamente en instalaciones limpias y
Factory Reset futuros.

Deuda real no bloqueante:

* estudiar lease o politica de recuperacion para una ejecucion que queda
  `EN_EJECUCION` tras una caida abrupta del Worker;
* mantener como regla que no exista auto-retry hasta poder garantizar que un
  script no producira efectos duplicados;
* evaluar retry durable de notificaciones y adjuntos Graph grandes solo bajo un
  contrato operativo nuevo;
* una sincronizacion automatica de feriados requeriria una politica propia; el
  scheduler v1.0.0 consume exclusivamente el calendario SQL local.

No existen fases adicionales obligatorias para considerar publicada v1.0.0.
