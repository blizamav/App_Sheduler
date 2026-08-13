# Inventario Maestro de Reconstruccion

## Proposito

Este documento fija la linea base del Hito 0 para reconstruir APP Scheduler sin perder requisitos aprobados ni copiar deuda accidental. La implementacion actual se conserva como referencia hasta completar y validar el reemplazo.

Fecha de corte: 2026-08-13.

## Fuentes revisadas

* `README.md`, `log_codex.md` y los 23 documentos de `docs/`.
* Codigo bajo `app/`, `scheduler_worker.py`, `run.py`, `Dockerfile` y `docker-compose.yml`.
* SQL de `database/release/`, `database/bootstrap/`, `database/factory_reset/`, migraciones vigentes y legado pre-release.
* Pruebas bajo `tests/`.
* Historial Git de Fases 17A, 17A.1, 17B, 17C, 17D, 17X, 18D, 19B, 19C, 19D, 19E.0A, 19E y 19F.

## Linea base verificable

| Area | Estado observado |
| --- | --- |
| Backend | Flask con fabrica de aplicacion, 16 blueprints funcionales y separacion parcial rutas/servicios/repositorios. |
| Superficie HTTP | 84 reglas, incluida ruta estatica. |
| Persistencia | SQL Server mediante `pyodbc`; 33 tablas en el bootstrap limpio. |
| SQL | 25 claves foraneas, 38 `CHECK`, 119 `DEFAULT`; no hay vistas, procedimientos, funciones ni triggers propios. |
| Seguridad funcional | Login hibrido, roles, permisos y `SUPER_ADMIN_ENV`; hash Werkzeug. |
| Permisos base | 52 permisos activos distribuidos en `SUPER_ADMIN`, `ADMIN`, `TI` y `TERCERO`. |
| Runtime | Servicio web Flask y worker separado; ejecuciones todavia usan hilos Python en el proceso que las inicia. |
| Frontend | 25 templates, CSS monolitico de aproximadamente 3.681 lineas y JS monolitico de aproximadamente 2.563 lineas. |
| Pruebas | Dos archivos de prueba, concentrados en Factory Reset; no existe cobertura transversal suficiente. |
| Docker | Servicios `web` y `worker`; ambos cargan explicitamente `.env.docker`. |
| Factory Reset | Arquitectura vigente in-place sobre `APP_SCHEDULER_QA`; blue-green deprecado. |
| Git | El fix previo de sintaxis T-SQL fue separado del cierre documental mediante commit propio; Hito 0 no mezcla ambos trabajos. |

## Inventario funcional y decision

| Dominio | Capacidad vigente | Clasificacion | Decision de reconstruccion |
| --- | --- | --- | --- |
| Autenticacion | Login por `SUPER_ADMIN_ENV` y por usuarios SQL | REIMPLEMENTAR | Mantener comportamiento hibrido, sesiones y mensajes sin filtrar secretos. |
| Usuarios | Alta, edicion, estado, roles y password seguro | REIMPLEMENTAR | Casos de uso transaccionales y permisos backend obligatorios. |
| Roles y permisos | Matriz persistida y decoradores de autorizacion | REFACTORIZAR | Conservar codigos; centralizar politica y probar cada ruta sensible. |
| Clientes | Mantenedor, estado y eliminacion controlada | REIMPLEMENTAR | Compartir patron de catalogos sin mezclar SQL en rutas. |
| Categorias | Mantenedor, estado y eliminacion controlada | REIMPLEMENTAR | Igual criterio de catalogos. |
| Tipos | Mantenedor, estado y eliminacion controlada | REIMPLEMENTAR | Igual criterio de catalogos. |
| Tareas | CRUD operativo, programacion, estado y eliminacion logica | REIMPLEMENTAR | Agregado transaccional con script, version, programacion y notificaciones. |
| Scripts | Contenedor logico, descarga y ciclo de vida | REIMPLEMENTAR | Preservar rutas seguras, hash y trazabilidad. |
| Versiones | Maximo tres slots, una activa y reemplazo trazable | CONSERVAR | Mantener reglas y reforzarlas con servicio y restricciones SQL vigentes. |
| `.env` de script | Archivo por version, limites y descarga protegida | REIMPLEMENTAR | Nunca persistir contenido secreto en BD ni mostrarlo en logs. |
| Scheduler | Configuracion, candidatos, feriados, eventos y heartbeat | REFACTORIZAR | Mantener worker separado y unificar el inicio de ejecuciones. |
| Ejecuciones | Manual, automatica, PID, detencion y estados | REFACTORIZAR | El proceso web no ejecutara scripts en hilos; ambos origenes usaran el mismo motor del worker. |
| Consola y logs | Polling, stdout/stderr, archivos y trazabilidad | REIMPLEMENTAR | Mantener experiencia aprobada con limites, cursores y politica de secretos. |
| Evidencias | Contrato stdout delimitado, parseo JSON y validacion | REIMPLEMENTAR | Validacion estatica sin ejecutar scripts y captura asociada a ejecucion/version. |
| Papelera | Retiro operativo, restauracion y eliminacion permanente | REIMPLEMENTAR | Preservar historial y limpieza fisica sin huerfanos. |
| Auditoria | Eventos de cambios y acciones sensibles | REIMPLEMENTAR | Servicio transversal, esquema estable y sanitizacion obligatoria. |
| Feriados | CRUD local, reglas de Chile y sincronizacion Nager.Date | REIMPLEMENTAR | SQL Server es fuente del scheduler; internet solo en sincronizacion manual. |
| Mail Graph | Configuracion global, destinatarios, evidencia y alertas | REIMPLEMENTAR | Secretos solo en entorno; envios idempotentes y auditables. |
| Paneles operativos | Panel principal, scheduler, ejecuciones y logs | CONSERVAR | Preservar flujos y jerarquia visual, reconstruyendo componentes. |
| Factory Reset | In-place, precheck, lock, transaccion y cuarentena | REIMPLEMENTAR | Mantener diseno final, no reutilizar blue-green. |

## Modelo de datos vigente

### Catalogos

`cat_estados_tarea`, `cat_estados_ejecucion`, `cat_tipos_programacion`, `cat_niveles_log`, `cat_tipos_tarea`, `cat_estados_version_script`.

### Seguridad

`usuarios`, `roles`, `permisos`, `usuarios_roles`, `roles_permisos`.

### Negocio y configuracion

`clientes`, `categorias`, `tipos`, `tareas`, `programaciones`, `scripts`, `scripts_versiones`, `configuracion_sistema`.

### Ejecucion, logs y auditoria

`ejecuciones`, `logs_tareas`, `logs_sistema`, `auditoria_cambios`.

### Scheduler y calendario

`configuracion_scheduler`, `scheduler_worker_heartbeat`, `scheduler_eventos`, `feriados`, `reglas_feriados_irrenunciables`.

### Notificaciones y evidencia

`notificaciones_config_tarea`, `notificaciones_destinatarios`, `evidencias_ejecucion`, `notificaciones_envios`, `configuracion_mail_graph`.

### Decision

El modelo es una fuente funcional util y se conserva como contrato inicial. Antes del Hito 2 se revisaran nulabilidad, cardinalidades, indices y estados; ningun cambio se aplicara directamente a QA sin script, revision y autorizacion.

## Permisos vigentes por dominio

La fuente ejecutable contiene 52 permisos activos. Los grupos son:

* Plataforma: `PANEL_VER`, `LOGS_VER`, `CONFIGURACION_ADMIN`, `FACTORY_RESET_EJECUTAR`.
* Usuarios: `USUARIOS_ADMIN`.
* Mantenedores: `CLIENTES_*`, `CATEGORIAS_*`, `TIPOS_*` para ver, crear, editar y cambiar estado.
* Tareas: `TAREAS_VER`, `TAREAS_CREAR`, `TAREAS_EDITAR`, `TAREAS_ESTADO`, `TAREAS_ACTIVAR`, `TAREAS_SUSPENDER`, `TAREAS_EJECUTAR`, `TAREAS_ELIMINAR`.
* Scripts: permisos para ver, crear, editar, cargar, versionar, reemplazar, activar/desactivar, eliminar, gestionar `.env` y activar version.
* Ejecuciones: ver, ejecutar, detener y consultar log.
* Scheduler: ver y editar configuracion.
* Feriados: ver, crear, editar, estado, eliminar y sincronizar.
* Papelera: ver, restaurar y eliminar permanentemente.
* Auditoria: ver y detalle.

La matriz exacta rol-permiso sera extraida a una prueba automatizada en el Hito 3; no se inferiran autorizaciones por la visibilidad de botones.

## Superficie HTTP actual

| Blueprint | Reglas |
| --- | ---: |
| `principal` | 5 |
| `usuarios` | 5 |
| `mantenedores` | 15 |
| `tareas` y `tareas_api` | 9 |
| `scripts` | 11 |
| `ejecuciones` | 6 |
| `scheduler` | 5 |
| `worker_api` | 5 |
| `feriados` | 8 |
| `papelera` | 4 |
| `auditoria` | 2 |
| `configuracion` y `configuracion_api` | 4 |
| `factory_reset` | 4 |

Las URLs vigentes son contrato de compatibilidad inicial. Su cambio exige tabla de equivalencias o redireccion documentada.

## Configuracion y secretos

Las plantillas `.env.example` y `.env.docker.example` exponen 48 claves equivalentes. Cubren aplicacion, SQL operativo, rutas, limites, Factory Reset y Microsoft Graph.

Decisiones:

* `.env` es solo LOCAL y `.env.docker` es solo Docker QA.
* Los archivos reales estan ignorados por Git; solo las plantillas se versionan.
* Docker debe cargar siempre `.env.docker`.
* `APP_VERSION` se usa en codigo pero no esta en las plantillas: REFACTORIZAR y documentar en Hito 1.
* La configuracion debe validarse por contexto; el web normal no debe exigir credenciales de mantenimiento si Factory Reset esta deshabilitado.
* Nunca se registran connection strings completas, passwords, tokens ni secretos Graph.

## Filesystem e integraciones

| Recurso | Clasificacion | Regla |
| --- | --- | --- |
| `scripts/` | CONSERVAR | Rutas relativas persistidas, raiz configurada y proteccion contra traversal/symlinks. |
| `env_scripts/` | CONSERVAR | Un `.env` por version; contenido fuera de BD. |
| `logs_tareas/` | CONSERVAR | Archivos por ejecucion con acceso autorizado. |
| `logs_sistema/` y `logs/` | REFACTORIZAR | Politica unica de rotacion, retencion y formato. |
| `runtime_control/` | CONSERVAR | Locks y coordinacion entre web, worker y Factory Reset. |
| Nager.Date | CONSERVAR | Integracion manual; el worker nunca depende de internet. |
| Microsoft Graph | CONSERVAR | Cliente desacoplado, timeout, sanitizacion e idempotencia. |
| SQLCMD | CONSERVAR | Herramienta exclusiva del Factory Reset in-place. |

## Deuda y contradicciones detectadas

| Hallazgo | Severidad | Resolucion |
| --- | --- | --- |
| `README.md` termina en fases anteriores y referencia rutas SQL que ya son legado. | Alta | Reescribir en Hito 15; hasta entonces este inventario manda. |
| `log_codex.md` y `ROADMAP.md` describen Factory Reset blue-green aunque fue reemplazado por in-place. | Alta | Normalizar estado maestro en Hito 0. |
| `VARIABLES_ENTORNO.md` y `OPERACION_WORKER.md` describen fallback Docker a `.env`; Compose ya fija `.env.docker`. | Alta | Corregir en Hito 1 sin tocar secretos. |
| `ARQUITECTURA.md` y `BASE_DATOS.md` conservan lenguaje de fases tempranas y pendientes ya implementados. | Media | Sustituir por documentacion objetivo y fichas de modulo por hito. |
| Ejecuciones manuales y automaticas crean hilos en procesos distintos. | Alta | Motor unico propiedad del worker en Hitos 6-7. |
| CSRF aparece de forma especifica en Factory Reset, no como proteccion transversal de escrituras. | Critica | Implementar politica global en Hito 1 y probarla en cada modulo. |
| CSS y JS son monoliticos. | Media | Dividir por componentes/modulos sin cambiar identidad en Hito 12. |
| Dos archivos de pruebas cubren casi solo Factory Reset. | Critica | Crear piramide transversal desde Hito 1. |
| Flask de desarrollo se usa en contenedor. | Alta para produccion | Mantener QA controlado y definir WSGI/hardening solo en checklist productivo. |
| `database/release/` convive con bootstrap, migraciones QA y legado. | Media | Mantener release protegido y documentar claramente cada canal SQL. |
| Documentacion de evidencia/Graph aun conserva secciones llamadas futuras. | Media | Actualizar junto con Hitos 8 y 10. |

## Componentes obsoletos

| Elemento | Clasificacion | Tratamiento |
| --- | --- | --- |
| Factory Reset blue-green, `NEW`, `OLD`, `FAILED` | DEPRECAR | Solo historia en Git/Changelog; no copiar. |
| Crear, eliminar o renombrar bases como parte del reset | DESCARTAR | Incompatible con cuenta de mantenimiento `db_owner` local. |
| `database/legacy_pre_release_13B/` como fuente ejecutable | DEPRECAR | Referencia historica de solo lectura. |
| Migracion QA 021 dentro de instalacion limpia/reset | DESCARTAR | Correctivo historico, no parte del modelo limpio. |
| Ejecucion de scripts desde hilos del proceso web | DESCARTAR | Sustituir por solicitudes persistentes consumidas por worker. |
| Fallback Docker a `.env` | DESCARTAR | Riesgo de mezclar LOCAL y QA. |
| Fases diagnosticas como arquitectura oficial | DESCARTAR | Se conservan solo en historia Git/Changelog. |

## Riesgos abiertos antes de implementar

1. Definir el contrato persistente para encolar ejecuciones sin perder compatibilidad con `ejecuciones`.
2. Decidir migracion/cutover del paquete Flask sin ejecutar simultaneamente dos motores.
3. Obtener una linea base de QA y respaldo antes de cambios SQL o Factory Reset real.
4. Validar la matriz completa de 52 permisos contra todas las rutas mutables.
5. Formalizar retencion de logs, auditoria, evidencias y notificaciones.
6. Resolver el lock de ERROR de Factory Reset actual solo mediante procedimiento autorizado; el Hito 0 no lo toca.

## Criterio de cierre del Hito 0

Hito 0 queda cerrado con este inventario y `ARQUITECTURA_RECONSTRUCCION.md` revisados, el roadmap normalizado y el README alineado. Hito 1 permanece pendiente y requiere autorizacion explicita; el cierre no habilita SQL destructivo, Factory Reset real ni cambios en `database/release/`.
