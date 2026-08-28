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

### Hito 4 - Clientes, categorias y tipos

Estado: CERRADO.

Clientes, categorias y tipos disponen de listados paginados, filtros, alta, edicion, estado, permisos backend, CSRF y auditoria canonica en el runtime aislado. El contrato SQL, los permisos bootstrap, las transacciones, la UI responsive y las pruebas quedaron reconciliados. No se implemento Papelera global ni eliminacion permanente.

### Hito 5 - Tareas, scripts, versiones y `.env`

Estado: CERRADO.

Se reconstruyeron tareas manuales, listado y filtros, scripts logicos 1:1, tres slots de version, unica version activa, reemplazo explicito solo sin referencias, carga `.py` validada y `.env` por version. SQL, auditoria y filesystem se coordinan con UoW y compensacion. No se persiste usuario ejecutor en `tareas`: la automatica usa `usuario_ejecucion = NULL` y la manual registra al usuario APP Scheduler en `ejecuciones`, segun el contrato cerrado en Hito 7.

### Hito 6 - Programaciones, scheduler y worker

Estado: CERRADO.

Programaciones, calculo temporal IANA/DST, calendario local, reserva automatica idempotente, heartbeat y loop controlado fueron reconstruidos bajo `src/app_scheduler/`. El scheduler persiste una ejecucion `PENDIENTE` con la version activa congelada y Hito 7 ahora consume esa fila sin duplicarla. El runtime historico sigue activo.

### Hito 7 - Motor unico de ejecucion, logs y evidencias

Estado: CERRADO.

Manual y automatica comparten reserva `PENDIENTE`, claim atomico y un unico
motor worker. Quedaron implementados subprocess seguro, entorno aislado,
stdout/stderr incremental, PID, timeout global, detencion persistida, logs,
captura de evidencia, historial, consola, permisos, CSRF y auditoria. No existe
cutover y el runtime historico permanece intacto.

Gate transversal de cierre: login invalido y errores publicos ya no pueden
renderizar una pagina vacia; Panel, sidebar, acciones y estados vacios fueron
reconciliados con la organizacion util del runtime historico sin copiar su deuda.
El gate incorporo Bootstrap 5.3.3 local, navegacion responsive, hub global
`/scripts`, correcciones visuales desktop/movil y disciplina OWASP aplicable sin
declarar cumplimiento formal. La validacion de cierre aprueba 205 pruebas
reconstruidas y 231 totales; una prueba de symlink queda omitida en Windows y
esta cubierta en Linux. Al cerrar ese hito, Hito 8 aun no habia sido iniciado.

### Hito 8 - Observabilidad, configuracion operativa e integracion tecnica QA

Estado: CERRADO.

Reimplementar `logs_sistema` global, observabilidad, panel/configuracion de
Scheduler y Worker, configuracion pendiente de evidencias y configuracion de
sistema relacionada. Incluir integracion tecnica temprana contra
`APP_SCHEDULER_QA` para web, worker, filesystem, logs y evidencia. No duplicar
stdout/stderr, consola ni captura base ya cerrados en Hito 7.

Implementacion actual: navegador paginado de `logs_sistema`, detalle seguro,
estado real de worker/scheduler, matriz de `configuracion_sistema` solo lectura,
edicion tipada de `configuracion_scheduler` y configuracion de evidencia por
tarea con validacion AST. El smoke real read-only contra `APP_SCHEDULER_QA`
confirmo contrato y lecturas, login invalido controlado y cero residuos. El
login SQL valido no se ejecuto al no existir una credencial de aplicacion
autorizada para la prueba; `SUPER_ADMIN_ENV` si fue validado.

### Hito 9 - Auditoria UI y Papelera

Estado: CERRADO.

Implementados en el runtime aislado la consulta, filtros y detalle inmutables
de auditoria, retiro operacional, restauracion inactiva, eliminacion permanente
condicionada, preservacion mediante snapshots y cleanup filesystem compensable.
Las entidades admitidas son las siete tablas que poseen
`eliminado_operativo`; ejecuciones, logs, evidencias y auditoria son historia
protegida y no ingresan a Papelera. El gate tecnico, Docker y visual responsive
esta aprobado. No hubo SQL ni mutaciones QA.

### Hito 10 - Feriados, notificaciones, Microsoft Graph y email

Estado: CERRADO.

Se reconstruyeron el mantenedor de feriados, sincronizacion manual y con preview
desde Nager.Date, prioridad de registros manuales, configuracion Graph global,
destinatarios TO/CC/BCC por tarea y despacho posterior a ejecucion para evidencia
o alerta interna. El scheduler conserva SQL Server como unica fuente de
calendario. El contenido completo de evidencia vive solo en memoria y la BD
mantiene metadata y trazabilidad. Graph usa client credentials, endpoints fijos,
timeouts, autoescape, adjuntos confinados y reserva at-most-once; no existe retry
automatico ni envio real dentro de la validacion. No hubo SQL, cambios de esquema,
cutover ni modificaciones al runtime historico.

El cierre aprobo 280 pruebas de reconstruccion y 306 totales, con un skip de
symlink cubierto en Linux, gates tecnicos/Docker y revision responsive. Un GET
no destructivo a Nager.Date valido conectividad y parser sin persistencia; Graph
real queda pendiente de configuracion autorizada para el Hito 14.

## Pendiente

### Ajuste contractual post-Hito 10 - Notificacion de exito independiente

Estado: LISTO PARA REVISION; migracion QA pendiente de autorizacion.

Se preparo `notificar_exito_activa`, el tipo canonico
`NOTIFICACION_EXITOSA`, el backfill de configuraciones con Evidencia y el CHECK
que impide Evidencia sin exito. El despacho puede enviar exito o error a scripts
sin Evidencia y agrega Evidencia solo cuando el bloque runtime es valido. La UI
separa Exito, Error y Evidencia e incorpora el flujo Datos -> Script ->
Evidencia -> Notificaciones -> Programacion. Hito 10 permanece cerrado y Hito
11 no fue iniciado.

### Hito 11 - Factory Reset in-place

Estado: CERRADO A NIVEL IMPLEMENTACION.

El runtime reconstruido incorpora Factory Reset in-place con permiso dedicado,
CSRF global, preview firmado, doble confirmacion, prechecks antes y despues del
lock, SQLCMD con cuenta separada, `sp_getapplock`, transaccion, cuarentena
filesystem compensable, progreso seguro y fail-closed. No crea, elimina o
renombra bases y no importa componentes del runtime historico.

Pendiente deliberado: smoke destructivo real sobre `APP_SCHEDULER_QA` en Hito
14, con respaldo y autorizacion explicita.

### Hito 12 - UI/UX y responsive final

Estado: CERRADO.

Se completo el inventario visual del runtime reconstruido, la validacion real
de vistas generales y flujos de detalle en 1440x900, 768x900, 390x844 y
844x390, y el cierre transversal de responsive, foco, navegacion, formularios,
tablas, estados y movimiento reducido. Evidencia no implementada se presenta
como capacidad opcional y la consola de ejecucion conserva jerarquia y ancho
correctos incluso con nombres de Worker extensos.

### Hito 13 - Docker QA

Estado: CERRADO.

Compose inicia exclusivamente `app_scheduler.web` y
`app_scheduler.worker.aplicacion`, carga `.env.docker` sin fallback, conserva
volumenes operativos, separa las credenciales de mantenimiento del Worker y
declara restart/healthchecks para Web y heartbeat. Build, checks y startup Web
QA fueron validados sin iniciar Scheduler ni consumir ejecuciones.

### Hito 14 - QA integral

Estado: CERRADO.

La QA integral aprobo Factory Reset in-place real, contrato SQL post-reset,
Docker QA, fixture funcional, ejecuciones manuales, recuperacion de cola,
ejecucion automatica at-most-once, Scheduler/Worker, Papelera, seguridad,
responsive y regresion completa. El primer reset fallo antes del commit por
opciones de sesion SQLCMD incompletas y demostro rollback SQL/filesystem; el
segundo y ultimo intento autorizado aprobo tras declarar todas las opciones SET
requeridas por indices filtrados.

El gate final Graph proceso exclusivamente la ejecucion `4`, genero una sola
`NOTIFICACION_EXITOSA` con el template canonico, sin evidencia, adjuntos, CC ni
BCC, y Microsoft Graph la acepto con HTTP 202. La reserva at-most-once impidio
un segundo despacho. Graph quedo deshabilitado nuevamente mediante la
configuracion SQL de la aplicacion, sin modificar archivos de entorno. Hito 15
permanece pendiente y no fue iniciado.

### Hito 15 - Documentacion, cutover y cierre

Completar documentacion y runbooks, ejecutar cutover controlado, retirar el
runtime historico, validar post-cutover y cerrar el proyecto con pendientes
productivos reales registrados.

## Reglas permanentes

* Una sola base: `APP_SCHEDULER_QA`.
* `.env` para LOCAL y `.env.docker` para Docker QA.
* `database/release/` es protegido y de solo lectura.
* No ejecutar SQL destructivo ni Factory Reset sin autorizacion explicita.
* No cerrar hitos con residuos no justificados.
* No marcar QA como validado solo por compilar o pasar mocks.
* Staging Git explicito; no usar `git add -A`.
* Cada cierre exige un gate transversal tecnico, funcional, visual y comparativo
  con el historico cuando corresponda. Una regresion UX objetiva bloquea el hito.
