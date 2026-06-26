/*
Release SQL limpio - APP Scheduler
Script: 099_validacion_instalacion.sql
Objetivo: validar instalacion limpia con consultas de solo lectura.
No modifica datos.
*/

USE APP_SCHEDULER_TEST_INSTALL;
GO

SELECT
    N'VALIDACION_BASE' AS seccion,
    DB_NAME() AS base_actual,
    CASE WHEN DB_NAME() = N'APP_SCHEDULER_TEST_INSTALL' THEN N'OK' ELSE N'REVISAR_BASE_DESTINO' END AS resultado;
GO

SELECT
    N'VALIDACION_TABLAS' AS seccion,
    v.nombre_tabla,
    CASE WHEN t.object_id IS NULL THEN 0 ELSE 1 END AS existe
FROM (VALUES
    (N'cat_estados_tarea'),
    (N'cat_estados_ejecucion'),
    (N'cat_tipos_programacion'),
    (N'cat_niveles_log'),
    (N'cat_tipos_tarea'),
    (N'cat_estados_version_script'),
    (N'usuarios'),
    (N'roles'),
    (N'permisos'),
    (N'usuarios_roles'),
    (N'roles_permisos'),
    (N'clientes'),
    (N'categorias'),
    (N'tipos'),
    (N'tareas'),
    (N'programaciones'),
    (N'scripts'),
    (N'scripts_versiones'),
    (N'configuracion_sistema'),
    (N'ejecuciones'),
    (N'logs_tareas'),
    (N'logs_sistema'),
    (N'auditoria_cambios'),
    (N'configuracion_scheduler'),
    (N'scheduler_worker_heartbeat'),
    (N'scheduler_eventos'),
    (N'feriados'),
    (N'reglas_feriados_irrenunciables')
) AS v(nombre_tabla)
LEFT JOIN sys.tables t
    ON t.name = v.nombre_tabla
   AND t.schema_id = SCHEMA_ID(N'dbo')
ORDER BY v.nombre_tabla;
GO

SELECT N'VALIDACION_ROLES' AS seccion, codigo_rol, nombre_rol, activo
FROM dbo.roles
ORDER BY codigo_rol;
GO

SELECT
    N'VALIDACION_ROLES_BASE' AS seccion,
    v.codigo_rol,
    CASE WHEN r.id_rol IS NULL THEN 1 ELSE 0 END AS faltante
FROM (VALUES
    (N'SUPER_ADMIN'),
    (N'ADMIN'),
    (N'TI'),
    (N'TERCERO')
) AS v(codigo_rol)
LEFT JOIN dbo.roles r
    ON r.codigo_rol = v.codigo_rol
   AND r.activo = 1
ORDER BY v.codigo_rol;
GO

SELECT
    N'VALIDACION_ROLES_FALTANTES' AS seccion,
    COUNT(*) AS roles_faltantes
FROM (VALUES
    (N'SUPER_ADMIN'),
    (N'ADMIN'),
    (N'TI'),
    (N'TERCERO')
) AS v(codigo_rol)
LEFT JOIN dbo.roles r
    ON r.codigo_rol = v.codigo_rol
   AND r.activo = 1
WHERE r.id_rol IS NULL;
GO

SELECT
    N'VALIDACION_ROLES_NO_ESPERADOS' AS seccion,
    r.codigo_rol,
    r.nombre_rol,
    r.activo
FROM dbo.roles r
WHERE r.codigo_rol NOT IN (N'SUPER_ADMIN', N'ADMIN', N'TI', N'TERCERO')
ORDER BY r.codigo_rol;
GO

SELECT
    N'VALIDACION_ROL_OPERADOR_NO_EXISTE' AS seccion,
    COUNT(*) AS total_operador
FROM dbo.roles
WHERE codigo_rol = N'OPERADOR';
GO

SELECT
    N'VALIDACION_ROLES_CONTEO' AS seccion,
    COUNT(*) AS total_roles,
    SUM(CASE WHEN codigo_rol IS NULL OR LTRIM(RTRIM(codigo_rol)) = N'' THEN 1 ELSE 0 END) AS roles_codigo_nulo,
    SUM(CASE WHEN nombre_rol IS NULL OR LTRIM(RTRIM(nombre_rol)) = N'' THEN 1 ELSE 0 END) AS roles_nombre_nulo
FROM dbo.roles;
GO

SELECT
    N'VALIDACION_PERMISOS' AS seccion,
    COUNT(*) AS total_permisos,
    SUM(CASE WHEN codigo_permiso IS NULL OR LTRIM(RTRIM(codigo_permiso)) = N'' THEN 1 ELSE 0 END) AS permisos_codigo_nulo,
    SUM(CASE WHEN modulo IS NULL OR LTRIM(RTRIM(modulo)) = N'' THEN 1 ELSE 0 END) AS permisos_modulo_nulo,
    SUM(CASE WHEN accion IS NULL OR LTRIM(RTRIM(accion)) = N'' THEN 1 ELSE 0 END) AS permisos_accion_nulo
FROM dbo.permisos;
GO

SELECT
    N'VALIDACION_ROLES_PERMISOS' AS seccion,
    r.codigo_rol,
    COUNT(rp.id_permiso) AS total_permisos_asignados
FROM dbo.roles r
LEFT JOIN dbo.roles_permisos rp
    ON rp.id_rol = r.id_rol
   AND rp.activo = 1
GROUP BY r.codigo_rol
ORDER BY r.codigo_rol;
GO

SELECT
    N'VALIDACION_ROLES_PERMISOS_ESPERADOS' AS seccion,
    v.codigo_rol,
    COUNT(rp.id_permiso) AS permisos_actuales,
    v.permisos_esperados,
    COUNT(rp.id_permiso) - v.permisos_esperados AS diferencia
FROM (VALUES
    (N'SUPER_ADMIN', 39),
    (N'ADMIN', 37),
    (N'TI', 31),
    (N'TERCERO', 7)
) AS v(codigo_rol, permisos_esperados)
LEFT JOIN dbo.roles r
    ON r.codigo_rol = v.codigo_rol
   AND r.activo = 1
LEFT JOIN dbo.roles_permisos rp
    ON rp.id_rol = r.id_rol
   AND rp.activo = 1
GROUP BY v.codigo_rol, v.permisos_esperados
ORDER BY v.codigo_rol;
GO

SELECT N'VALIDACION_CATALOGOS' AS seccion, N'cat_estados_tarea' AS catalogo, COUNT(*) AS total, SUM(CASE WHEN nombre IS NULL OR LTRIM(RTRIM(nombre)) = N'' THEN 1 ELSE 0 END) AS nombres_nulos FROM dbo.cat_estados_tarea
UNION ALL SELECT N'VALIDACION_CATALOGOS', N'cat_estados_ejecucion', COUNT(*), SUM(CASE WHEN nombre IS NULL OR LTRIM(RTRIM(nombre)) = N'' THEN 1 ELSE 0 END) FROM dbo.cat_estados_ejecucion
UNION ALL SELECT N'VALIDACION_CATALOGOS', N'cat_tipos_programacion', COUNT(*), SUM(CASE WHEN nombre IS NULL OR LTRIM(RTRIM(nombre)) = N'' THEN 1 ELSE 0 END) FROM dbo.cat_tipos_programacion
UNION ALL SELECT N'VALIDACION_CATALOGOS', N'cat_niveles_log', COUNT(*), SUM(CASE WHEN nombre IS NULL OR LTRIM(RTRIM(nombre)) = N'' THEN 1 ELSE 0 END) FROM dbo.cat_niveles_log
UNION ALL SELECT N'VALIDACION_CATALOGOS', N'cat_tipos_tarea', COUNT(*), SUM(CASE WHEN nombre IS NULL OR LTRIM(RTRIM(nombre)) = N'' THEN 1 ELSE 0 END) FROM dbo.cat_tipos_tarea
UNION ALL SELECT N'VALIDACION_CATALOGOS', N'cat_estados_version_script', COUNT(*), SUM(CASE WHEN nombre IS NULL OR LTRIM(RTRIM(nombre)) = N'' THEN 1 ELSE 0 END) FROM dbo.cat_estados_version_script;
GO

SELECT N'VALIDACION_CATALOGOS_CODIGOS' AS seccion, N'estado_tarea_ACTIVA' AS elemento, COUNT(*) AS total FROM dbo.cat_estados_tarea WHERE codigo = N'ACTIVA'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'estado_tarea_INACTIVA', COUNT(*) FROM dbo.cat_estados_tarea WHERE codigo = N'INACTIVA'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'ejecucion_EN_EJECUCION', COUNT(*) FROM dbo.cat_estados_ejecucion WHERE codigo = N'EN_EJECUCION'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'ejecucion_EXITOSA', COUNT(*) FROM dbo.cat_estados_ejecucion WHERE codigo = N'EXITOSA'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'ejecucion_ERROR', COUNT(*) FROM dbo.cat_estados_ejecucion WHERE codigo = N'ERROR'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'ejecucion_DETENIDA_MANUALMENTE', COUNT(*) FROM dbo.cat_estados_ejecucion WHERE codigo = N'DETENIDA_MANUALMENTE'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'tipo_programacion_MANUAL', COUNT(*) FROM dbo.cat_tipos_programacion WHERE codigo = N'MANUAL'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'tipo_programacion_DIARIA', COUNT(*) FROM dbo.cat_tipos_programacion WHERE codigo = N'DIARIA'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'tipo_programacion_SEMANAL', COUNT(*) FROM dbo.cat_tipos_programacion WHERE codigo = N'SEMANAL'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'tipo_programacion_MENSUAL', COUNT(*) FROM dbo.cat_tipos_programacion WHERE codigo = N'MENSUAL'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'tipo_programacion_FECHA_ESPECIFICA', COUNT(*) FROM dbo.cat_tipos_programacion WHERE codigo = N'FECHA_ESPECIFICA'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'tipo_tarea_MANUAL', COUNT(*) FROM dbo.cat_tipos_tarea WHERE codigo = N'MANUAL'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'tipo_tarea_PROGRAMADA', COUNT(*) FROM dbo.cat_tipos_tarea WHERE codigo = N'PROGRAMADA'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'version_ACTIVA', COUNT(*) FROM dbo.cat_estados_version_script WHERE codigo = N'ACTIVA'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'version_DISPONIBLE', COUNT(*) FROM dbo.cat_estados_version_script WHERE codigo = N'DISPONIBLE'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'version_REEMPLAZADA', COUNT(*) FROM dbo.cat_estados_version_script WHERE codigo = N'REEMPLAZADA'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'version_INACTIVA', COUNT(*) FROM dbo.cat_estados_version_script WHERE codigo = N'INACTIVA'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'nivel_INFO', COUNT(*) FROM dbo.cat_niveles_log WHERE codigo = N'INFO'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'nivel_WARNING', COUNT(*) FROM dbo.cat_niveles_log WHERE codigo = N'WARNING'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'nivel_ERROR', COUNT(*) FROM dbo.cat_niveles_log WHERE codigo = N'ERROR'
UNION ALL SELECT N'VALIDACION_CATALOGOS_CODIGOS', N'nivel_CRITICAL', COUNT(*) FROM dbo.cat_niveles_log WHERE codigo = N'CRITICAL';
GO

SELECT
    N'VALIDACION_CONFIGURACION' AS seccion,
    COUNT(*) AS configuraciones_scheduler_activas,
    SUM(CASE WHEN scheduler_activo = 0 THEN 1 ELSE 0 END) AS scheduler_apagado,
    SUM(CASE WHEN permitir_ejecucion_automatica = 0 THEN 1 ELSE 0 END) AS automatica_deshabilitada,
    SUM(CASE WHEN intervalo_revision_segundos = 60 THEN 1 ELSE 0 END) AS intervalo_60,
    SUM(CASE WHEN max_ejecuciones_concurrentes = 3 THEN 1 ELSE 0 END) AS max_concurrentes_3
FROM dbo.configuracion_scheduler
WHERE activo = 1;
GO

SELECT
    N'VALIDACION_CONFIGURACION_SISTEMA' AS seccion,
    clave,
    valor,
    tipo_dato,
    es_sensible,
    activo
FROM dbo.configuracion_sistema
ORDER BY clave;
GO

SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS' AS seccion, N'usuarios' AS tabla, COUNT(*) AS total FROM dbo.usuarios
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'clientes', COUNT(*) FROM dbo.clientes
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'categorias', COUNT(*) FROM dbo.categorias
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'tipos', COUNT(*) FROM dbo.tipos
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'tareas', COUNT(*) FROM dbo.tareas
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'programaciones', COUNT(*) FROM dbo.programaciones
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'scripts', COUNT(*) FROM dbo.scripts
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'scripts_versiones', COUNT(*) FROM dbo.scripts_versiones
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'ejecuciones', COUNT(*) FROM dbo.ejecuciones
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'logs_tareas', COUNT(*) FROM dbo.logs_tareas
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'logs_sistema', COUNT(*) FROM dbo.logs_sistema
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'auditoria_cambios', COUNT(*) FROM dbo.auditoria_cambios
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'scheduler_worker_heartbeat', COUNT(*) FROM dbo.scheduler_worker_heartbeat
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'scheduler_eventos', COUNT(*) FROM dbo.scheduler_eventos
UNION ALL SELECT N'VALIDACION_TABLAS_OPERATIVAS_VACIAS', N'feriados', COUNT(*) FROM dbo.feriados;
GO

SELECT
    N'VALIDACION_COLUMNAS_NOT_NULL' AS seccion,
    c.TABLE_NAME AS tabla,
    c.COLUMN_NAME AS columna,
    c.DATA_TYPE AS tipo_dato,
    CASE WHEN dc.name IS NULL THEN 0 ELSE 1 END AS tiene_default
FROM INFORMATION_SCHEMA.COLUMNS c
LEFT JOIN sys.columns sc
    ON sc.object_id = OBJECT_ID(QUOTENAME(c.TABLE_SCHEMA) + N'.' + QUOTENAME(c.TABLE_NAME))
   AND sc.name = c.COLUMN_NAME
LEFT JOIN sys.default_constraints dc
    ON dc.parent_object_id = sc.object_id
   AND dc.parent_column_id = sc.column_id
WHERE c.TABLE_SCHEMA = N'dbo'
  AND c.IS_NULLABLE = N'NO'
ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;
GO

SELECT
    N'VALIDACION_SEGURIDAD_RELEASE' AS seccion,
    N'configuracion_sistema_posibles_secretos' AS control,
    COUNT(*) AS total
FROM dbo.configuracion_sistema
WHERE clave LIKE N'%PASSWORD%'
   OR clave LIKE N'%SECRET%'
   OR clave LIKE N'%TOKEN%'
   OR valor LIKE N'%PASSWORD%'
   OR valor LIKE N'%SECRET%'
   OR valor LIKE N'%TOKEN%'
UNION ALL
SELECT
    N'VALIDACION_SEGURIDAD_RELEASE',
    N'configuracion_sistema_rutas_locales',
    COUNT(*)
FROM dbo.configuracion_sistema
WHERE valor LIKE N'%' + N'C:' + NCHAR(92) + N'Users' + N'%'
   OR valor LIKE N'%' + NCHAR(92) + N'%'
   OR valor LIKE N'%/home/%';
GO

SELECT
    N'VALIDACION_INDICES_CONSTRAINTS' AS seccion,
    i.name AS indice_critico,
    OBJECT_NAME(i.object_id) AS tabla,
    i.is_unique,
    i.has_filter,
    i.filter_definition
FROM sys.indexes i
WHERE i.name IN (
    N'UX_scripts_versiones_script_numero',
    N'UX_scripts_versiones_script_activa',
    N'UX_configuracion_scheduler_activa',
    N'UX_feriados_fecha_pais_activo',
    N'UX_reglas_feriados_irrenunciables_pais_mes_dia_activo',
    N'UX_ejecuciones_clave_programacion_automatica',
    N'UX_scheduler_worker_heartbeat_nombre_activo',
    N'IX_auditoria_cambios_fecha_evento',
    N'IX_auditoria_cambios_usuario',
    N'IX_auditoria_cambios_entidad'
)
ORDER BY i.name;
GO

SELECT
    N'VALIDACION_FK' AS seccion,
    fk.name AS clave_foranea,
    OBJECT_NAME(fk.parent_object_id) AS tabla_origen,
    OBJECT_NAME(fk.referenced_object_id) AS tabla_referenciada
FROM sys.foreign_keys fk
WHERE fk.name LIKE N'FK_%'
ORDER BY tabla_origen, clave_foranea;
GO

SELECT
    N'VALIDACION_CHECKS' AS seccion,
    cc.name AS check_constraint,
    OBJECT_NAME(cc.parent_object_id) AS tabla,
    cc.definition
FROM sys.check_constraints cc
ORDER BY tabla, check_constraint;
GO
