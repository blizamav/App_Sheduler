# Modulos APP Scheduler v1.0.0

## Fuente oficial

La implementacion vigente vive en `src/app_scheduler/`. Las carpetas `app/`,
`run.py` y `scheduler_worker.py` son legado preservado y no deben usarse como
runtime, referencia de rutas nuevas ni fuente de reglas actuales.

## Entradas

| Componente | Entry point | Responsabilidad |
|---|---|---|
| Web | `python -m app_scheduler.web` | Fabrica Flask, rutas, sesion y UI |
| Worker | `python -m app_scheduler.worker.aplicacion` | Scheduler y consumo de cola |
| Worker queue-only | `python -m app_scheduler.worker.aplicacion --queue-only` | Consume cola sin evaluar programaciones |
| Ciclo controlado | `python -m app_scheduler.worker.aplicacion --queue-only --once` | Un ciclo de claim y espera de cierre |

## Capas

| Capa | Ruta | Contenido |
|---|---|---|
| Bootstrap | `src/app_scheduler/aplicacion.py`, `web.py` | Fabrica, registro de modulos y CLI |
| Configuracion | `src/app_scheduler/configuracion.py` | Variables tipadas y validacion por capacidad |
| Compartido | `src/app_scheduler/compartido/` | SQL, UoW, CSRF, autorizacion, auditoria, logging y filesystem |
| Casos de uso | `src/app_scheduler/modulos/*/casos_uso.py` | Reglas y coordinacion transaccional |
| HTTP | `src/app_scheduler/modulos/*/rutas.py` | Blueprints, validacion request y respuestas |
| Persistencia | `src/app_scheduler/persistencia/` | DTO/mapeadores y repositorios pyodbc parametrizados |
| Presentacion | `src/app_scheduler/presentacion/` | Jinja, Bootstrap local, CSS y JavaScript modular |
| Worker | `src/app_scheduler/worker/` | Scheduler, cola, motor, procesos, evidencia y servicio |

## Modulos funcionales

| Modulo | Ruta principal | Responsabilidad |
|---|---|---|
| Base | `/`, `/salud` | Panel, contexto de version y health Web |
| Autenticacion | `/login`, `/logout` | Login hibrido y sesion minima |
| Usuarios | `/usuarios/` | Alta, edicion, estado y roles |
| Seguridad | `/roles-permisos/` | Matriz de roles y permisos |
| Catalogos | `/clientes/`, `/categorias/`, `/tipos/` | Mantenedores base |
| Tareas | `/tareas/` | Datos, flujo guiado y configuracion |
| Scripts | `/scripts/`, detalle por tarea | Hub, versiones, activacion, `.env` y descarga |
| Programaciones | `/programaciones/` | Agenda, zona horaria y calendario |
| Ejecuciones | `/ejecuciones/` | Solicitud manual, historial, consola, notificaciones y detencion |
| Operacion | `/operacion/estado`, `/logs/` | Estado, heartbeat y logs del sistema |
| Configuracion | `/configuracion/` | Scheduler y Mail Graph global |
| Feriados | `/feriados/` | Calendario local y sincronizacion manual |
| Evidencias | integrado en tarea/worker | Validacion AST, captura stdout y metadata |
| Notificaciones | integrado en tarea/worker | Destinatarios, disponibilidad, reserva, despacho y estado Graph |
| Auditoria | `/auditoria/` | Consulta inmutable de acciones humanas |
| Papelera | `/papelera/` | Retiro, restauracion y eliminacion condicionada |
| Factory Reset | `/administracion/factory-reset` | Preview y reset in-place fail-closed |

## Flujo de ejecucion

La Web y el Scheduler no ejecutan scripts. Ambos crean una fila `PENDIENTE`
con tarea, script y version congelados. El Worker realiza el claim atomico,
cambia a `EN_EJECUCION`, invoca el motor subprocess y persiste el estado final,
logs, evidencia y notificacion. Esta separacion evita motores paralelos y
mantiene recuperables las solicitudes que aun no fueron reclamadas.

La disponibilidad efectiva de correo se calcula una sola vez en
`ServicioConfiguracionGraph`. Tareas consume un resumen sin identificadores
sensibles para advertir antes de una ejecucion; Ejecuciones consulta la
trazabilidad segura de `notificaciones_envios`. El polling sincroniza todas las
cards y mantiene separados el estado del script y el del correo.

El dispatcher post-ejecucion evalua tipos independientes. Una ejecucion
`EXITOSA` puede reservar `NOTIFICACION_EXITOSA`, `EVIDENCIA_CLIENTE`, ambos o
ninguno segun su configuracion. Exito usa destinatarios `EXITO` y el template
`correos/exito.html`; Evidencia usa destinatarios `EVIDENCIA`, exige payload
runtime `VALIDADA` y renderiza `correos/evidencia.html`. Un fallo evalua
exclusivamente `ALERTA_INTERNA`, con destinatarios `ALERTA` o globales.

## Persistencia

Los repositorios reciben una conexion de una unidad de trabajo; no abren commits
ocultos. Los valores de usuario viajan como parametros `?` de pyodbc y las
partes dinamicas se limitan a allowlists internas. El contrato canonico es el
bootstrap 19C.1 de 33 tablas, 457 columnas y 38 CHECK documentado en
`docs/PERSISTENCIA_RECONSTRUCCION.md`.

## Seguridad transversal

Las mutaciones requieren permiso backend y CSRF. Las vistas usan autoescape;
los errores publicos se normalizan; rutas y archivos se confinan a roots
configuradas; el motor usa `shell=False`; contrasenas, secretos Graph y
contenido `.env` no se serializan en DTO publicos ni auditoria.

## Runtime historico

`app/`, `run.py` y `scheduler_worker.py` se mantienen para trazabilidad del
proceso de reconstruccion. No se eliminan en v1.0.0, pero no son iniciados por
Docker Compose, no deben recibir nuevas funcionalidades y no prevalecen frente
a `src/app_scheduler/`.
