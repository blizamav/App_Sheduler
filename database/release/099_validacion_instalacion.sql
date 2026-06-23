/*
Release SQL limpio - APP Scheduler
Script: 099_validacion_instalacion.sql
Objetivo: validar instalacion limpia con consultas de solo lectura.
No modifica datos.
*/

USE APP_SCHEDULER_QA;
GO

SELECT
    DB_NAME() AS base_actual,
    COUNT(*) AS tablas_app_scheduler
FROM sys.tables
WHERE schema_id = SCHEMA_ID(N'dbo');
GO

SELECT N'roles' AS elemento, COUNT(*) AS total FROM dbo.roles
UNION ALL SELECT N'permisos', COUNT(*) FROM dbo.permisos
UNION ALL SELECT N'roles_permisos', COUNT(*) FROM dbo.roles_permisos
UNION ALL SELECT N'estados_tarea', COUNT(*) FROM dbo.cat_estados_tarea
UNION ALL SELECT N'estados_ejecucion', COUNT(*) FROM dbo.cat_estados_ejecucion
UNION ALL SELECT N'tipos_programacion', COUNT(*) FROM dbo.cat_tipos_programacion
UNION ALL SELECT N'estados_version_script', COUNT(*) FROM dbo.cat_estados_version_script
UNION ALL SELECT N'configuracion_scheduler_activa', COUNT(*) FROM dbo.configuracion_scheduler WHERE activo = 1
UNION ALL SELECT N'reglas_feriados_irrenunciables', COUNT(*) FROM dbo.reglas_feriados_irrenunciables WHERE activo = 1;
GO

SELECT N'tareas' AS tabla, COUNT(*) AS registros_iniciales FROM dbo.tareas
UNION ALL SELECT N'scripts', COUNT(*) FROM dbo.scripts
UNION ALL SELECT N'scripts_versiones', COUNT(*) FROM dbo.scripts_versiones
UNION ALL SELECT N'ejecuciones', COUNT(*) FROM dbo.ejecuciones
UNION ALL SELECT N'logs_tareas', COUNT(*) FROM dbo.logs_tareas
UNION ALL SELECT N'auditoria_cambios', COUNT(*) FROM dbo.auditoria_cambios;
GO

SELECT
    i.name AS indice_critico,
    OBJECT_NAME(i.object_id) AS tabla
FROM sys.indexes i
WHERE i.name IN (
    N'UX_scripts_versiones_script_numero',
    N'UX_scripts_versiones_script_activa',
    N'UX_configuracion_scheduler_activa',
    N'UX_feriados_fecha_pais_activo',
    N'UX_reglas_feriados_irrenunciables_pais_mes_dia_activo',
    N'UX_ejecuciones_clave_programacion_automatica',
    N'UX_scheduler_worker_heartbeat_nombre_activo'
)
ORDER BY i.name;
GO

SELECT
    fk.name AS clave_foranea,
    OBJECT_NAME(fk.parent_object_id) AS tabla_origen,
    OBJECT_NAME(fk.referenced_object_id) AS tabla_referenciada
FROM sys.foreign_keys fk
WHERE fk.name LIKE N'FK_%'
ORDER BY tabla_origen, clave_foranea;
GO

SELECT
    cc.name AS check_constraint,
    OBJECT_NAME(cc.parent_object_id) AS tabla
FROM sys.check_constraints cc
ORDER BY tabla, check_constraint;
GO
