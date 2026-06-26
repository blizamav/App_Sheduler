/*
    Diagnostico Fase 11H - Desacople historico para papelera

    Script de solo lectura. Ajuste @id_tarea, @id_script o @id_version
    para revisar un caso concreto antes/despues de aplicar la migracion 017.
*/

USE APP_SCHEDULER_QA;
GO

DECLARE @id_tarea int = 1;
DECLARE @id_script int = NULL;
DECLARE @id_version int = NULL;

SELECT
    fk.name AS nombre_fk,
    OBJECT_SCHEMA_NAME(fk.parent_object_id) + '.' + OBJECT_NAME(fk.parent_object_id) AS tabla_origen,
    OBJECT_SCHEMA_NAME(fk.referenced_object_id) + '.' + OBJECT_NAME(fk.referenced_object_id) AS tabla_referenciada
FROM sys.foreign_keys fk
WHERE OBJECT_NAME(fk.parent_object_id) IN ('ejecuciones', 'logs_tareas', 'programaciones', 'scripts', 'scripts_versiones')
  AND OBJECT_NAME(fk.referenced_object_id) IN ('tareas', 'scripts', 'scripts_versiones', 'ejecuciones')
ORDER BY tabla_origen, nombre_fk;

SELECT
    OBJECT_SCHEMA_NAME(c.object_id) + '.' + OBJECT_NAME(c.object_id) AS tabla,
    c.name AS columna,
    CASE WHEN c.is_nullable = 1 THEN 'NULL' ELSE 'NOT NULL' END AS nulabilidad
FROM sys.columns c
WHERE c.object_id IN (OBJECT_ID(N'dbo.ejecuciones'), OBJECT_ID(N'dbo.logs_tareas'))
  AND c.name IN ('id_tarea', 'id_script', 'id_version')
ORDER BY tabla, columna;

SELECT 'tareas' AS origen, COUNT(1) AS total
FROM dbo.tareas
WHERE id_tarea = @id_tarea
UNION ALL
SELECT 'programaciones', COUNT(1)
FROM dbo.programaciones
WHERE id_tarea = @id_tarea
UNION ALL
SELECT 'scripts', COUNT(1)
FROM dbo.scripts
WHERE id_tarea = @id_tarea
UNION ALL
SELECT 'scripts_versiones', COUNT(1)
FROM dbo.scripts_versiones v
INNER JOIN dbo.scripts s ON s.id_script = v.id_script
WHERE s.id_tarea = @id_tarea
UNION ALL
SELECT 'ejecuciones', COUNT(1)
FROM dbo.ejecuciones
WHERE id_tarea = @id_tarea
UNION ALL
SELECT 'logs_tareas', COUNT(1)
FROM dbo.logs_tareas
WHERE id_tarea = @id_tarea;

IF OBJECT_ID(N'dbo.scheduler_eventos') IS NOT NULL
BEGIN
    EXEC sp_executesql
        N'SELECT ''scheduler_eventos'' AS origen, COUNT(1) AS total FROM dbo.scheduler_eventos WHERE id_tarea = @id_tarea',
        N'@id_tarea int',
        @id_tarea = @id_tarea;
END
ELSE
BEGIN
    SELECT 'scheduler_eventos' AS origen, 0 AS total;
END

SELECT
    COUNT(1) AS ejecuciones_tarea,
    SUM(CASE WHEN id_tarea_original IS NULL THEN 1 ELSE 0 END) AS sin_id_tarea_original,
    SUM(CASE WHEN nombre_tarea_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_nombre_tarea_snapshot,
    SUM(CASE WHEN cliente_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_cliente_snapshot,
    SUM(CASE WHEN categoria_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_categoria_snapshot,
    SUM(CASE WHEN tipo_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_tipo_snapshot,
    SUM(CASE WHEN nombre_script_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_nombre_script_snapshot,
    SUM(CASE WHEN nombre_archivo_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_nombre_archivo_snapshot,
    SUM(CASE WHEN version_script_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_version_script_snapshot
FROM dbo.ejecuciones
WHERE id_tarea = @id_tarea;

SELECT
    COUNT(1) AS logs_tarea,
    SUM(CASE WHEN nombre_tarea IS NULL THEN 1 ELSE 0 END) AS sin_nombre_tarea,
    SUM(CASE WHEN nombre_script IS NULL THEN 1 ELSE 0 END) AS sin_nombre_script,
    SUM(CASE WHEN nombre_archivo_log IS NULL THEN 1 ELSE 0 END) AS sin_nombre_archivo_log,
    SUM(CASE WHEN ruta_relativa_log IS NULL THEN 1 ELSE 0 END) AS sin_ruta_relativa_log
FROM dbo.logs_tareas
WHERE id_tarea = @id_tarea;

SELECT
    COUNT(1) AS ejecuciones_script,
    SUM(CASE WHEN nombre_script_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_nombre_script_snapshot,
    SUM(CASE WHEN nombre_archivo_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_nombre_archivo_snapshot,
    SUM(CASE WHEN version_script_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_version_script_snapshot
FROM dbo.ejecuciones
WHERE @id_script IS NOT NULL
  AND id_script = @id_script;

SELECT
    COUNT(1) AS ejecuciones_version,
    SUM(CASE WHEN nombre_script_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_nombre_script_snapshot,
    SUM(CASE WHEN nombre_archivo_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_nombre_archivo_snapshot,
    SUM(CASE WHEN version_script_snapshot IS NULL THEN 1 ELSE 0 END) AS sin_version_script_snapshot
FROM dbo.ejecuciones
WHERE @id_version IS NOT NULL
  AND id_version = @id_version;
