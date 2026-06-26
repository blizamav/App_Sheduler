# Auditoria Release SQL - Fase 13B.1

## 1. Resumen ejecutivo

Se realizo auditoria estatica del release SQL limpio contra el schema consolidado, seeds historicos y usos principales del backend Python.

Resultado: el release tenia inconsistencias de seeds frente a columnas `NOT NULL` del schema final. Se corrigieron los scripts release para que la instalacion limpia pueda reintentarse manualmente en `APP_SCHEDULER_TEST_INSTALL` sin aplicar parches directos en base de datos.

No se ejecuto SQL, no se conecto a SQL Server, no se modifico `.env`, no se toco `APP_SCHEDULER_QA` ni `APP_SCHEDULER_TEST_INSTALL`.

## 2. Errores encontrados durante Fase 13B

| Script | Error | Causa |
|---|---|---|
| `003_seed_roles_permisos.sql` | `Cannot insert the value NULL into column 'codigo_rol'` | El seed creaba roles sin informar `codigo_rol`, requerido por `dbo.roles`. |
| `004_seed_catalogos_base.sql` | `Cannot insert the value NULL into column 'nombre'` en catalogos | Los `MERGE` informaban `codigo` y `descripcion`, pero omitian `nombre`, requerido por todos los catalogos base. |
| `005_seed_configuracion_inicial.sql` | Riesgo detectado antes de ejecutar | El seed usaba columna `observacion` en `configuracion_scheduler`, pero el schema tiene `descripcion`; ademas omitio `tipo_dato` en `configuracion_sistema`. |
| `004_seed_catalogos_base.sql` | Riesgo funcional | `cat_tipos_tarea` tenia valores tecnicos (`PYTHON`, `BAT`) pero el backend usa `MANUAL` y `PROGRAMADA`. |

## 3. Causa raiz

El release SQL fue consolidado manualmente desde migraciones y seeds incrementales, pero algunos seeds quedaron desacoplados del schema final:

- Se omitieron columnas obligatorias sin `DEFAULT`.
- Algunos `MERGE` usaban nombres visibles en vez de codigos estables.
- Un seed uso una columna antigua/inexistente.
- Un catalogo quedo con valores que no coinciden con los codigos que inserta el backend.

## 3.1. Correccion de criterio: roles base

Durante la correccion inicial del seed `003` se simplificaron y reinterpretaron indebidamente los roles base del release. Ese criterio era incorrecto para Fase 13B.1, porque el release limpio debe replicar el estado base real de `APP_SCHEDULER_QA`, no redisenar la seguridad.

La comparacion contra `APP_SCHEDULER_QA` confirmo que los roles base reales son:

- `SUPER_ADMIN`
- `ADMIN`
- `TI`
- `TERCERO`

`APP_SCHEDULER_QA` no tiene rol `OPERADOR`; por lo tanto, `OPERADOR` fue eliminado del release ejecutable.

La matriz `roles_permisos` fue ajustada a los conteos reales de QA:

- `SUPER_ADMIN`: 39 permisos.
- `ADMIN`: 37 permisos.
- `TI`: 31 permisos.
- `TERCERO`: 7 permisos.

La validacion `099_validacion_instalacion.sql` ahora incluye `VALIDACION_ROLES_BASE`, `VALIDACION_ROLES_FALTANTES`, `VALIDACION_ROLES_NO_ESPERADOS`, `VALIDACION_ROL_OPERADOR_NO_EXISTE` y `VALIDACION_ROLES_PERMISOS_ESPERADOS`. El resultado esperado es que los cuatro roles existan activos, `OPERADOR` no exista y la diferencia de permisos por rol sea `0`.

## 4. Matriz tabla por tabla

| Tabla | Clasificacion | Columnas | NOT NULL sin default relevante | PK/FK/UNIQUE/CHECK/Indices | Seed inicial | Debe quedar vacia | Uso backend | Riesgo detectado | Accion |
|---|---|---|---|---|---|---|---|---|---|
| `cat_estados_tarea` | Catalogo | `id_estado_tarea`, `codigo`, `nombre`, `descripcion`, fechas, usuarios, `activo` | `codigo`, `nombre` | PK, UX `codigo` | Si | No | FK de `tareas.estado_tarea`; servicios usan `ACTIVA`, `INACTIVA` | Seed omitia `nombre` | Corregido en `004`. |
| `cat_estados_ejecucion` | Catalogo | `id_estado_ejecucion`, `codigo`, `nombre`, `descripcion`, fechas, usuarios, `activo` | `codigo`, `nombre` | PK, UX `codigo` | Si | No | FK de `ejecuciones` y `logs_tareas`; ejecuciones usan `EN_EJECUCION`, `EXITOSA`, `ERROR`, `DETENIDA_MANUALMENTE` | Seed omitia `nombre` | Corregido en `004`. |
| `cat_tipos_programacion` | Catalogo | `id_tipo_programacion`, `codigo`, `nombre`, `descripcion`, fechas, usuarios, `activo` | `codigo`, `nombre` | PK, UX `codigo` | Si | No | `servicio_tareas`, `servicio_programador`, `repositorio_scheduler` | Seed omitia `nombre` | Corregido en `004`. |
| `cat_niveles_log` | Catalogo | `id_nivel_log`, `codigo`, `nombre`, `descripcion`, fechas, usuarios, `activo` | `codigo`, `nombre` | PK, UX `codigo` | Si | No | FK de `logs_sistema.nivel` | Seed omitia `nombre`; faltaba `CRITICAL` | Corregido en `004`. |
| `cat_tipos_tarea` | Catalogo | `id_tipo_tarea`, `codigo`, `nombre`, `descripcion`, fechas, usuarios, `activo` | `codigo`, `nombre` | PK, UX `codigo` | Si | No | FK de `tareas.tipo_tarea`; backend usa `MANUAL` y `PROGRAMADA` | Valores no coincidian con backend | Corregido en `004`. |
| `cat_estados_version_script` | Catalogo | `id_estado_version_script`, `codigo`, `nombre`, `descripcion`, fechas, usuarios, `activo` | `codigo`, `nombre` | PK, UX `codigo` | Si | No | `servicio_scripts`, `repositorio_scripts` | Seed omitia `nombre` | Corregido en `004`. |
| `usuarios` | Seguridad | usuario, nombre, email, hash, bloqueo, eliminado operativo, fechas, activo | `usuario`, `nombre_completo`, `password_hash` | PK, UX `usuario`, indices operativo | No | Si | `repositorio_usuarios`, login SQL | No se deben crear usuarios reales | Sin seed. |
| `roles` | Seguridad | `codigo_rol`, `nombre_rol`, descripcion, sistema, fechas, activo | `codigo_rol`, `nombre_rol` | PK, UX `codigo_rol` | Si | No | `repositorio_roles`, `repositorio_permisos`, reglas `SUPER_ADMIN`/`ADMIN` | Seed omitio `codigo_rol` | Corregido en `003`. |
| `permisos` | Seguridad | `codigo_permiso`, modulo, accion, descripcion, fechas, activo | `codigo_permiso`, `modulo`, `accion` | PK, UX `codigo_permiso`, UX modulo/accion | Si | No | Decoradores `permiso_requerido` y sidebar | Sin error confirmado | Revisado. |
| `usuarios_roles` | Seguridad | usuario, rol, fecha, usuario_creacion, activo | IDs por FK | PK, UX usuario/rol, FKs | No | Si | Asignacion de roles a usuarios | No crear usuarios reales | Sin seed. |
| `roles_permisos` | Seguridad | rol, permiso, permitido, fecha, usuario_creacion, activo | IDs por FK | PK, UX rol/permiso, FKs | Si | No | Carga permisos de sesion | Debia relacionar por codigo estable | Corregido en `003`. |
| `clientes` | Maestra operativa | nombre, normalizado, descripcion, eliminado operativo, fechas, activo | `nombre_cliente`, `nombre_normalizado` | PK, UX normalizado | No | Si | mantenedores, tareas, snapshots | No cargar datos reales | Sin seed. |
| `categorias` | Maestra operativa | nombre, normalizado, descripcion, eliminado operativo, fechas, activo | `nombre_categoria`, `nombre_normalizado` | PK, UX normalizado | No | Si | mantenedores, tareas, snapshots | No cargar datos reales | Sin seed. |
| `tipos` | Maestra operativa | nombre, normalizado, descripcion, eliminado operativo, fechas, activo | `nombre_tipo`, `nombre_normalizado` | PK, UX normalizado | No | Si | mantenedores, tareas, snapshots | No cargar datos reales | Sin seed. |
| `tareas` | Operativa | nombre, descripcion, observacion, cliente/categoria/tipo, tipo/estado, ejecucion, eliminado operativo, fechas, activo | `nombre_tarea`, `tipo_tarea`, `estado_tarea` | PK, FKs a maestros/catalogos, indices | No | Si | `repositorio_tareas`, scheduler, panel | Depende de catalogos correctos | Corregido `cat_tipos_tarea`. |
| `programaciones` | Operativa | tarea, tipo, modo, horas, intervalo, dias, fechas, feriados, zona, vigencia, fechas, activo | `tipo_programacion` | PK, FK tarea/catalogo, checks, indices | No | Si | `repositorio_tareas`, `repositorio_scheduler` | Catalogo debe incluir tipos usados | Corregido `004`. |
| `scripts` | Operativa | tarea, nombre, descripcion, version activa, eliminado operativo, fechas, activo | `nombre_script` | PK, FK tarea y version activa, UX tarea | No | Si | `repositorio_scripts`, ejecuciones | Debe quedar vacia | Sin seed. |
| `scripts_versiones` | Operativa | script, numero, archivo, rutas, hash, estado, activa, env, carga, eliminado, fechas | numero, archivo, rutas, hash, estado, usuario_carga | PK, FK, checks, UX script/version, UX activa | No | Si | `repositorio_scripts`, ejecuciones | Debe quedar vacia | Sin seed. |
| `configuracion_sistema` | Configuracion | clave, valor, tipo_dato, descripcion, sensible, fechas, activo | `clave`, `valor`, `tipo_dato` | PK, UX clave | Si | No | Configuracion general futura | Seed omitio `tipo_dato` | Corregido en `005`. |
| `ejecuciones` | Historica/ejecucion | IDs, origen, estado, inicio/termino, PID, detencion, programacion, worker, snapshots | `origen_ejecucion`, `estado_ejecucion`, `fecha_hora_inicio` | PK, FK estado, checks, indices | No | Si | `repositorio_ejecuciones`, panel, scheduler | Debe quedar vacia | Sin seed. |
| `logs_tareas` | Historica/logs | ejecucion, tarea, nombres, rutas log, inicio/termino, estado, salida, usuario | log fields y `estado_final` | PK, FK ejecucion/estado, checks | No | Si | consola y logs de ejecucion | Debe quedar vacia | Sin seed. |
| `logs_sistema` | Historica/logs | usuario, accion, modulo, descripcion, valores, ip, user_agent, fecha, nivel | `accion`, `modulo`, `descripcion`, `nivel` | PK, FK nivel, check | No | Si | `servicio_logs_sistema`, auditoria fallback | Debe quedar vacia | Sin seed. |
| `auditoria_cambios` | Auditoria | fecha, usuario, accion, entidad, id/nombre, valores, ip, resultado, modulo, ruta, metodo, activo | `usuario`, `accion`, `entidad` | PK, indices auditoria | No | Si | `servicio_auditoria`, `/auditoria` | Debe quedar vacia | Sin seed. |
| `configuracion_scheduler` | Scheduler/configuracion | flags, intervalo, max, worker, descripcion, fechas, activo | Defaults cubren obligatorias | PK, checks, UX activa | Si | No | `repositorio_configuracion_scheduler`, worker | Seed usaba `observacion` inexistente | Corregido en `005`. |
| `scheduler_worker_heartbeat` | Scheduler/ejecucion | worker, estado, fechas, resultado, contadores, pid, host, version, activo | `nombre_worker` | PK, checks, UX worker activo | No | Si | `repositorio_worker_heartbeat`, panel | Debe quedar vacia | Sin seed. |
| `scheduler_eventos` | Scheduler/historica | fecha, worker, tarea, snapshots, programacion, tipo, decision, motivo, detalle, feriado, origen, activo | `tipo_evento`, `decision` | PK, checks, indices filtros | No | Si | `repositorio_scheduler_eventos`, panel/eventos | Debe quedar vacia | Sin seed. |
| `feriados` | Maestra calendario | fecha, nombre, tipo, pais, irrenunciable, activo, origen, observacion, fechas, usuarios | `fecha`, `nombre` | PK, check origen, UX fecha/pais activo | No | Si | `repositorio_feriados`, calendario | No cargar API/manuales reales | Sin seed. |
| `reglas_feriados_irrenunciables` | Catalogo/reglas | pais, mes, dia, nombre, irrenunciable, activo, observacion, fechas, usuarios | `mes`, `dia`, `nombre_referencia` | PK, checks, UX pais/mes/dia activo | Si | No | `repositorio_reglas_feriados`, sincronizacion | Revisado | Seed `006` correcto. |

## 5. Matriz seed por seed

| Seed release | Objetivo | Tablas | Requiere datos | Idempotencia | Hallazgos | Accion |
|---|---|---|---|---|---|---|
| `003_seed_roles_permisos.sql` | Roles, permisos y relaciones | `roles`, `permisos`, `roles_permisos` | Si | `MERGE` por codigo y `NOT EXISTS` en relaciones | Faltaba `codigo_rol`; relaciones usaban `nombre_rol` | Corregido. |
| `004_seed_catalogos_base.sql` | Catalogos base | `cat_*` | Si | `MERGE` por `codigo` | Faltaba `nombre`; `cat_tipos_tarea` no coincidia con backend | Corregido. |
| `005_seed_configuracion_inicial.sql` | Configuracion minima | `configuracion_scheduler`, `configuracion_sistema` | Si | `IF NOT EXISTS` | Columna `observacion` inexistente; faltaba `tipo_dato` | Corregido. |
| `006_seed_feriados_base.sql` | Reglas irrenunciables Chile | `reglas_feriados_irrenunciables` | Si | `MERGE` por pais/mes/dia/activo | Sin error detectado | Mantener. |

## 6. Tablas que deben quedar con datos

- `roles`
- `permisos`
- `roles_permisos`
- `cat_estados_tarea`
- `cat_estados_ejecucion`
- `cat_tipos_programacion`
- `cat_niveles_log`
- `cat_tipos_tarea`
- `cat_estados_version_script`
- `configuracion_scheduler`
- `configuracion_sistema`
- `reglas_feriados_irrenunciables`

## 7. Tablas que deben quedar vacias

- `usuarios`
- `usuarios_roles`
- `clientes`
- `categorias`
- `tipos`
- `tareas`
- `programaciones`
- `scripts`
- `scripts_versiones`
- `ejecuciones`
- `logs_tareas`
- `logs_sistema`
- `auditoria_cambios`
- `scheduler_worker_heartbeat`
- `scheduler_eventos`
- `feriados`

## 8. Columnas NOT NULL revisadas

Se revisaron las columnas `NOT NULL` sin default relevante. Las que afectan seeds release fueron:

- `roles.codigo_rol`, `roles.nombre_rol`
- `permisos.codigo_permiso`, `permisos.modulo`, `permisos.accion`
- `cat_*.codigo`, `cat_*.nombre`
- `configuracion_sistema.clave`, `configuracion_sistema.valor`, `configuracion_sistema.tipo_dato`
- `configuracion_scheduler` cubre obligatorias por default, pero el seed debe usar columnas existentes
- `reglas_feriados_irrenunciables.mes`, `dia`, `nombre_referencia`

## 9. Catalogos requeridos por la app

- Estados tarea: `ACTIVA`, `INACTIVA`.
- Estados ejecucion: `PENDIENTE`, `EN_EJECUCION`, `EXITOSA`, `ERROR`, `CANCELADA`, `DETENIDA_MANUALMENTE`.
- Tipos programacion: `MANUAL`, `DIARIA`, `SEMANAL`, `MENSUAL`, `FECHA_ESPECIFICA`.
- Tipos tarea: `MANUAL`, `PROGRAMADA`.
- Estados version script: `ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`.
- Niveles log: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

## 10. Roles y permisos requeridos por la app

Roles base del release:

- `SUPER_ADMIN`
- `ADMIN`
- `TI`
- `TERCERO`

Permisos base del release:

- Panel: `PANEL_VER`
- Usuarios/configuracion: `USUARIOS_ADMIN`, `CONFIGURACION_ADMIN`
- Mantenedores: `CLIENTES_*`, `CATEGORIAS_*`, `TIPOS_*`
- Tareas: `TAREAS_*`
- Scripts: `SCRIPTS_*`
- Ejecuciones/logs: `EJECUCIONES_*`, `LOGS_VER`
- Scheduler: `SCHEDULER_CONFIG_VER`, `SCHEDULER_CONFIG_EDITAR`
- Feriados: `FERIADOS_*`
- Papelera: `PAPELERA_*`
- Auditoria: `AUDITORIA_VER`, `AUDITORIA_DETALLE`

El release replica `APP_SCHEDULER_QA`: `OPERADOR` no se crea porque no existe en la base real actual.

## 11. Configuraciones minimas requeridas

`configuracion_scheduler` debe tener un registro activo con:

- `scheduler_activo = 0`
- `permitir_ejecucion_automatica = 0`
- `intervalo_revision_segundos = 60`
- `max_ejecuciones_concurrentes = 3`
- `modo_mantenimiento = 0`
- `nombre_worker_principal = worker_default`

`configuracion_sistema` debe incluir `RELEASE_SQL` con `tipo_dato = TEXTO`.

## 12. Riesgos detectados

| Riesgo | Estado |
|---|---|
| Base de prueba parcial tras fallos previos | Requiere reiniciar manualmente la prueba desde base limpia. |
| Rol `OPERADOR` creado por reinterpretacion | Corregido: `OPERADOR` eliminado del release porque no existe en `APP_SCHEDULER_QA`. |
| Conteos de permisos por rol no coincidian con QA | Corregido: `SUPER_ADMIN = 39`, `ADMIN = 37`, `TI = 31`, `TERCERO = 7`. |
| No se ejecuto SQL desde Codex | Correcto por regla; validacion real queda manual. |
| Release apunta a base fija `APP_SCHEDULER_TEST_INSTALL` | Correcto para Fase 13B; si se usa otro nombre debe cambiarse controladamente en todos los scripts. |

## 13. Correcciones aplicadas

- `003`: roles con `codigo_rol`, `nombre_rol`, `descripcion`, `es_sistema`; `MERGE` por `codigo_rol`; relaciones por `codigo_rol`; roles base `SUPER_ADMIN`, `ADMIN`, `TI` y `TERCERO`; `OPERADOR` eliminado del release ejecutable.
- `004`: todos los catalogos incluyen `nombre`; se agrego `CRITICAL`; `cat_tipos_tarea` queda en `MANUAL` y `PROGRAMADA`.
- `005`: `configuracion_scheduler` usa `descripcion`; se agrega `nombre_worker_principal`; `configuracion_sistema` incluye `tipo_dato`.
- `099`: validacion por secciones para base, tablas, roles, permisos, catalogos, configuracion, tablas vacias, columnas NOT NULL, seguridad, indices, FKs y checks.

## 14. Validaciones manuales que debe ejecutar el usuario

Ejecutar manualmente en SSMS sobre una base limpia:

1. `database/release/001_crear_base_datos.sql`
2. `database/release/002_schema_final.sql`
3. `database/release/003_seed_roles_permisos.sql`
4. `database/release/004_seed_catalogos_base.sql`
5. `database/release/005_seed_configuracion_inicial.sql`
6. `database/release/006_seed_feriados_base.sql`
7. `database/release/099_validacion_instalacion.sql`

Resultados esperados:

- `VALIDACION_BASE.resultado = OK`.
- Todas las tablas esperadas con `existe = 1`.
- `VALIDACION_ROLES_FALTANTES.roles_faltantes = 0`.
- `VALIDACION_ROL_OPERADOR_NO_EXISTE.total_operador = 0`.
- `VALIDACION_ROLES_PERMISOS_ESPERADOS.diferencia = 0` para `SUPER_ADMIN`, `ADMIN`, `TI` y `TERCERO`.
- `roles_codigo_nulo = 0`.
- Catalogos con `nombres_nulos = 0`.
- Codigos criticos con `total = 1`.
- Una configuracion scheduler activa con defaults seguros.
- Tablas operativas/historicas vacias con `total = 0`.
- `configuracion_sistema_posibles_secretos = 0`.
- `configuracion_sistema_rutas_locales = 0`.
- Indices, FKs y checks presentes.

## 15. Estado final recomendado

Reintentar Fase 13B desde una base limpia `APP_SCHEDULER_TEST_INSTALL`. No avanzar a Fase 13C hasta que los scripts `001` a `006` y `099` se ejecuten sin errores y los resultados de validacion queden documentados.
