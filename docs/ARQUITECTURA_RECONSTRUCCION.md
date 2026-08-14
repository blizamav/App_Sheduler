# Arquitectura de Reconstruccion

## Estado

Arquitectura maestra aprobada al cerrar Hito 0. Hito 1 implemento sus cimientos y Hito 2 cerro la persistencia funcional en el mismo runtime aislado; el runtime historico sigue activo y no se ha realizado cutover.

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
| Hilos web para ejecucion | `worker/contratos.py` | Solo contrato comun; motor real bloqueado hasta Hito 7. |

No se copiaron rutas funcionales, repositorios de tablas, scheduler, motor de ejecucion, Graph, feriados, papelera ni Factory Reset. Los entrypoints `run.py` y `scheduler_worker.py` siguen apuntando exclusivamente al runtime historico.

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
6. auditar resultado y limpiar temporales.

Todas las rutas se resuelven contra raices configuradas y se rechazan traversal, symlinks inseguros, raices contenidas y nombres fuera de contrato.

## Scheduler, cola y worker

El worker sera propietario de dos bucles coordinados:

* programador: evalua calendarios y genera solicitudes automaticas;
* ejecutor: reclama solicitudes manuales o automaticas y lanza procesos.

La web manual solo solicita ejecucion. No crea `threading.Thread` ni procesos Python. La solicitud persistente debe contener origen, tarea, script, version, actor y fecha. El worker la reclama de forma atomica y registra PID, salida y cierre.

El contrato definitivo de cola se diseña en Hito 2. Preferencia: extender estados/columnas de `ejecuciones` si mantiene claridad; crear tabla de solicitudes solo si evita ambiguedad real. Debe incluir lease o marca de reclamo para recuperacion tras caida.

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

Graph se encapsula tras un cliente propio. El servicio decide destinatarios, idempotencia, reintentos limitados y estado del envio. El client secret proviene exclusivamente del entorno y nunca vuelve a HTML, logs o auditoria.

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

## Docker y operacion

Compose mantiene dos servicios:

* `web`: aplicacion Flask/WSGI segun ambiente;
* `worker`: scheduler y motor de ejecucion.

Ambos usan la misma imagen y `.env.docker`, con volumenes compartidos solo donde el contrato lo exige. El Hito 13 validara healthchecks, shutdown, permisos de volumen, ODBC, SQLCMD y recuperacion tras reinicio. Produccion requerira WSGI, secretos externos, backup, retencion y observabilidad como hito separado.

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

Hito 1 quedo cerrado formalmente con su versionado controlado. El runtime reconstruido permanecio aislado y Hito 2 se inicio posteriormente mediante autorizacion expresa.

## Criterio para cerrar Hito 2

Hito 2 quedo cerrado formalmente tras reconciliar el contrato limpio de 456 columnas con las 462 observadas en la QA historica. Las seis columnas adicionales eran aliases legacy de `auditoria_cambios`, reemplazados por columnas canonicas y conservados en QA solo por compatibilidad historica. Hito 3 quedo cerrado con autenticacion, usuarios, roles/permisos y auditoria implementados en el runtime aislado. Hito 4 quedo cerrado con clientes, categorias y tipos sobre la persistencia y seguridad comunes; Hito 5 no fue iniciado.
