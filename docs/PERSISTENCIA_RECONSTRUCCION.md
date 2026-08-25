# Persistencia de la reconstruccion

## Estado y fuente de verdad

Hito 2 construyo y cerro la persistencia funcional del runtime aislado
`src/app_scheduler/`. Hito 7 la extiende con repositorio de ejecuciones, logs y
evidencia; Hito 8 agrega consultas operativas y configuracion tipada; Hito 9
agrega lectura de auditoria y Papelera; Hito 10 consume las tablas existentes de
feriados y notificaciones. El ajuste contractual post-Hito 10 prepara la
migracion incremental `022` y actualiza el bootstrap canonico; no se ha aplicado
a QA ni sustituye `app/`, `run.py` o `scheduler_worker.py`.

## Persistencia Hito 10

* `RepositorioFeriados` implementa filtros/paginacion, CRUD local, estado,
  borrado manual controlado y reconciliacion `API_NAGER`. La unicidad activa
  fecha/pais y la prioridad `MANUAL` se validan antes de escribir.
* `RepositorioNotificaciones` administra una configuracion activa por tarea,
  reemplazo atomico de destinatarios TO/CC/BCC y la unica configuracion global
  `MAIL_GRAPH`.
* Cada despacho reserva `notificaciones_envios` bajo `sp_getapplock`. La
  existencia de cualquier intento previo del mismo tipo y ejecucion impide un
  segundo envio automatico; Hito 10 no implementa retries.
* El motor confirma primero estado y metadata de evidencia. El JSON parseado se
  entrega en memoria al despachador y no se persiste completo. El resultado
  Graph se confirma en una transaccion posterior, sin alterar `ejecuciones`.
* Auditoria humana comparte UoW con configuraciones y feriados; eventos tecnicos
  usan `logs_sistema`. Secretos, tokens y contenido `.env` no se persisten.

## Persistencia Hito 9

* `RepositorioAuditoria` suma lectura paginada, filtros parametrizados, detalle
  y opciones de filtro. La proyeccion es canonica incluso en QA legacy.
* `RepositorioPapelera` usa una allowlist fija de siete tablas con
  `eliminado_operativo`; la union global filtra y pagina en SQL Server.
* El retiro/restauracion bloquea la fila mediante `UPDLOCK, HOLDLOCK` y no
  confirma desde el repositorio.
* La purga de tarea/script/version se bloquea ante cualquier ejecucion historica.
  Asi conserva los valores congelados de `ejecuciones.id_script` e `id_version`
  y no contiene DELETE ni UPDATE de desacople sobre ejecuciones, logs,
  evidencias, eventos o auditoria.
* Las operaciones SQL y la auditoria comparten una UoW. El filesystem se
  prepara y pone en cuarentena antes del commit; un fallo revierte los renames.

La matriz de referencias, permisos y compensacion se mantiene en
`docs/AUDITORIA_PAPELERA_RECONSTRUCCION.md`.

## Persistencia Hito 8

* `RepositorioLogsSistema`: `COUNT` + `OFFSET/FETCH` de 25 filas, filtros
  parametrizados y detalle por PK. Niveles reales: `INFO`, `WARNING`, `ERROR`,
  `CRITICAL`.
* `RepositorioOperacion`: lectura acotada de `configuracion_scheduler`, ultimo
  heartbeat activo, metricas SQL agregadas y matriz `configuracion_sistema`.
* La unica escritura global actualiza la fila activa de
  `configuracion_scheduler` por PK y allowlist; auditoria y cambio comparten UoW.
* `RepositorioEvidencias`: upsert funcional sobre la configuracion activa de
  `notificaciones_config_tarea`, preservando el contrato `STDOUT_V1` y su indice
  unico filtrado.
* `RepositorioAuditoria` detecta dentro de la misma conexion si la QA historica
  conserva columnas legacy `NOT NULL`. En base limpia escribe solo el contrato
  canonico; en QA escribe simultaneamente columnas canonicas y aliases legacy,
  sin cambiar DDL ni hacer depender al runtime nuevo de esas columnas antiguas.
* No existe limpieza automatica de `logs_sistema`: no hay contrato vigente para
  un job destructivo. Retencion queda documentada como deuda, sin borrar datos.

## Persistencia Hito 7

`RepositorioEjecuciones` implementa reserva manual, claim atomico, ownership,
PID, solicitud de detencion, cierre condicional, `logs_tareas`, metadata de
`evidencias_ejecucion` e historial. La automatica ya reservada se consume por
`id_ejecucion` y sus `id_script`/`id_version`; no se crea otra fila.

El DDL no contiene `id_programacion`, timeout ni estado `TIMEOUT`. Hito 7 no los
oculta en otros campos: la clave automatica conserva idempotencia y el timeout
global de ambiente finaliza como `ERROR`. `PENDIENTE` es recuperable; una
`EN_EJECUCION` perdida queda incierta y no se relanza automaticamente sin una
futura lease explicita.

El contrato se extrajo estaticamente, sin consultar QA, desde:

1. `database/bootstrap/manifest.json`.
2. `database/release/002_schema_final.sql` (solo lectura).
3. `database/bootstrap/007_crear_notificaciones_evidencias.sql`.
4. `database/bootstrap/008_crear_configuracion_mail_graph.sql`.
5. `database/bootstrap/100_validacion_bootstrap_actual.sql`.

Contrato limpio preparado: 33 tablas `dbo`, 457 columnas, 25 FK, 39 CHECK, 118 DEFAULT y 120 indices. No existen vistas, procedures, funciones ni triggers propios en el bootstrap. El delta respecto del contrato cerrado de Hito 10 es una columna `BIT NOT NULL`, su DEFAULT, el CHECK Evidencia/Exito y el indice filtrado de envios exitosos.

## Inventario tecnico de las 33 tablas

La columna `Claves/reglas` resume UNIQUE, indices filtrados y CHECK relevantes. Las columnas enumeradas son las que definen el contrato funcional principal; el DDL preparado conserva el detalle completo de las 457 columnas.

| Tabla | Proposito | PK | FK | Claves/reglas y columnas clave | Modulo consumidor |
| --- | --- | --- | --- | --- | --- |
| `cat_estados_tarea` | Estados validos de tarea | `id_estado_tarea` | - | UNIQUE `codigo`; `nombre`, `activo` | Tareas |
| `cat_estados_ejecucion` | Estados de ejecucion y log | `id_estado_ejecucion` | - | UNIQUE `codigo`; `nombre`, `activo` | Ejecuciones |
| `cat_tipos_programacion` | Tipos de agenda | `id_tipo_programacion` | - | UNIQUE `codigo`; `nombre`, `activo` | Programador |
| `cat_niveles_log` | Niveles tecnicos de log | `id_nivel_log` | - | UNIQUE `codigo`; `nombre`, `activo` | Observabilidad |
| `cat_tipos_tarea` | Tarea manual o programada | `id_tipo_tarea` | - | UNIQUE `codigo`; `nombre`, `activo` | Tareas |
| `cat_estados_version_script` | Ciclo de vida de versiones | `id_estado_version_script` | - | UNIQUE `codigo`; ACTIVA/DISPONIBLE/REEMPLAZADA/INACTIVA | Scripts |
| `usuarios` | Identidad SQL de la aplicacion | `id_usuario` | - | UNIQUE `usuario`; `password_hash`, bloqueo, Papelera y `activo` | Autenticacion/Usuarios |
| `roles` | Roles funcionales | `id_rol` | - | UNIQUE `codigo_rol`; `es_sistema`, `activo` | Seguridad |
| `permisos` | Permisos por modulo/accion | `id_permiso` | - | UNIQUE `codigo_permiso` y (`modulo`,`accion`) | Seguridad |
| `usuarios_roles` | Asociacion usuario-rol | `id_usuario_rol` | `id_usuario -> usuarios`; `id_rol -> roles` | UNIQUE (`id_usuario`,`id_rol`); `activo` | Seguridad |
| `roles_permisos` | Matriz rol-permiso | `id_rol_permiso` | `id_rol -> roles`; `id_permiso -> permisos` | UNIQUE (`id_rol`,`id_permiso`); `permitido`, `activo` | Seguridad |
| `clientes` | Catalogo de clientes | `id_cliente` | - | UNIQUE `nombre_normalizado`; Papelera y `activo` | Mantenedores/Tareas |
| `categorias` | Catalogo de categorias | `id_categoria` | - | UNIQUE `nombre_normalizado`; Papelera y `activo` | Mantenedores/Tareas |
| `tipos` | Catalogo de tipos | `id_tipo` | - | UNIQUE `nombre_normalizado`; Papelera y `activo` | Mantenedores/Tareas |
| `tareas` | Proceso programable | `id_tarea` | cliente, categoria, tipo y catalogos de tipo/estado | IDs de contexto, `tipo_tarea`, `estado_tarea`, proximas fechas, Papelera | Tareas/Programador |
| `programaciones` | Agenda de una tarea | `id_programacion` | `id_tarea -> tareas`; tipo -> catalogo | CHECK intervalo, dia 1-31 y modo; fechas, horas, zona, feriados | Programador |
| `scripts` | Contenedor logico 1:1 con tarea | `id_script` | `id_tarea -> tareas`; `id_version_activa -> scripts_versiones` diferida | UNIQUE `id_tarea`; `id_version_activa`, Papelera | Scripts |
| `scripts_versiones` | Archivo/version fisica | `id_version` | `id_script -> scripts`; estado -> catalogo | UNIQUE (`id_script`,`numero_version`), CHECK 1-3, unica activa filtrada; hash/rutas/env | Scripts |
| `configuracion_sistema` | Configuracion no secreta y marcas de version | `id_configuracion` | - | UNIQUE `clave`; `valor`, `tipo_dato`, `es_sensible`, `activo` | Plataforma |
| `ejecuciones` | Historial de ejecucion | `id_ejecucion` | estado -> catalogo | CHECK origen/duracion; clave automatica unica filtrada; `id_tarea`, `id_script`, `id_version`, snapshots | Ejecuciones/Worker |
| `logs_tareas` | Log tecnico por ejecucion | `id_log` | `id_ejecucion -> ejecuciones`; estado final -> catalogo | CHECK duracion; rutas de log, codigo salida, error | Ejecuciones |
| `logs_sistema` | Eventos generales del sistema | `id` | nivel -> catalogo | CHECK nivel; actor, accion, modulo, valores e IP | Observabilidad |
| `auditoria_cambios` | Trazabilidad funcional con actor/contexto | `id_auditoria` | - | `accion`, `entidad`, antes/despues, resultado, ruta y metodo | Auditoria transversal |
| `configuracion_scheduler` | Configuracion global del programador | `id_configuracion` | - | Una fila activa filtrada; CHECK intervalo 10-3600 y concurrencia 1-20 | Programador |
| `scheduler_worker_heartbeat` | Estado de vida por worker | `id_worker` | - | Nombre activo unico filtrado; CHECK estados y contadores | Worker/Observabilidad |
| `scheduler_eventos` | Decisiones y omisiones del scheduler | `id_evento` | - | CHECK tipo/decision/origen; snapshots, clave, motivo, `activo` | Programador |
| `feriados` | Calendario local | `id_feriado` | - | Fecha/pais activo unico filtrado; CHECK pais/origen | Calendario/Programador |
| `reglas_feriados_irrenunciables` | Reglas locales mes/dia | `id_regla` | - | Pais/mes/dia activo unico filtrado; CHECK rangos | Calendario |
| `notificaciones_config_tarea` | Politica de evidencia/alerta por tarea | `id_config_notificacion` | `id_tarea -> tareas` | Una config activa por tarea; CHECK `STDOUT_V1` | Notificaciones |
| `notificaciones_destinatarios` | Destinatarios TO/CC/BCC | `id_destinatario` | config -> `notificaciones_config_tarea` | Un destinatario activo por config/tipo/canal/email; CHECK tipo/canal/email | Notificaciones |
| `evidencias_ejecucion` | Metadata minima de evidencia stdout | `id_evidencia` | `id_ejecucion -> ejecuciones` | UNIQUE `id_ejecucion`; CHECK estados/cantidades; hash sin JSON completo | Evidencias |
| `notificaciones_envios` | Intentos de envio Graph | `id_envio` | ejecucion, evidencia y auto-FK de reintento | CHECK tipo/estado/intento/status; unico envio exitoso de cliente | Notificaciones |
| `configuracion_mail_graph` | Configuracion global Mail Graph sin secret | `id_config_mail` | - | UNIQUE `MAIL_GRAPH`; una activa filtrada; secret solo `ENV`; scope/remitente validados | Configuracion/Graph |

## Relaciones principales

```text
usuarios -> usuarios_roles -> roles -> roles_permisos -> permisos

clientes ----+
categorias --+-> tareas -> programaciones
tipos -------+       |
                     +-> scripts -> scripts_versiones
                     |       ^          |
                     |       +-- id_version_activa
                     |
                     +-> notificaciones_config_tarea -> notificaciones_destinatarios

ejecuciones -> logs_tareas
     |
     +-> evidencias_ejecucion -> notificaciones_envios
     +----------------------------> notificaciones_envios
```

`ejecuciones.id_tarea`, `id_script` e `id_version` son anulables y no tienen FK en el esquema final para preservar historia despues de eliminaciones permanentes. La trazabilidad queda en esos IDs cuando existen y en snapshots. `scheduler_eventos` aplica la misma estrategia sin FK operativa.

## Arquitectura aplicada

* `compartido/base_datos.py`: proveedor inyectable, conexiones cortas, `autocommit=False` y timeouts.
* `compartido/unidad_trabajo.py`: transaccion explicita; `confirmar`, `revertir`, rollback por defecto y cierre garantizado.
* `persistencia/repositorio.py`: ejecucion DB-API comun, cierre de cursor y traduccion segura de errores.
* `persistencia/modelos.py`: DTO inmutables y patron comun de paginacion.
* `persistencia/mapeadores.py`: conversion explicita por contrato de columnas; un cambio de forma produce `ErrorPersistencia`.
* `persistencia/contratos.py`: protocolos para desacoplar futuros casos de uso.
* Repositorios funcionales: usuarios, seguridad y catalogos.

No existe conexion global, ORM, session implícita ni commit dentro de repositorios.

## Repositorios disponibles

| Repositorio | Operaciones Hito 2 | Uso posterior |
| --- | --- | --- |
| `RepositorioUsuarios` | obtener por ID, credencial por identificador, listar paginado/filtrado y actualizar ultimo login | Hito 3 |
| `RepositorioSeguridad` | listar roles/permisos, roles de usuario y permisos efectivos en una consulta | Hito 3 |
| `RepositorioClientes` | obtener, buscar por clave fisica y listar por estado | Hito 4 |
| `RepositorioCategorias` | obtener, buscar por clave fisica y listar por estado | Hito 4 |
| `RepositorioTipos` | obtener, buscar por clave fisica y listar por estado | Hito 4 |

La consulta de credencial es la unica que selecciona `password_hash`; el DTO `Usuario` no lo contiene y `CredencialUsuario` lo excluye de `repr`. Buscar un catalogo por `nombre_normalizado` incluye Papelera para respetar la restriccion fisica UNIQUE.

Hito 5 agrega `RepositorioTareas` y `RepositorioScripts`. Hito 6 agrega `RepositorioProgramaciones`, `RepositorioScheduler` y `RepositorioHeartbeat` con DTO/mapeadores explicitos. Los repositorios no hacen commit; los casos de uso y el despachador confirman la UoW.

La reserva automatica inserta `ejecuciones` en `PENDIENTE` y actualiza `tareas.proxima_ejecucion` en una sola transaccion. `UX_ejecuciones_clave_programacion_automatica` es la garantia de concurrencia: una colision 2601/2627 se interpreta como ocurrencia ya reservada y no crea una segunda ejecucion. `id_script` e `id_version` quedan congelados; `usuario_ejecucion` es nulo y `nombre_worker` conserva el actor tecnico.

No fue necesaria migracion: `programaciones` ya contiene frecuencia, modo, horas, fechas, feriados, zona y vigencia; `ejecuciones` ya contiene version, fecha/clave programada y worker; heartbeat, eventos, configuracion y feriados ya existen en el bootstrap limpio.

## Convenciones SQL

1. Esquema explicito `dbo` y columnas enumeradas; no `SELECT *`.
2. Valores siempre mediante placeholders `?` de `pyodbc`.
3. Fragmentos dinamicos solo desde opciones internas cerradas; nunca desde texto del usuario.
4. Ordenamientos fijos o mediante allowlist cuando se incorporen ordenes seleccionables.
5. Fechas permanecen como `datetime`, `date` o `time` hasta presentacion.
6. `bit` se convierte explicitamente a `bool`; estados se conservan como codigos SQL vigentes.
7. Listados crecientes usan `ORDER BY ... OFFSET ? ROWS FETCH NEXT ? ROWS ONLY` y conteo separado.
8. Los repositorios no hacen commit. El caso de uso confirma la UoW completa.

## Transacciones y errores

Lectura simple: repositorio con conexion de vida controlada. Operacion compuesta: una `UnidadTrabajoSQL` comparte la misma conexion entre repositorios, confirma una sola vez y revierte ante error o salida sin confirmacion.

Las excepciones DB-API se convierten en `ErrorPersistencia`. El detalle conserva operacion, clase tecnica y SQLSTATE valido, pero no SQL completo, parametros, connection string ni texto libre del driver.

La auditoria se invoca desde los casos de uso dentro de la misma UoW, con actor y contexto. No se genera automaticamente desde helpers SQL. Secretos Graph, passwords y contenido `.env` permanecen en variables/archivos de entorno, no en configuracion SQL.

## Estrategia de pruebas

* Fakes DB-API programables conservan SQL, parametros, rowcount, cursores y limites transaccionales.
* Tests de mapeo detectan columnas faltantes y evitan exponer hashes por representacion.
* Tests de repositorio verifican placeholders, paginacion SQL Server, ausencia de N+1 para permisos y cero commits ocultos.
* Tests de contrato parsean estaticamente 002/007/008 y exigen las 33 tablas, columnas consumidas, relaciones y reglas de versiones.
* No se crea BBDD temporal ni se consulta QA.

Hito 2 agrega 22 pruebas; la suite completa queda en 71 pruebas aprobadas.

## Reconciliacion QA historica 462 vs bootstrap limpio 456

La diferencia se origino al ejecutar sobre la tabla antigua `database/legacy_pre_release_13B/migrations/018_crear_o_ajustar_auditoria_cambios.sql`. Esa migracion agrego las columnas canonicas, copio hacia ellas la informacion anterior y mantuvo las columnas legacy para no borrar historial. Una instalacion limpia crea directamente el contrato canonico en `database/release/002_schema_final.sql`, por lo que no necesita los seis aliases.

| Tabla | Columna QA adicional | Tipo historico | Origen y reemplazo | Uso historico | Uso actual | Estado | Decision y justificacion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `auditoria_cambios` | `fecha_hora` | `datetime2(0) NOT NULL` | Migracion 005; copiada a `fecha_evento` por 018 | Fecha original del evento | Solo fallback de compatibilidad | REEMPLAZADA | Excluir del contrato limpio; `fecha_evento` conserva semantica y DEFAULT |
| `auditoria_cambios` | `tabla_afectada` | `nvarchar(100) NOT NULL` | Migracion 005; copiada a `entidad` por 018 | Nombre de tabla auditada | Solo fallback de compatibilidad | REEMPLAZADA | Excluir; `entidad` es la columna canonica consumida |
| `auditoria_cambios` | `id_registro` | `nvarchar(100) NOT NULL` | Migracion 005; copiada a `id_entidad` por 018 | Identificador auditado | Solo fallback de compatibilidad | REEMPLAZADA | Excluir; `id_entidad` admite identificadores equivalentes |
| `auditoria_cambios` | `valor_anterior` | `nvarchar(max) NULL` | Migracion 005; copiada a `valores_antes` por 018 | Snapshot anterior | Solo fallback de compatibilidad | REEMPLAZADA | Excluir; `valores_antes` es el contrato vigente |
| `auditoria_cambios` | `valor_nuevo` | `nvarchar(max) NULL` | Migracion 005; copiada a `valores_despues` por 018 | Snapshot posterior | Solo fallback de compatibilidad | REEMPLAZADA | Excluir; `valores_despues` es el contrato vigente |
| `auditoria_cambios` | `ip` | `varchar(45) NULL` | Migracion 005; convertida a `ip_origen` por 018 | IP de origen | Solo fallback de compatibilidad | REEMPLAZADA | Excluir; `ip_origen nvarchar(100)` amplia capacidad |

Evidencia adicional: `app/repositorios/repositorio_auditoria.py` prefiere siempre las columnas canonicas y usa las legacy solo cuando aquellas no existen; al registrar sobre una QA historica escribe ambas para compatibilidad. No hay funcionalidad vigente que requiera las seis columnas en una base limpia. El DEFAULT e indices legacy asociados a `fecha_hora`, `tabla_afectada` e `id_registro` tampoco forman parte del contrato canonico.

Decision: las seis columnas quedan clasificadas como `C. REEMPLAZADA`. El contrato definitivo permanece en 33 tablas y 456 columnas. No se modificaron bootstrap, release, migraciones ni QA.

## Deuda documentada

* La compatibilidad de auditoria 462/456 quedo reconciliada; el detalle y la decision contractual se mantienen en la seccion anterior.
* `scripts.id_version_activa` y `scripts_versiones.es_activa` se actualizan en una unica UoW; el indice filtrado sigue siendo la garantia fisica de una sola activa.
* El maximo de tres se controla por slots libres en servicio y por `CHECK(numero_version BETWEEN 1 AND 3)` mas `UNIQUE(id_script, numero_version)`.
* Un slot no activo solo puede reemplazarse cuando `ejecuciones.id_version` no lo referencia. El esquema limpio no contiene otra columna funcional que apunte a `scripts_versiones.id_version`.
* La clave funcional de tarea (`nombre_tarea`, cliente, categoria y tipo) se valida en servicio, pero no tiene UNIQUE fisico en el esquema vigente; una carrera concurrente extrema queda como deuda legitima sin migracion autorizada.
* Las UNIQUE fisicas de usuarios/catalogos/versiones incluyen registros en Papelera; los servicios deben distinguir activo, inactivo y eliminado antes de escribir.
* El modelo no incluye views/procedures para paginacion o seguridad; las consultas permanecen explicitas en repositorios.
* Hito 6 define `SolicitudEjecucion` comun y reserva automatica `PENDIENTE`; Hito 7 implementa el reclamo y motor unico sin crear un segundo contrato.
