/*
    Fase 11H - Desacople historico para papelera

    Objetivo:
    - Permitir eliminacion permanente real de filas operativas ya retiradas.
    - Conservar ejecuciones, logs de tareas, eventos del programador y snapshots.
    - Cortar solo FKs historicas que impiden borrar maestros operativos.

    Ejecucion manual en SQL Server Management Studio.
*/

USE APP_SCHEDULER_QA;
GO

IF COL_LENGTH('dbo.ejecuciones', 'nombre_tarea_snapshot') IS NULL
BEGIN
    RAISERROR('Debe ejecutar primero la migracion 016_agregar_snapshots_historial_borrado_operativo.sql.', 16, 1);
    RETURN;
END
GO

UPDATE e
SET id_tarea_original = COALESCE(e.id_tarea_original, e.id_tarea),
    nombre_tarea_snapshot = COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea),
    cliente_snapshot = COALESCE(e.cliente_snapshot, c.nombre_cliente),
    categoria_snapshot = COALESCE(e.categoria_snapshot, ca.nombre_categoria),
    tipo_snapshot = COALESCE(e.tipo_snapshot, ti.nombre_tipo),
    nombre_script_snapshot = COALESCE(e.nombre_script_snapshot, s.nombre_script),
    nombre_archivo_snapshot = COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo),
    version_script_snapshot = COALESCE(e.version_script_snapshot, CONVERT(nvarchar(20), v.numero_version)),
    usuario_ejecucion_snapshot = COALESCE(e.usuario_ejecucion_snapshot, e.usuario_ejecucion)
FROM dbo.ejecuciones e
LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
LEFT JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
LEFT JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
LEFT JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version;
GO

IF OBJECT_ID(N'dbo.scheduler_eventos') IS NOT NULL
   AND COL_LENGTH('dbo.scheduler_eventos', 'id_tarea_original') IS NOT NULL
BEGIN
    UPDATE se
    SET id_tarea_original = COALESCE(se.id_tarea_original, se.id_tarea),
        nombre_tarea_snapshot = COALESCE(se.nombre_tarea_snapshot, t.nombre_tarea),
        cliente_snapshot = COALESCE(se.cliente_snapshot, c.nombre_cliente),
        categoria_snapshot = COALESCE(se.categoria_snapshot, ca.nombre_categoria),
        tipo_snapshot = COALESCE(se.tipo_snapshot, ti.nombre_tipo)
    FROM dbo.scheduler_eventos se
    LEFT JOIN dbo.tareas t ON t.id_tarea = se.id_tarea
    LEFT JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
    LEFT JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
    LEFT JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo;
END
GO

IF EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE parent_object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'FK_ejecuciones_tareas'
)
BEGIN
    ALTER TABLE dbo.ejecuciones DROP CONSTRAINT FK_ejecuciones_tareas;
END
GO

IF EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE parent_object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'FK_ejecuciones_scripts'
)
BEGIN
    ALTER TABLE dbo.ejecuciones DROP CONSTRAINT FK_ejecuciones_scripts;
END
GO

IF EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE parent_object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'FK_ejecuciones_scripts_versiones'
)
BEGIN
    ALTER TABLE dbo.ejecuciones DROP CONSTRAINT FK_ejecuciones_scripts_versiones;
END
GO

IF EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE parent_object_id = OBJECT_ID(N'dbo.logs_tareas')
      AND name = N'FK_logs_tareas_tareas'
)
BEGIN
    ALTER TABLE dbo.logs_tareas DROP CONSTRAINT FK_logs_tareas_tareas;
END
GO

IF EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'IX_ejecuciones_tarea_fecha'
)
BEGIN
    DROP INDEX IX_ejecuciones_tarea_fecha ON dbo.ejecuciones;
END
GO

IF EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'IX_ejecuciones_script_version'
)
BEGIN
    DROP INDEX IX_ejecuciones_script_version ON dbo.ejecuciones;
END
GO

IF EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.logs_tareas')
      AND name = N'IX_logs_tareas_tarea_fecha'
)
BEGIN
    DROP INDEX IX_logs_tareas_tarea_fecha ON dbo.logs_tareas;
END
GO

IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'id_tarea'
      AND is_nullable = 0
)
BEGIN
    ALTER TABLE dbo.ejecuciones ALTER COLUMN id_tarea int NULL;
END
GO

IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'id_script'
      AND is_nullable = 0
)
BEGIN
    ALTER TABLE dbo.ejecuciones ALTER COLUMN id_script int NULL;
END
GO

IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'id_version'
      AND is_nullable = 0
)
BEGIN
    ALTER TABLE dbo.ejecuciones ALTER COLUMN id_version int NULL;
END
GO

IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.logs_tareas')
      AND name = N'id_tarea'
      AND is_nullable = 0
)
BEGIN
    ALTER TABLE dbo.logs_tareas ALTER COLUMN id_tarea int NULL;
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'IX_ejecuciones_tarea_fecha'
)
BEGIN
    CREATE INDEX IX_ejecuciones_tarea_fecha
    ON dbo.ejecuciones(id_tarea, fecha_hora_inicio DESC);
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.ejecuciones')
      AND name = N'IX_ejecuciones_script_version'
)
BEGIN
    CREATE INDEX IX_ejecuciones_script_version
    ON dbo.ejecuciones(id_script, id_version);
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.logs_tareas')
      AND name = N'IX_logs_tareas_tarea_fecha'
)
BEGIN
    CREATE INDEX IX_logs_tareas_tarea_fecha
    ON dbo.logs_tareas(id_tarea, fecha_creacion DESC);
END
GO
