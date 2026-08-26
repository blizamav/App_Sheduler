# Arquitectura de Reconstruccion

## Estado

Arquitectura maestra aprobada al cerrar Hito 0. Los Hitos 1-13 estan cerrados
como Release Candidate; el runtime reconstruido es el default Docker QA y el
runtime historico queda solo como referencia hasta el cutover de Hito 15.

## Implementacion Hito 10

El calendario conserva SQL Server como unica fuente usada por el scheduler.
Nager.Date se encapsula en un cliente con endpoint fijo, timeout y TLS normal, y
solo se invoca desde una sincronizacion manual autorizada con preview.

```text
UI feriados -> caso de uso -> Nager.Date manual -> reconciliacion -> SQL + auditoria
motor -> cierre SQL ejecucion -> evidencia efimera -> reserva envio -> Graph -> cierre envio
```

La configuracion Graph combina metadata no secreta de
`configuracion_mail_graph` con kill switch y secret provenientes del entorno.
El worker confirma primero ejecucion/evidencia, reserva el tipo de correo de
forma at-most-once y realiza HTTP fuera de la transaccion. Un fallo Graph se
registra en `notificaciones_envios` y `logs_sistema`, pero nunca reescribe el
resultado de la ejecucion. Los adjuntos se resuelven solo bajo el root de la
version y bloquean symlinks, traversal, `.env`, codigo y tamanos no admitidos.
No hay retry automatico ni envio real en las pruebas de Hito 10.

## Implementacion Hito 9

Auditoria conserva una superficie estrictamente read-only sobre el repositorio
canonico/legacy existente. Papelera agrega un caso de uso central, entidad
allowlist y una UoW comun para estado, auditoria y preservacion historica.

```text
GET Auditoria -> servicio de consulta -> repositorio paginado -> SQL canonico/legacy
POST Papelera -> permiso + CSRF -> lock de fila -> dependencias -> estado/auditoria -> commit
POST Purga -> validar ausencia de historia -> cuarentena FS -> DELETE operativo -> commit -> cleanup
```

La purga se bloquea si tarea, script o version conserva ejecuciones, por lo que
`ejecuciones.id_script` e `id_version` no se nulifican ni reinterpretan. Tampoco
elimina ejecuciones, logs, evidencias, eventos ni auditoria. El
filesystem usa el almacen confinado de Hito 5 y compensacion por rename. No se
agregan DDL, repositorios paralelos ni transacciones ocultas. El contrato
completo esta en `docs/AUDITORIA_PAPELERA_RECONSTRUCCION.md`.

## Implementacion Hito 8

La observabilidad global se separa de la consola de ejecucion:

```text
logs_sistema -> RepositorioLogsSistema -> /logs/ + detalle seguro
configuracion_scheduler + heartbeat + ejecuciones -> /operacion/estado
configuracion_sistema -> matriz solo lectura y valores sensibles protegidos
notificaciones_config_tarea + script activo -> validacion AST -> configuracion por tarea
```

Las consultas de logs son parametrizadas, paginadas y con orden fijo en
allowlist. La configuracion scheduler acepta solo cinco campos tipados y audita
antes/despues en la misma UoW. La evidencia se valida con AST y lectura confinada
del `.py`; nunca se importa, ejecuta ni evalua el script. No se agregaron tablas,
jobs destructivos, Graph, Factory Reset reconstruido ni entrypoints. Papelera
se incorpora posteriormente en Hito 9 sin cambiar este alcance.

## Implementacion Hito 7

Flask solo autoriza y reserva. El worker reclama bajo lock transaccional y ejecuta
manuales y automaticas mediante `MotorEjecucionSubprocess`. El proceso recibe
una allowlist de entorno OS mas el `.env` de la version, usa cwd determinista,
`shell=False`, pipes separados y grupo de procesos propio. Logs y evidencia se
producen desde el mismo flujo; la automatica nunca vuelve a resolver la version.

```text
WEB manual ----> PENDIENTE --+
                              +-> claim atomico -> motor -> estado/log/evidencia
SCHEDULER auto -> PENDIENTE --+
```

El worker revisa la cola entre ciclos del scheduler y limita claims con la
configuracion SQL. Factory Reset y mantenimiento bloquean trabajo nuevo. No se
promete exactly-once: despues del claim se aplica at-most-once y una ejecucion
incierta no se relanza sin lease persistente. Detalle en
`docs/MOTOR_EJECUCION_RECONSTRUCCION.md`.

El entrypoint oficial admite dos composiciones sobre el mismo
`ServicioWorker` y el mismo `ProcesadorColaEjecuciones`:

* modo predeterminado: construye `ServicioScheduler`, evalua programaciones y
  despues consume la cola;
* `--queue-only`: no construye `ServicioScheduler` y solo consume filas ya
  `PENDIENTE` mediante el claim y motor existentes.

`--once` limita cualquiera de las composiciones a un ciclo y espera el cierre
de los trabajos reclamados. El modo de cola conserva heartbeat, limite de
concurrencia SQL, mantenimiento, bloqueo fail-closed de Factory Reset, logs,
evidencia y notificaciones. No inserta reservas automaticas ni llama a
`ServicioScheduler.ejecutar_ciclo`.

## Implementacion Hito 6

El proceso web administra programaciones y el proceso worker es el unico dueño del loop scheduler. El flujo reconstruido es:

```text
WEB -> caso de uso Programaciones -> SQL + auditoria
WORKER -> scheduler -> SolicitudEjecucion -> reserva dbo.ejecuciones PENDIENTE
Hito 7 -> reclamo atomico -> motor unico manual/automatico
```

La version automatica se resuelve desde `scripts.id_version_activa` al disparar y su `id_version` queda congelado en `ejecuciones`. La automatica no inventa usuario aplicativo: `usuario_ejecucion = NULL`; `nombre_worker` y la clave de programacion identifican al solicitante tecnico. Hito 7 consume esa fila exacta mediante subprocess sin cambiar la decision del scheduler.

El calculo temporal usa `programaciones.zona_horaria` IANA y entrega `datetime2` local sin offset, compatible con el esquema. Una hora inexistente por DST se omite; una hora ambigua se reserva una sola vez usando el primer `fold`. Cada fecha se calcula desde la regla civil, sin deriva diaria. La politica historica de reinicio salta ocurrencias anteriores a la ventana de polling y avanza al siguiente disparo. El indice unico filtrado de `clave_programacion` resuelve carreras entre workers; el chequeo previo no es la garantia de idempotencia.

## Implementacion Hito 1

Mapa de transicion aplicado:

| Actual | Runtime reconstruido | Estado |
| --- | --- | --- |
| `app/__init__.py` | `src/app_scheduler/aplicacion.py` | Fabrica reimplementada y aislada. |
| `app/config.py` | `src/app_scheduler/configuracion.py` | Tipado, validacion por capacidad y secretos fuera de mensajes. |
| `app/database/conexion.py` | `compartido/base_datos.py` | Proveedor inyectable, conexiones cortas y errores controlados. |
| Commit/rollback disperso | `compartido/unidad_trabajo.py` | Transaccion explicita y cierre garantizado. |
| CSRF especifico Factory Reset | `compartido/csrf.py` | Politica global para `POST`, `PUT`, `PATCH` y `DELETE`. |
| Manejo local de errores | `compartido/errores.py` | Jerarquia y respuestas HTML/JSON seguras. |
| Logging por servicios | `compartido/logging.py` | Formato comun y sanitizacion base. |
| CSS/JS monoliticos | `presentacion/static/` | Base dividida por tokens, layout, componentes y modulos. |
| Hilos web para ejecucion | `worker/contratos.py` y motor Hito 7 | Flask reserva; el worker reclama y ejecuta con el motor unico. |

Hito 1 no copio rutas funcionales ni modulos de negocio. Los Hitos 3-13
reimplementaron incrementalmente seguridad, catalogos, tareas/scripts,
scheduler, motor, logs, consola, evidencia, observabilidad, Papelera, feriados y
Graph, ademas de Factory Reset in-place, UI final y Docker QA. Los archivos
`run.py` y `scheduler_worker.py` permanecen como referencia historica, pero
Compose y Dockerfile ya no los usan.

## Implementacion Hito 2

La infraestructura Hito 1 se extiende, no se reemplaza:

| Capa | Implementacion | Limite |
| --- | --- | --- |
| Contrato SQL | Inventario de 33 tablas y tests contra DDL bootstrap | Sin cambiar esquema ni consultar QA |
| Modelos | DTO inmutables y paginacion | Sin ORM ni entidades activas complejas |
| Mapeo | Columnas explicitas a atributos Python | Sin mapper generico magico |
| Repositorios | Usuarios, seguridad y catalogos | Sin CRUD web ni repositorios vacios por tabla |
| Transaccion | `UnidadTrabajoSQL` compartida por repositorios | Commit solo desde caso de uso |
| Errores | Traduccion DB-API con operacion/clase/SQLSTATE | Sin SQL, parametros o secretos en mensajes |

El mapa completo, relaciones, convenciones y deuda quedan en `docs/PERSISTENCIA_RECONSTRUCCION.md`.

## Principios

1. Conservar contratos funcionales aprobados y reconstruir su implementacion.
2. Una unica base del aplicativo: `APP_SCHEDULER_QA`.
3. Flask atiende HTTP; el worker posee scheduler y ejecucion de procesos.
4. Ejecucion manual y automatica comparten un unico motor.
5. SQL parametrizado y transacciones delimitadas por caso de uso.
6. Autorizacion, CSRF, auditoria y sanitizacion son transversales.
7. Filesystem se trata como recurso transaccional compensable.
8. `database/release/` permanece publicado, protegido y de solo lectura.
9. Factory Reset es exclusivamente in-place.
10. Cada hito entrega codigo, pruebas y documentacion coherentes.

## Estrategia de reemplazo

No se borrara `app/` al comenzar. Se construira el nuevo runtime en un paquete independiente y se migraran modulos por cortes verticales verificables. Solo un runtime se registrara en cada entrypoint; no se permitira que implementacion antigua y nueva escriban simultaneamente el mismo dominio.

Estructura objetivo:

```text
src/
  app_scheduler/
    aplicacion.py
    configuracion.py
    extensiones.py
    compartido/
      autorizacion.py
      csrf.py
      errores.py
      base_datos.py
      unidad_trabajo.py
      auditoria.py
      filesystem.py
      sanitizacion.py
    modulos/
      autenticacion/
      usuarios/
      mantenedores/
      tareas/
      scripts/
      programador/
      ejecuciones/
      observabilidad/
      auditoria/
      papelera/
      calendario/
      notificaciones/
      factory_reset/
    worker/
      aplicacion.py
      programador.py
      ejecutor.py
      heartbeat.py
    presentacion/
      templates/
      static/
tests/
  unitarios/
  integracion/
  sql/
  filesystem/
  seguridad/
  worker/
  factory_reset/
```

Cada modulo puede contener `rutas.py`, `casos_uso.py`, `repositorio.py`, `modelos.py` y `validadores.py` cuando los necesite. No se crean capas vacias ni abstracciones sin comportamiento.

## Dependencias permitidas

```text
presentacion/rutas
        |
        v
casos de uso/servicios
        |
        +--> repositorios --> base_datos
        +--> filesystem
        +--> integraciones externas
        +--> auditoria
```

Reglas:

* Las rutas traducen HTTP y no contienen SQL ni reglas de negocio extensas.
* Los casos de uso controlan autorizacion de dominio, transaccion y resultado.
* Los repositorios encapsulan SQL Server y devuelven estructuras tipadas simples.
* Templates no deciden permisos de forma autoritativa.
* Un modulo no importa rutas o templates de otro modulo.
* Dependencias externas se inyectan mediante fabricas explicitas, sin contenedor complejo.

## Configuracion

`configuracion.py` construira una configuracion validada e inmutable al iniciar cada proceso.

Perfiles:

* LOCAL: variables del proceso y `.env`.
* QA Docker: variables inyectadas por Compose desde `.env.docker`.
* Produccion: proveedor de secretos/variables del runtime; se define en hito posterior.

La validacion sera por capacidad. SQL operativo es obligatorio para web/worker; Graph solo cuando esta habilitado; credenciales de mantenimiento solo para Factory Reset habilitado. Los errores nombran variables faltantes, nunca valores.

## Acceso a SQL Server

Se mantiene `pyodbc` por compatibilidad y bajo costo de cambio.

La capa compartida proveera:

* fabrica de conexiones con timeout y nombre de aplicacion;
* context managers para cursor y conexion;
* parametros para todos los datos de usuario;
* traduccion controlada de errores tecnicos;
* unidad de trabajo para operaciones multi-repositorio;
* transacciones cortas, sin conexiones globales ni entre requests.

No se adopta ORM en esta etapa: el modelo y SQL Server ya estan consolidados, y un ORM agregaria migracion de riesgo sin beneficio proporcional.

## Modelo y evolucion SQL

Las 33 tablas del bootstrap son la linea base. El Hito 2 generara un diccionario versionado y pruebas de:

* PK, FK, `UNIQUE`, `CHECK`, `DEFAULT` e indices filtrados;
* estados validos;
* una version activa y maximo tres slots por script;
* trazabilidad `ejecucion -> script -> version`;
* unicidad de configuraciones globales;
* integridad de papelera, auditoria, evidencia y notificaciones.

Canales SQL:

* `database/release/`: publicacion historica protegida; no se modifica.
* `database/bootstrap/`: instalacion limpia actual y validacion.
* `database/factory_reset/`: runner in-place propio.
* nuevas evoluciones: directorio versionado de la reconstruccion, creado solo al aprobar Hito 2.
* `legacy_pre_release_13B/` y correctivos QA: referencia historica, no fuente limpia.

## Autenticacion y autorizacion

Se conserva login hibrido:

1. `SUPER_ADMIN_ENV` permite recuperacion administrativa y no se persiste como usuario normal.
2. Usuarios SQL activos autentican con hash seguro.
3. La sesion guarda identidad minima y se revalida para acciones sensibles.
4. Cada ruta/caso de uso exige permisos backend.
5. La UI solo refleja permisos ya concedidos; ocultar un control no autoriza.

Implementacion Hito 3:

* `modulos/autenticacion/` coordina login/logout y no contiene SQL directo.
* `modulos/usuarios/` concentra validacion, hashing, jerarquia y UoW para usuario + rol + auditoria.
* `compartido/autorizacion.py` conserva una sola identidad inmutable y una sola familia de decoradores.
* La cookie guarda solo tipo, `id_usuario` y login; roles/permisos de usuarios SQL se recargan en cada request protegido.
* `SUPER_ADMIN_ENV` se reconstruye desde configuracion y puede autenticar aunque falle la auditoria SQL; los modulos que requieren datos continuan dependiendo de SQL Server.
* `RepositorioAuditoria` escribe exclusivamente las columnas canonicas de `auditoria_cambios`.

Implementacion Hito 4:

* `modulos/catalogos/` concentra especificaciones cerradas y casos de uso para clientes, categorias y tipos; no acepta tablas o columnas desde HTTP.
* Los repositorios fundacionales se extienden con paginacion, filtros y escrituras parametrizadas, siempre sin commit interno.
* Cada alta, edicion o cambio de estado comparte UoW con `RepositorioAuditoria`; un fallo de cualquier parte revierte la operacion completa.
* Las doce rutas conservan permisos por modulo/accion y reciben CSRF desde la proteccion transversal.
* `eliminado_operativo` se respeta como frontera con la futura Papelera, que no se implementa en este hito.

Hardening del Hito 1:

* CSRF global en toda operacion mutable, incluidas APIs de sesion;
* cookies `HttpOnly`, `SameSite` y `Secure` segun ambiente;
* regeneracion/limpieza de sesion en login/logout;
* limites de upload y validacion de extension/contenido;
* mensajes sin enumeracion de usuarios ni secretos.

## Tareas, scripts y filesystem

La tarea es el agregado principal. Crear o editar una tarea puede coordinar programacion, script inicial, version, `.env` y notificaciones dentro de una unidad de trabajo.

Como SQL Server y filesystem no comparten transaccion distribuida:

1. validar y escribir a ubicacion temporal segura;
2. iniciar transaccion SQL;
3. mover/promover archivos con nombres determinados;
4. confirmar SQL;
5. compensar filesystem si SQL falla;

Hito 5 implementa este limite en `modulos/tareas`, `modulos/scripts`,
`persistencia/repositorio_tareas.py`, `persistencia/repositorio_scripts.py` y
`compartido/filesystem.py`. Los archivos se preparan en el mismo volumen,
se promueven atomicamente dentro de la UoW y se restauran si SQL o auditoria
fallan antes del commit. Los roots y nombres se derivan de configuracion y
metadata validada; el request nunca entrega una ruta fisica.

En Hito 5 toda tarea nueva era `MANUAL`; Hito 6 agrego programaciones y reserva
automatica. `dbo.tareas` y `dbo.programaciones` no contienen ejecutor. Hito 7
congelo el contrato: la automatica reserva `usuario_ejecucion = NULL` y conserva
`nombre_worker` como actor tecnico; la manual registra en `ejecuciones` al
usuario autenticado de APP Scheduler.
6. auditar resultado y limpiar temporales.

Todas las rutas se resuelven contra raices configuradas y se rechazan traversal, symlinks inseguros, raices contenidas y nombres fuera de contrato.

## Scheduler, cola y worker

El worker reconstruido es propietario del loop scheduler y del motor unico:

* programador: implementado; evalua calendarios y reserva solicitudes automaticas `PENDIENTE`;
* ejecutor: implementado; reclama solicitudes manuales o automaticas y lanza el proceso confinado.

La web manual solo solicita ejecucion; no crea `threading.Thread` ni procesos Python. `SolicitudEjecucion` contiene origen, tarea, script, version, actor y fecha. La automatica persiste una fila en `ejecuciones`; la manual reserva otra bajo el mismo contrato, y el worker aplica claim atomico, PID, salida y cierre.

El contrato reutiliza `ejecuciones`: el scheduler crea una unica fila `PENDIENTE` con version congelada y Hito 7 reclama esa misma fila. Una `PENDIENTE` es recuperable; una `EN_EJECUCION` perdida queda incierta y no se relanza sin una futura lease SQL.

Reglas comunes:

* una sola validacion central para manual y automatica;
* version activa para automatica y seleccion confirmada para manual;
* no duplicar tarea en ejecucion;
* respetar mantenimiento, feriados y configuracion;
* heartbeat y shutdown controlado;
* reconciliacion de ejecuciones abandonadas.

## Logs, consola y evidencias

Se separan cuatro flujos:

* salida completa de ejecucion para operadores autorizados;
* logs tecnicos del sistema;
* eventos de decision del scheduler;
* auditoria de acciones de usuario/sistema.

La consola usara polling incremental por cursor o numero de linea, con intervalo moderado y estado terminal. Los secretos reales se sanitizan; la evidencia destinada a terceros se trata de forma separada.

La evidencia mantiene el contrato stdout entre delimitadores. La validacion estatica usa AST/tokenizacion sin importar ni ejecutar el script. En runtime, el bloque JSON se valida, se resume en BD y se asocia a la ejecucion y version exactas.

## Papelera y auditoria

Papelera separa retiro operativo de eliminacion permanente. La eliminacion permanente:

* exige permiso, confirmacion fuerte y auditoria;
* conserva historial requerido;
* elimina solo archivos y estructuras autorizadas;
* ejecuta dry-run de recursos;
* termina con cero scripts, `.env` o directorios huerfanos.

Auditoria es append-only desde la aplicacion. Registra actor, accion, entidad, identificador, resultado y contexto sanitizado. No almacena passwords, tokens, secretos Graph ni contenido `.env`.

## Calendario y Microsoft Graph

SQL Server es la unica fuente de feriados consumida por el scheduler. Nager.Date se consulta solo desde una accion manual autorizada, con preview, timeout y prioridad de datos manuales.

Graph se encapsula tras un cliente propio. El servicio decide destinatarios,
idempotencia at-most-once y estado del envio. Hito 10 no hace reintentos
automaticos. El client secret proviene exclusivamente del entorno y nunca
vuelve a HTML, logs o auditoria.

## Factory Reset in-place

Se conserva el diseno final:

```text
precheck -> lock runtime -> pausa worker -> cuarentena filesystem
-> una sesion SQLCMD -> sp_getapplock -> XACT_ABORT + transaccion
-> limpieza explicita -> bootstrap 002..011 -> validacion 100
-> commit -> filesystem base -> auditoria -> liberar lock
```

Restricciones:

* target exacto `APP_SCHEDULER_QA` y allowlist fail-closed;
* cuenta `user_scheduler_mantenimiento` con `db_owner` solo en esa base;
* sin crear, eliminar o renombrar bases;
* `database/release/001_crear_base_datos.sql` nunca participa;
* una sola sesion SQLCMD para conservar transaccion y applock;
* sintaxis SQL propia validada con parseo real no destructivo;
* error previo a commit revierte SQL y filesystem;
* error no confirmable conserva lock y recursos de recuperacion documentados.

## Presentacion y frontend

Se conserva la identidad visual actual, no sus archivos monoliticos. La capa objetivo separa:

* tokens y base;
* layout/sidebar/topbar;
* componentes de formulario, tabla, modal, badges y alertas;
* estilos por modulo;
* JS base y controladores por pantalla.

No se incorporara framework SPA. Jinja y JavaScript modular cubren la interaccion vigente con menor costo. Se validaran desktop, notebook, tablet y movil; tablas tendran contenedor responsive y acciones accesibles.

Desde el gate transversal de Hito 7, Bootstrap 5.3.3 versionado localmente es la
base estructural. `base.html` concentra shell, Offcanvas, topbar, dropdown,
flashes y modal; cada modulo carga solo su hoja/controlador adicional. No existe
dependencia de CDN, SPA, jQuery ni JavaScript inline. Las mutaciones conservan
autorizacion backend y CSRF; loading y confirmacion no cambian contratos HTTP.
La revision visual manual y sus correcciones responsive forman parte del cierre
del Hito 7; el pulido global fue completado y validado en Hito 12.

### Gate transversal de calidad

Cada hito debe superar cuatro dimensiones antes de cerrarse:

1. tecnica: compilacion, pruebas, templates, JavaScript y packaging;
2. funcional: flujos, permisos, errores y estados vacios;
3. visual: jerarquia, legibilidad, responsive y controles accesibles;
4. comparativa: contraste con la superficie historica equivalente cuando exista.

Los tests verdes no compensan una pantalla rota. Una regresion UX objetiva o un
error que deje una superficie vacia bloquea el cierre. El runtime historico se
usa solo como referencia de organizacion y no como fuente para copiar deuda.

## Docker y operacion

Desde Hito 13, Compose mantiene dos servicios reconstruidos:

* `web`: aplicacion Flask/WSGI segun ambiente;
* `worker`: scheduler y motor de ejecucion.

Ambos usan la misma imagen y `.env.docker`, con volumenes compartidos solo donde
el contrato lo exige. Web arranca con `python -m app_scheduler.web`; Worker con
`python -m app_scheduler.worker.aplicacion` en modo Scheduler+cola. La imagen
no usa los entrypoints historicos. Web expone `/salud` y Worker comprueba el
heartbeat activo de su propio hostname; la cuenta de mantenimiento Factory
Reset se vacia expresamente en el servicio Worker. Produccion requerira WSGI,
secretos externos, backup y retencion como cierre posterior.

## Estrategia de pruebas

Cada hito agregara:

* unitarias para reglas puras;
* integracion para repositorios SQL;
* contratos de permisos por ruta;
* filesystem con temporales y casos traversal/symlink;
* worker y scheduler con reloj/control de concurrencia;
* SQL de bootstrap y Factory Reset con parseo real no destructivo;
* smoke HTTP para flujos criticos;
* QA real antes de marcar un modulo cerrado.

Los mocks no reemplazan validacion SQL, ODBC, Docker o filesystem cuando esos componentes son parte del riesgo.

## Observabilidad y housekeeping

Cada recurso temporal tendra propietario, ubicacion, criterio de retiro y limpieza en exito/fallo. Se mediran ejecuciones atascadas, heartbeat, errores scheduler, notificaciones fallidas, espacio de logs y locks. Un hito no cierra con residuos no justificados.

### Estado de vida transversal del Worker

La fuente de verdad sigue siendo `dbo.scheduler_worker_heartbeat`; no existe un
heartbeat frontend ni paralelo. `ServicioObservabilidad` combina esa senal con
el intervalo de `configuracion_scheduler` y la cantidad real de ejecuciones
`PENDIENTE`. La Web solo clasifica y presenta; no inicia procesos, no consume la
cola y no ejecuta scripts.

La topbar y las vistas operativas consumen un endpoint GET minimo mediante
polling. La ejecucion manual mantiene el contrato `Web -> PENDIENTE -> Worker`.
El lock de mantenimiento es una politica fail-closed independiente y puede
bloquear la reserva aun cuando el Worker este operativo.

Permanece como requisito de los hitos posteriores de runtime: Worker como
servicio permanente, restart automatico, healthcheck de proceso, recuperacion
de cola `PENDIENTE` y tratamiento seguro de una caida durante
`EN_EJECUCION`. Este ajuste no inicia Hito 11 ni adelanta el cutover.

## Decisiones cerradas y pendientes

### Cerradas

* Flask + Jinja + JavaScript modular.
* SQL Server mediante `pyodbc`.
* Unica base `APP_SCHEDULER_QA`.
* Web y worker separados.
* Factory Reset in-place.
* Docker QA usa `.env.docker` sin fallback.
* Release publicado no se modifica.

### Pendientes posteriores a Hito 2

* Forma exacta de la cola persistente de ejecuciones, a cerrar con el modulo del motor unico.
* Estrategia de migracion/cutover desde QA historica cuando los modulos reconstruidos esten completos.
* Retencion cuantificada de logs/evidencias/auditoria.
* Retencion y rate limiting distribuido para autenticacion quedan como hardening posterior; Hito 3 conserva intentos fallidos del modelo vigente sin introducir infraestructura externa.

## Criterio para cerrar Hito 1

Hito 1 quedo cerrado formalmente con su versionado controlado. El runtime reconstruido permanecio aislado y los hitos posteriores se iniciaron mediante autorizacion expresa.

## Criterio para cerrar Hito 2

Hito 2 quedo cerrado formalmente tras reconciliar el contrato limpio de 456 columnas con las 462 observadas en la QA historica. Las seis columnas adicionales eran aliases legacy de `auditoria_cambios`, reemplazados por columnas canonicas y conservados en QA solo por compatibilidad historica. Hitos 3-7 quedaron cerrados y Hito 8 completo su integracion tecnica read-only contra QA; el cutover permanece pendiente.

## Hub transversal de scripts

`/scripts` pertenece al mismo blueprint y caso de uso de scripts del runtime
reconstruido. La lectura global sigue el flujo
`ruta -> ServicioScripts.listar -> RepositorioScripts.listar_paginado -> SQL
parametrizado` y retorna una proyeccion `ResumenScript`; no introduce otro
servicio, repositorio ni entidad mutable.

La proyeccion excluye rutas fisicas, rutas relativas y contenido `.env`. Solo
expone cantidad de versiones con entorno configurado. El detalle conserva la
relacion `tarea 1:1 script logico` y muestra los slots v1, v2 y v3 en orden.
Este ajuste forma parte del Hito 7 cerrado. Hito 8 no se inicia con su cierre.

## Ajuste contractual de notificaciones post-Hito 10

La arquitectura mantiene cuatro responsabilidades separadas: el motor confirma
el estado de ejecucion, Evidencias captura contenido opcional desde stdout,
Notificaciones decide el evento de negocio y Microsoft Graph lo transporta.
`NOTIFICACION_EXITOSA` ya no depende de que exista Evidencia; una omision de
Evidencia no cambia una ejecucion exitosa ni dispara una alerta de error. La
migracion `022` y el bootstrap preparado expresan el invariante
`enviar_evidencia = 0 OR notificar_exito_activa = 1`. Factory Reset fue
reconstruido posteriormente y cerrado a nivel implementacion en Hito 11.
