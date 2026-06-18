/*
    Diagnostico Fase 11I - Validacion post desacople historico

    Script de solo lectura. Ajuste @id_ejecucion si necesita validar
    una ejecucion historica especifica.
*/

USE APP_SCHEDULER_QA;
GO

DECLARE @id_ejecucion bigint = 14;

SELECT
    COUNT(1) AS total_ejecuciones,
    SUM(CASE WHEN id_tarea IS NULL THEN 1 ELSE 0 END) AS con_id_tarea_null,
    SUM(CASE WHEN id_script IS NULL THEN 1 ELSE 0 END) AS con_id_script_null,
    SUM(CASE WHEN id_version IS NULL THEN 1 ELSE 0 END) AS con_id_version_null
FROM dbo.ejecuciones;

SELECT
    id_ejecucion,
    id_tarea,
    id_script,
    id_version,
    id_tarea_original,
    nombre_tarea_snapshot,
    cliente_snapshot,
    categoria_snapshot,
    tipo_snapshot,
    nombre_script_snapshot,
    nombre_archivo_snapshot,
    version_script_snapshot,
    usuario_ejecucion_snapshot,
    CASE
        WHEN nombre_tarea_snapshot IS NOT NULL
         AND cliente_snapshot IS NOT NULL
         AND categoria_snapshot IS NOT NULL
         AND tipo_snapshot IS NOT NULL
         AND nombre_script_snapshot IS NOT NULL
         AND nombre_archivo_snapshot IS NOT NULL
         AND version_script_snapshot IS NOT NULL
        THEN 'SNAPSHOT_COMPLETO'
        ELSE 'SNAPSHOT_INCOMPLETO'
    END AS estado_snapshot
FROM dbo.ejecuciones
WHERE id_tarea IS NULL
   OR id_script IS NULL
   OR id_version IS NULL
   OR id_ejecucion = @id_ejecucion
ORDER BY id_ejecucion DESC;

SELECT
    COUNT(1) AS logs_total,
    SUM(CASE WHEN id_tarea IS NULL THEN 1 ELSE 0 END) AS logs_con_id_tarea_null,
    SUM(CASE WHEN id_ejecucion IS NULL THEN 1 ELSE 0 END) AS logs_sin_ejecucion
FROM dbo.logs_tareas;

SELECT
    lt.id_log,
    lt.id_ejecucion,
    lt.id_tarea,
    lt.nombre_tarea,
    lt.nombre_script,
    lt.nombre_archivo_log,
    lt.ruta_relativa_log,
    lt.estado_final
FROM dbo.logs_tareas lt
WHERE lt.id_tarea IS NULL
   OR lt.id_ejecucion = @id_ejecucion
ORDER BY lt.id_log DESC;

SELECT
    e.id_ejecucion,
    COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, 'Tarea eliminada') AS nombre_tarea_visible,
    COALESCE(e.nombre_script_snapshot, s.nombre_script, 'Script eliminado') AS nombre_script_visible,
    COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo, 'Archivo historico') AS archivo_visible,
    COALESCE(e.version_script_snapshot, CONVERT(varchar(10), v.numero_version), 'historica') AS version_visible,
    COALESCE(e.usuario_ejecucion_snapshot, e.usuario_ejecucion, 'Usuario historico') AS usuario_visible,
    CASE WHEN e.id_tarea IS NULL OR t.id_tarea IS NULL THEN 1 ELSE 0 END AS tarea_maestra_eliminada,
    CASE WHEN e.id_script IS NULL OR s.id_script IS NULL THEN 1 ELSE 0 END AS script_maestro_eliminado,
    CASE WHEN e.id_version IS NULL OR v.id_version IS NULL THEN 1 ELSE 0 END AS version_maestra_eliminada
FROM dbo.ejecuciones e
LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
WHERE e.id_ejecucion = @id_ejecucion;

IF OBJECT_ID(N'dbo.scheduler_eventos') IS NOT NULL
BEGIN
    SELECT
        COUNT(1) AS eventos_total,
        SUM(CASE WHEN id_tarea IS NULL THEN 1 ELSE 0 END) AS eventos_con_id_tarea_null,
        SUM(CASE WHEN nombre_tarea_snapshot IS NULL THEN 1 ELSE 0 END) AS eventos_sin_nombre_snapshot
    FROM dbo.scheduler_eventos;

    SELECT TOP (100)
        id_evento,
        fecha_evento,
        id_tarea,
        COALESCE(nombre_tarea_snapshot, nombre_tarea, 'Tarea eliminada') AS nombre_tarea_visible,
        cliente_snapshot,
        categoria_snapshot,
        tipo_snapshot,
        tipo_evento,
        decision,
        motivo
    FROM dbo.scheduler_eventos
    WHERE id_tarea IS NULL
       OR nombre_tarea_snapshot IS NOT NULL
    ORDER BY fecha_evento DESC, id_evento DESC;
END

SELECT
    'tareas' AS entidad,
    COUNT(1) AS eliminados_operativos
FROM dbo.tareas
WHERE ISNULL(eliminado_operativo, 0) = 1
UNION ALL
SELECT 'scripts', COUNT(1)
FROM dbo.scripts
WHERE ISNULL(eliminado_operativo, 0) = 1
UNION ALL
SELECT 'scripts_versiones', COUNT(1)
FROM dbo.scripts_versiones
WHERE ISNULL(eliminado_operativo, 0) = 1;
