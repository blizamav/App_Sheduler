# Base de datos

## Estado

Fase 3B - Scripts SQL Server versionados creados. No se ha creado conexion real desde Flask, no se han ejecutado scripts automaticamente y no se ha creado ninguna tabla desde Codex.

## Base objetivo

* Motor: SQL Server.
* Base: `APP_SCHEDULER_QA`.
* Variable de entorno: `DB_DATABASE`.
* Servidor, usuario, clave y driver deben venir desde `.env`.

## Scripts SQL versionados

Estructura creada:

```text
database/
  migrations/
    001_crear_base_datos.sql
    002_crear_catalogos.sql
    003_crear_tablas_seguridad.sql
    004_crear_tablas_negocio.sql
    005_crear_tablas_ejecucion_logs.sql
    006_crear_indices.sql
  seeds/
    001_datos_iniciales_catalogos.sql
    002_roles_permisos_iniciales.sql
```

Orden correcto de ejecucion manual en SQL Server Management Studio:

1. `database/migrations/001_crear_base_datos.sql`
2. `database/migrations/002_crear_catalogos.sql`
3. `database/migrations/003_crear_tablas_seguridad.sql`
4. `database/migrations/004_crear_tablas_negocio.sql`
5. `database/migrations/005_crear_tablas_ejecucion_logs.sql`
6. `database/migrations/006_crear_indices.sql`
7. `database/seeds/001_datos_iniciales_catalogos.sql`
8. `database/seeds/002_roles_permisos_iniciales.sql`

Resumen por script:

* `001_crear_base_datos.sql`: crea `APP_SCHEDULER_QA` si no existe.
* `002_crear_catalogos.sql`: crea catalogos de estados, tipos y niveles.
* `003_crear_tablas_seguridad.sql`: crea usuarios, roles, permisos, usuarios_roles y roles_permisos. No crea usuario inicial.
* `004_crear_tablas_negocio.sql`: crea clientes, categorias, tipos, tareas, programaciones, scripts, scripts_versiones y configuracion_sistema.
* `005_crear_tablas_ejecucion_logs.sql`: crea ejecuciones, logs_tareas, logs_sistema y auditoria_cambios.
* `006_crear_indices.sql`: crea indices recomendados, indice unico filtrado para version activa y FK diferida `scripts.id_version_activa`.
* `001_datos_iniciales_catalogos.sql`: inserta estados y catalogos base con `MERGE`.
* `002_roles_permisos_iniciales.sql`: inserta roles y permisos base con `MERGE`; no crea usuarios.

Restricciones implementadas en scripts:

* `IF DB_ID(...) IS NULL` para crear base.
* `IF OBJECT_ID(...) IS NULL` para crear tablas.
* PK, FK y `UNIQUE` principales.
* FK desde estados/tipos operativos hacia tablas catalogo.
* `CHECK(numero_version BETWEEN 1 AND 3)`.
* `UNIQUE(id_script, numero_version)`.
* Indice unico filtrado `UX_scripts_versiones_script_activa` para una sola version activa por `id_script`.
* `CHECK` para estados simples de versiones, origen de ejecucion, niveles de log y rangos basicos.

## Resumen del ajuste de versionamiento

El modelo separa el concepto de script en dos niveles:

* `scripts`: script logico asociado a una tarea. Representa el proceso/script como entidad estable.
* `scripts_versiones`: archivos Python versionados disponibles para ese script logico.

Decision aprobada: se mantiene esta separacion `scripts` + `scripts_versiones`.

Reglas principales:

* Cada tarea puede tener un script logico asociado.
* Cada script logico puede mantener maximo 3 versiones disponibles.
* Solo una version puede estar activa por script.
* La ejecucion automatica usa siempre la version activa.
* La ejecucion manual puede usar la activa o una version especifica disponible.
* Toda ejecucion registra `id_script` e `id_version`.
* Los logs se relacionan con `id_ejecucion`; desde ejecuciones se obtiene script y version exacta.
* Los reemplazos de version quedan en `auditoria_cambios` y `logs_sistema`.
* Una version `REEMPLAZADA` no cuenta dentro del maximo de 3 versiones disponibles.
* `scripts.id_version_activa` se mantiene como referencia directa a la version activa.

## Convenciones propuestas

* Tablas en minuscula y plural: `usuarios`, `scripts_versiones`.
* Llaves primarias con prefijo `id_`.
* Llaves foraneas con el mismo nombre de la PK referenciada.
* Fechas en `datetime2(0)`.
* Estados en `varchar(30)` con validacion desde servicio y `CHECK` cuando sea simple.
* Rutas en `nvarchar(500)`.
* Hash de archivos en `varchar(128)`.

## Campos estandar recomendados

* `fecha_creacion datetime2(0) not null default sysdatetime()`
* `fecha_actualizacion datetime2(0) null`
* `usuario_creacion nvarchar(100) null`
* `usuario_actualizacion nvarchar(100) null`
* `activo bit not null default 1`

## Estados propuestos

### estado_tarea

`ACTIVA`, `INACTIVA`, `SUSPENDIDA`, `EN_EJECUCION`, `ERROR`, `FINALIZADA`.

### estado_ejecucion

`PENDIENTE`, `EN_EJECUCION`, `EXITOSA`, `ERROR`, `CANCELADA`, `OMITIDA`, `OMITIDA_FERIADO`, `OMITIDA_FIN_SEMANA`.

### tipo_programacion

`DIARIA`, `SEMANAL`, `MENSUAL`, `FECHAS_ESPECIFICAS`, `INTERVALO_DIARIO`, `MANUAL`.

### estado_version

`ACTIVA`, `DISPONIBLE`, `REEMPLAZADA`, `INACTIVA`.

## Tablas criticas para primera version

* `usuarios`
* `roles`
* `permisos`
* `usuarios_roles`
* `clientes`
* `categorias`
* `tipos`
* `tareas`
* `programaciones`
* `scripts`
* `scripts_versiones`
* `ejecuciones`
* `logs_tareas`
* `logs_sistema`
* `auditoria_cambios`
* `configuracion_sistema`

## Tablas futuras no implementables aun

* `feriados`
* `calendarios_laborales`
* `notificaciones`
* `parametros_tarea`
* `ambientes`
* `respaldos`

## Relaciones principales

* Un usuario puede tener varios roles mediante `usuarios_roles`.
* Un rol puede tener varios permisos mediante `permisos`.
* Una tarea pertenece a un cliente, categoria y tipo.
* Una tarea tiene un script logico mediante `scripts.id_tarea`.
* Un script logico tiene hasta 3 versiones disponibles en `scripts_versiones`.
* `scripts.id_version_activa` referencia la version activa vigente.
* Una programacion pertenece a una tarea.
* Una ejecucion pertenece a una tarea, script logico y version exacta ejecutada.
* Un log de tarea pertenece a una ejecucion.
* Auditoria registra cambios de versiones, activaciones y reemplazos.

## Diccionario inicial de datos

### usuarios

Objetivo: almacenar usuarios internos de la aplicacion cuando se implemente Fase 4.

Campos: `id_usuario int identity`, `usuario nvarchar(100)`, `nombre_completo nvarchar(200)`, `email nvarchar(200) null`, `password_hash nvarchar(300)`, `debe_cambiar_password bit`, `ultimo_login datetime2(0) null`, `intentos_fallidos int`, `bloqueado bit`, campos estandar.
PK: `id_usuario`.
Indices: `UX_usuarios_usuario`, `IX_usuarios_activo`.
Observacion: el usuario inicial sigue viniendo desde `.env` hasta Fase 4.

### roles

Objetivo: definir perfiles de acceso.

Campos: `id_rol int identity`, `nombre_rol nvarchar(80)`, `descripcion nvarchar(300) null`, `es_sistema bit`, campos estandar.
PK: `id_rol`.
Indices: `UX_roles_nombre_rol`.

### permisos

Objetivo: controlar permisos por modulo y accion para cada rol.

Campos: `id_permiso int identity`, `id_rol int`, `modulo nvarchar(80)`, `accion nvarchar(80)`, `permitido bit`, campos estandar.
PK: `id_permiso`.
FK: `id_rol -> roles.id_rol`.
Indices: `IX_permisos_rol_modulo`, `UX_permisos_rol_modulo_accion`.

### usuarios_roles

Objetivo: relacionar usuarios con uno o mas roles.

Campos: `id_usuario_rol int identity`, `id_usuario int`, `id_rol int`, `fecha_creacion datetime2(0)`, `usuario_creacion nvarchar(100) null`, `activo bit`.
PK: `id_usuario_rol`.
FK: `id_usuario -> usuarios.id_usuario`, `id_rol -> roles.id_rol`.
Indices: `UX_usuarios_roles_usuario_rol`, `IX_usuarios_roles_rol`.

### clientes

Objetivo: catalogar clientes asociados a tareas.

Campos: `id_cliente int identity`, `nombre_cliente nvarchar(150)`, `nombre_normalizado nvarchar(150)`, `descripcion nvarchar(300) null`, campos estandar.
PK: `id_cliente`.
Indices: `UX_clientes_nombre_normalizado`, `IX_clientes_activo`.

### categorias

Objetivo: agrupar tareas por categoria funcional.

Campos: `id_categoria int identity`, `nombre_categoria nvarchar(150)`, `nombre_normalizado nvarchar(150)`, `descripcion nvarchar(300) null`, campos estandar.
PK: `id_categoria`.
Indices: `UX_categorias_nombre_normalizado`.

### tipos

Objetivo: clasificar tareas por tipo operacional.

Campos: `id_tipo int identity`, `nombre_tipo nvarchar(150)`, `nombre_normalizado nvarchar(150)`, `descripcion nvarchar(300) null`, campos estandar.
PK: `id_tipo`.
Indices: `UX_tipos_nombre_normalizado`.

### tareas

Objetivo: registrar tareas ejecutables asociadas a cliente, categoria, tipo y script logico.

| Campo | Tipo SQL Server | Descripcion |
| --- | --- | --- |
| id_tarea | int identity(1,1) | PK |
| nombre_tarea | nvarchar(200) | Nombre visible |
| descripcion | nvarchar(1000) null | Detalle |
| id_cliente | int | FK clientes |
| id_categoria | int | FK categorias |
| id_tipo | int | FK tipos |
| tipo_tarea | varchar(20) | PROGRAMADA o MANUAL |
| estado_tarea | varchar(30) | Estado operacional |
| ultima_ejecucion | datetime2(0) null | Ultima ejecucion |
| proxima_ejecucion | datetime2(0) null | Proxima ejecucion calculada |
| ultimo_estado_ejecucion | varchar(30) null | Resultado reciente |
| permite_ejecucion_manual | bit | Habilita ejecucion manual |
| fecha_creacion | datetime2(0) | Auditoria |
| fecha_actualizacion | datetime2(0) null | Auditoria |
| usuario_creacion | nvarchar(100) null | Auditoria |
| usuario_actualizacion | nvarchar(100) null | Auditoria |
| activo | bit | Estado logico |

PK: `id_tarea`.
FK: `id_cliente`, `id_categoria`, `id_tipo`.
Indices: `IX_tareas_estado`, `IX_tareas_cliente_categoria_tipo`, `IX_tareas_proxima_ejecucion`, `IX_tareas_tipo_tarea`, `IX_tareas_nombre`.
Observacion: se elimina `id_script_actual` de `tareas`; el script logico se resuelve desde `scripts.id_tarea`.

### scripts

Objetivo: representar el script logico asociado a una tarea/proceso, sin guardar versiones fisicas directamente.

| Campo | Tipo SQL Server | Descripcion |
| --- | --- | --- |
| id_script | int identity(1,1) | PK |
| id_tarea | int | FK tareas |
| nombre_script | nvarchar(200) | Nombre logico |
| descripcion | nvarchar(1000) null | Descripcion funcional |
| id_version_activa | int null | FK a `scripts_versiones.id_version` |
| fecha_creacion | datetime2(0) | Auditoria |
| fecha_actualizacion | datetime2(0) null | Auditoria |
| usuario_creacion | nvarchar(100) null | Auditoria |
| usuario_actualizacion | nvarchar(100) null | Auditoria |
| activo | bit | Estado logico |

PK: `id_script`.
FK: `id_tarea -> tareas.id_tarea`, `id_version_activa -> scripts_versiones.id_version`.
Indices: `UX_scripts_id_tarea`, `IX_scripts_version_activa`, `IX_scripts_activo`.
Observacion: `id_version_activa` fue aprobado como FK directa. Puede quedar `null` durante la creacion inicial antes de cargar la primera version; luego debe apuntar a una version activa.

### scripts_versiones

Objetivo: almacenar hasta 3 versiones disponibles por script logico con trazabilidad de carga, hash, rutas y estado.

| Campo | Tipo SQL Server | Descripcion |
| --- | --- | --- |
| id_version | int identity(1,1) | PK |
| id_script | int | FK scripts |
| numero_version | tinyint | 1, 2 o 3 |
| nombre_archivo | nvarchar(255) | Archivo `.py` seguro |
| ruta_fisica | nvarchar(500) | Ruta resuelta en ambiente |
| ruta_relativa | nvarchar(500) | Ruta desde `RUTA_BASE_SCRIPTS` |
| hash_archivo | varchar(128) | Hash del contenido |
| estado_version | varchar(30) | ACTIVA, DISPONIBLE, REEMPLAZADA, INACTIVA |
| es_activa | bit | Marca rapida de version activa |
| usuario_carga | nvarchar(100) | Usuario que cargo/reemplazo |
| fecha_carga | datetime2(0) | Fecha de carga/reemplazo |
| observacion | nvarchar(1000) null | Motivo o comentario |
| fecha_creacion | datetime2(0) | Auditoria |
| fecha_actualizacion | datetime2(0) null | Auditoria |

PK: `id_version`.
FK: `id_script -> scripts.id_script`.
Indices recomendados:

* `UX_scripts_versiones_script_numero`: unico por `id_script, numero_version`.
* `UX_scripts_versiones_script_activa_filtrado`: unico filtrado por `id_script` donde `es_activa = 1`.
* `IX_scripts_versiones_script_estado`: busqueda por script y estado.
* `IX_scripts_versiones_hash`: trazabilidad por hash.

Observaciones:

* La ruta relativa debe seguir `CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/vN/NOMBRE_SCRIPT.py`.
* `ruta_fisica` se deriva de `RUTA_BASE_SCRIPTS` y no debe quemarse en codigo.
* Una version reemplazada no debe borrarse sin auditoria; puede cambiar a `REEMPLAZADA` y actualizar ruta/hash segun estrategia aprobada.

### programaciones

Objetivo: guardar reglas de agenda para tareas programadas o manuales.

Campos: `id_programacion int identity`, `id_tarea int`, `tipo_programacion varchar(30)`, `hora_inicio time(0) null`, `hora_termino time(0) null`, `hora_ejecucion time(0) null`, `intervalo_minutos int null`, `dias_semana varchar(50) null`, `dia_mes tinyint null`, `fechas_especificas nvarchar(max) null`, `configuracion_json nvarchar(max) null`, `zona_horaria nvarchar(80)`, `fecha_inicio_vigencia date null`, `fecha_fin_vigencia date null`, campos estandar.
PK: `id_programacion`.
FK: `id_tarea -> tareas.id_tarea`.
Indices: `IX_programaciones_tarea_activo`, `IX_programaciones_tipo`.

### ejecuciones

Objetivo: registrar cada intento de ejecucion manual o automatica, indicando exactamente la version ejecutada.

| Campo | Tipo SQL Server | Descripcion |
| --- | --- | --- |
| id_ejecucion | bigint identity(1,1) | PK |
| id_tarea | int | FK tareas |
| id_script | int | FK script logico ejecutado |
| id_version | int | FK version exacta ejecutada |
| origen_ejecucion | varchar(20) | MANUAL o AUTOMATICA |
| estado_ejecucion | varchar(30) | Estado |
| fecha_hora_inicio | datetime2(0) | Inicio |
| fecha_hora_termino | datetime2(0) null | Termino |
| duracion_segundos | int null | Duracion |
| codigo_salida | int null | Codigo del proceso |
| mensaje_error | nvarchar(max) null | Error resumido |
| usuario_ejecucion | nvarchar(100) null | Usuario o scheduler |
| pid_proceso | int null | Proceso local si aplica |
| fecha_creacion | datetime2(0) | Auditoria |

PK: `id_ejecucion`.
FK: `id_tarea -> tareas.id_tarea`, `id_script -> scripts.id_script`, `id_version -> scripts_versiones.id_version`.
Indices: `IX_ejecuciones_tarea_fecha`, `IX_ejecuciones_script_version`, `IX_ejecuciones_estado`, `IX_ejecuciones_inicio`.
Observacion: el servicio debe validar que `id_version` pertenezca al `id_script` informado.

### logs_tareas

Objetivo: vincular ejecuciones con logs fisicos y metadatos.

Campos: `id_log bigint identity`, `id_tarea int`, `id_ejecucion bigint`, `nombre_tarea nvarchar(200)`, `nombre_script nvarchar(255)`, `ruta_fisica_log nvarchar(500)`, `ruta_relativa_log nvarchar(500)`, `fecha_hora_inicio datetime2(0)`, `fecha_hora_termino datetime2(0) null`, `duracion_segundos int null`, `estado_final varchar(30)`, `codigo_salida int null`, `mensaje_error nvarchar(max) null`, `usuario_ejecucion nvarchar(100) null`, `fecha_creacion datetime2(0)`.
PK: `id_log`.
FK: `id_tarea -> tareas.id_tarea`, `id_ejecucion -> ejecuciones.id_ejecucion`.
Indices: `IX_logs_tareas_tarea_fecha`, `IX_logs_tareas_ejecucion`, `IX_logs_tareas_estado`.
Observacion: no duplica `id_version`; se obtiene desde `ejecuciones`.

### logs_sistema

Objetivo: registrar eventos internos de seguridad, sistema y operacion.

Campos: `id bigint identity`, `usuario nvarchar(100) null`, `accion nvarchar(100)`, `modulo nvarchar(100)`, `descripcion nvarchar(max)`, `valor_anterior nvarchar(max) null`, `valor_nuevo nvarchar(max) null`, `ip varchar(45) null`, `user_agent nvarchar(500) null`, `fecha_hora datetime2(0)`, `nivel varchar(20)`, `fecha_creacion datetime2(0)`.
PK: `id`.
Indices: `IX_logs_sistema_fecha`, `IX_logs_sistema_usuario`, `IX_logs_sistema_modulo_nivel`.

### auditoria_cambios

Objetivo: registrar cambios de datos importantes con trazabilidad antes/despues.

Campos: `id_auditoria bigint identity`, `tabla_afectada nvarchar(100)`, `id_registro nvarchar(100)`, `accion nvarchar(50)`, `valor_anterior nvarchar(max) null`, `valor_nuevo nvarchar(max) null`, `usuario nvarchar(100)`, `ip varchar(45) null`, `user_agent nvarchar(500) null`, `fecha_hora datetime2(0)`, `modulo nvarchar(100)`.
PK: `id_auditoria`.
Indices: `IX_auditoria_tabla_registro`, `IX_auditoria_usuario_fecha`, `IX_auditoria_fecha`.
Observacion: debe registrar cargas, activaciones, reemplazos e inactivaciones de versiones.

### configuracion_sistema

Objetivo: guardar parametros no sensibles modificables desde UI futura.

Campos: `id_configuracion int identity`, `clave nvarchar(120)`, `valor nvarchar(max)`, `tipo_dato varchar(30)`, `descripcion nvarchar(300) null`, `es_sensible bit`, campos estandar.
PK: `id_configuracion`.
Indices: `UX_configuracion_clave`.
Observacion: secretos reales siguen en `.env`.

## Estrategia para maximo 3 versiones

Decision aprobada para primera version: validar el maximo de 3 versiones en capa de servicio y reforzar en base con constraints e indice unico filtrado.

### Validacion en servicio

Ventajas:

* Mensajes claros al usuario antes de tocar archivos.
* Permite flujo guiado: si hay 3 versiones, pedir seleccion de version a reemplazar.
* Mantiene el control junto con validaciones de extension, ruta, hash y auditoria.

Desventajas:

* Si otro proceso escribe directo a la base, podria saltarse la regla.

### Indices y constraints recomendados

* `CHECK(numero_version between 1 and 3)` limita los numeros permitidos.
* `UNIQUE(id_script, numero_version)` evita dos versiones con el mismo numero.
* Indice unico filtrado `WHERE es_activa = 1` garantiza una sola version activa.

### Trigger o procedimiento almacenado

Uso futuro aprobado si se requiere blindaje en base:

* Trigger `AFTER INSERT/UPDATE` puede impedir mas de 3 versiones activas/disponibles por `id_script`.
* Procedimiento almacenado `sp_cargar_version_script` centraliza la regla.

Decision aprobada: iniciar con servicio + constraints simples; trigger o procedimiento almacenado queda como mejora futura.

## Estructura fisica propuesta para scripts versionados

Decision aprobada: usar carpetas `v1`, `v2` y `v3`.

```text
scripts/CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/v1/NOMBRE_SCRIPT.py
scripts/CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/v2/NOMBRE_SCRIPT.py
scripts/CATEGORIA/TIPO/CLIENTE/TIPO_TAREA/NOMBRE_SCRIPT/v3/NOMBRE_SCRIPT.py
```

Ejemplo:

```text
scripts/AUDIOS/VENTAS/BECS/PROGRAMADAS/SCRIPT1/v1/SCRIPT1.py
scripts/AUDIOS/VENTAS/BECS/PROGRAMADAS/SCRIPT1/v2/SCRIPT1.py
scripts/AUDIOS/VENTAS/BECS/PROGRAMADAS/SCRIPT1/v3/SCRIPT1.py
```

## Scripts SQL sugeridos, no ejecutados

Estos fragmentos son propuesta para discusion; no deben ejecutarse hasta aprobar modelo y estrategia de migraciones.

```sql
-- PROPUESTA NO EJECUTADA
-- Una sola version activa por script:
-- CREATE UNIQUE INDEX UX_scripts_versiones_script_activa
-- ON scripts_versiones(id_script)
-- WHERE es_activa = 1;

-- Numeros permitidos:
-- ALTER TABLE scripts_versiones
-- ADD CONSTRAINT CK_scripts_versiones_numero
-- CHECK (numero_version between 1 and 3);

-- Estados permitidos:
-- ALTER TABLE scripts_versiones
-- ADD CONSTRAINT CK_scripts_versiones_estado
-- CHECK (estado_version in ('ACTIVA','DISPONIBLE','REEMPLAZADA','INACTIVA'));
```

## Decisiones aprobadas antes de Fase 3B

* Se aprueba mantener `scripts` como script logico y `scripts_versiones` como tabla fisica de versiones.
* Se aprueba mantener `scripts.id_version_activa`.
* Una version `REEMPLAZADA` no cuenta dentro del maximo de 3 versiones disponibles.
* En primera version, el maximo de 3 se controla en capa de servicio.
* En base de datos se refuerza con `CHECK(numero_version between 1 and 3)`, `UNIQUE(id_script, numero_version)` e indice unico filtrado para una sola version activa.
* Trigger o procedimiento almacenado queda como mejora futura.
* Se aprueba estructura fisica con carpetas `v1`, `v2` y `v3`.

## Decisiones pendientes antes de implementar

* Confirmar estrategia exacta de reemplazo fisico: sobrescribir carpeta `vN` con auditoria previa o preservar copia historica adicional antes de reemplazar.
* Ejecutar scripts manualmente en SQL Server Management Studio cuando se apruebe la aplicacion fisica del modelo.
* Fase posterior: crear conexion Flask-SQL Server y repositorios, sin quemar credenciales.
