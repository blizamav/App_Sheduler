/*
Diagnostico manual post Fase 11F - tareas, scripts y versiones.
Ejecutar manualmente en SSMS. No modifica datos.

El modelo vigente usa:
- scripts.activo
- scripts.eliminado_operativo
- scripts.id_version_activa
- scripts_versiones.estado_version
- scripts_versiones.es_activa
- scripts_versiones.eliminado_operativo
*/

SELECT
    t.id_tarea,
    t.nombre_tarea,
    t.activo AS tarea_activa,
    ISNULL(t.eliminado_operativo, 0) AS tarea_eliminada_operativo,
    s.id_script,
    s.nombre_script,
    s.activo AS script_activo,
    ISNULL(s.eliminado_operativo, 0) AS script_eliminado_operativo,
    s.id_version_activa,
    sv.id_version,
    sv.numero_version,
    sv.nombre_archivo,
    sv.estado_version,
    sv.es_activa AS version_es_activa,
    ISNULL(sv.eliminado_operativo, 0) AS version_eliminada_operativo,
    ejecuciones_en_curso = (
        SELECT COUNT(1)
        FROM dbo.ejecuciones e
        WHERE e.id_tarea = t.id_tarea
          AND e.estado_ejecucion = 'EN_EJECUCION'
    ),
    disponibilidad_calculada = CASE
        WHEN t.activo = 0 THEN 'No ejecutable: Tarea inactiva'
        WHEN ISNULL(t.eliminado_operativo, 0) = 1 THEN 'No ejecutable: Tarea borrada operativamente'
        WHEN (
            SELECT COUNT(1)
            FROM dbo.ejecuciones e
            WHERE e.id_tarea = t.id_tarea
              AND e.estado_ejecucion = 'EN_EJECUCION'
        ) > 0 THEN 'No ejecutable: Ejecucion en curso'
        WHEN s.id_script IS NULL THEN 'No ejecutable: Sin script asociado'
        WHEN ISNULL(s.eliminado_operativo, 0) = 1 THEN 'No ejecutable: Script borrado operativamente'
        WHEN s.activo = 0 THEN 'No ejecutable: Script inactivo'
        WHEN s.id_version_activa IS NULL OR sv.id_version IS NULL THEN 'No ejecutable: Sin version activa'
        WHEN ISNULL(sv.eliminado_operativo, 0) = 1 THEN 'No ejecutable: Version borrada operativamente'
        WHEN ISNULL(sv.es_activa, 0) = 0 OR sv.estado_version <> 'ACTIVA' THEN 'No ejecutable: Version no disponible'
        ELSE 'Ejecutable'
    END
FROM dbo.tareas t
LEFT JOIN dbo.scripts s
    ON s.id_tarea = t.id_tarea
LEFT JOIN dbo.scripts_versiones sv
    ON sv.id_version = s.id_version_activa
WHERE t.id_tarea IN (1, 2, 3)
ORDER BY t.id_tarea, s.id_script;

SELECT
    s.id_script,
    s.id_tarea,
    s.nombre_script,
    s.activo AS script_activo,
    ISNULL(s.eliminado_operativo, 0) AS script_eliminado_operativo,
    s.id_version_activa,
    sv.id_version,
    sv.numero_version,
    sv.nombre_archivo,
    sv.estado_version,
    sv.es_activa AS version_es_activa,
    ISNULL(sv.eliminado_operativo, 0) AS version_eliminada_operativo
FROM dbo.scripts s
LEFT JOIN dbo.scripts_versiones sv
    ON sv.id_version = s.id_version_activa
ORDER BY s.id_tarea, s.id_script, sv.numero_version;

SELECT
    sv.id_script,
    sv.id_version,
    sv.numero_version,
    sv.nombre_archivo,
    sv.estado_version,
    sv.es_activa AS version_es_activa,
    ISNULL(sv.eliminado_operativo, 0) AS version_eliminada_operativo
FROM dbo.scripts_versiones sv
ORDER BY sv.id_script, sv.numero_version;
