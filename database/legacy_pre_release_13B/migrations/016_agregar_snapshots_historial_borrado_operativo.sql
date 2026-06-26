/*
Fase 11F - APP Scheduler
Script: 016_agregar_snapshots_historial_borrado_operativo.sql
Objetivo: permitir borrado operativo seguro conservando historial mediante snapshots.
Nota: ejecutar manualmente en SSMS. No borra ejecuciones, logs, eventos ni auditoria.
*/

USE APP_SCHEDULER_QA;
GO

DECLARE @sql nvarchar(max);

/* Campos de control para retiro operativo. */
IF COL_LENGTH('dbo.tareas', 'eliminado_operativo') IS NULL
BEGIN
    ALTER TABLE dbo.tareas ADD
        eliminado_operativo bit NOT NULL CONSTRAINT DF_tareas_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL;
END;
GO

IF COL_LENGTH('dbo.scripts', 'eliminado_operativo') IS NULL
BEGIN
    ALTER TABLE dbo.scripts ADD
        eliminado_operativo bit NOT NULL CONSTRAINT DF_scripts_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL;
END;
GO

IF COL_LENGTH('dbo.scripts_versiones', 'eliminado_operativo') IS NULL
BEGIN
    ALTER TABLE dbo.scripts_versiones ADD
        eliminado_operativo bit NOT NULL CONSTRAINT DF_scripts_versiones_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL;
END;
GO

IF COL_LENGTH('dbo.usuarios', 'eliminado_operativo') IS NULL
BEGIN
    ALTER TABLE dbo.usuarios ADD
        eliminado_operativo bit NOT NULL CONSTRAINT DF_usuarios_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL;
END;
GO

IF COL_LENGTH('dbo.clientes', 'eliminado_operativo') IS NULL
BEGIN
    ALTER TABLE dbo.clientes ADD
        eliminado_operativo bit NOT NULL CONSTRAINT DF_clientes_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL;
END;
GO

IF COL_LENGTH('dbo.categorias', 'eliminado_operativo') IS NULL
BEGIN
    ALTER TABLE dbo.categorias ADD
        eliminado_operativo bit NOT NULL CONSTRAINT DF_categorias_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL;
END;
GO

IF COL_LENGTH('dbo.tipos', 'eliminado_operativo') IS NULL
BEGIN
    ALTER TABLE dbo.tipos ADD
        eliminado_operativo bit NOT NULL CONSTRAINT DF_tipos_eliminado_operativo DEFAULT 0,
        fecha_eliminado_operativo datetime2(0) NULL,
        usuario_eliminado_operativo nvarchar(100) NULL,
        motivo_eliminado_operativo nvarchar(500) NULL;
END;
GO

/* Snapshots historicos de ejecuciones. */
IF COL_LENGTH('dbo.ejecuciones', 'id_tarea_original') IS NULL
    ALTER TABLE dbo.ejecuciones ADD id_tarea_original int NULL;
GO
IF COL_LENGTH('dbo.ejecuciones', 'nombre_tarea_snapshot') IS NULL
    ALTER TABLE dbo.ejecuciones ADD nombre_tarea_snapshot nvarchar(200) NULL;
GO
IF COL_LENGTH('dbo.ejecuciones', 'cliente_snapshot') IS NULL
    ALTER TABLE dbo.ejecuciones ADD cliente_snapshot nvarchar(200) NULL;
GO
IF COL_LENGTH('dbo.ejecuciones', 'categoria_snapshot') IS NULL
    ALTER TABLE dbo.ejecuciones ADD categoria_snapshot nvarchar(200) NULL;
GO
IF COL_LENGTH('dbo.ejecuciones', 'tipo_snapshot') IS NULL
    ALTER TABLE dbo.ejecuciones ADD tipo_snapshot nvarchar(200) NULL;
GO
IF COL_LENGTH('dbo.ejecuciones', 'nombre_script_snapshot') IS NULL
    ALTER TABLE dbo.ejecuciones ADD nombre_script_snapshot nvarchar(200) NULL;
GO
IF COL_LENGTH('dbo.ejecuciones', 'nombre_archivo_snapshot') IS NULL
    ALTER TABLE dbo.ejecuciones ADD nombre_archivo_snapshot nvarchar(255) NULL;
GO
IF COL_LENGTH('dbo.ejecuciones', 'version_script_snapshot') IS NULL
    ALTER TABLE dbo.ejecuciones ADD version_script_snapshot nvarchar(50) NULL;
GO
IF COL_LENGTH('dbo.ejecuciones', 'usuario_ejecucion_snapshot') IS NULL
    ALTER TABLE dbo.ejecuciones ADD usuario_ejecucion_snapshot nvarchar(100) NULL;
GO

UPDATE e
SET id_tarea_original = COALESCE(e.id_tarea_original, e.id_tarea),
    nombre_tarea_snapshot = COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea),
    cliente_snapshot = COALESCE(e.cliente_snapshot, c.nombre_cliente),
    categoria_snapshot = COALESCE(e.categoria_snapshot, ca.nombre_categoria),
    tipo_snapshot = COALESCE(e.tipo_snapshot, ti.nombre_tipo),
    nombre_script_snapshot = COALESCE(e.nombre_script_snapshot, s.nombre_script),
    nombre_archivo_snapshot = COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo),
    version_script_snapshot = COALESCE(e.version_script_snapshot, CONVERT(varchar(10), v.numero_version)),
    usuario_ejecucion_snapshot = COALESCE(e.usuario_ejecucion_snapshot, e.usuario_ejecucion)
FROM dbo.ejecuciones e
LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
LEFT JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
LEFT JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
LEFT JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version;
GO

/* Snapshots historicos de eventos del programador. */
IF OBJECT_ID(N'dbo.scheduler_eventos', N'U') IS NOT NULL
BEGIN
    IF COL_LENGTH('dbo.scheduler_eventos', 'id_tarea_original') IS NULL
        ALTER TABLE dbo.scheduler_eventos ADD id_tarea_original int NULL;
    IF COL_LENGTH('dbo.scheduler_eventos', 'nombre_tarea_snapshot') IS NULL
        ALTER TABLE dbo.scheduler_eventos ADD nombre_tarea_snapshot nvarchar(200) NULL;
    IF COL_LENGTH('dbo.scheduler_eventos', 'cliente_snapshot') IS NULL
        ALTER TABLE dbo.scheduler_eventos ADD cliente_snapshot nvarchar(200) NULL;
    IF COL_LENGTH('dbo.scheduler_eventos', 'categoria_snapshot') IS NULL
        ALTER TABLE dbo.scheduler_eventos ADD categoria_snapshot nvarchar(200) NULL;
    IF COL_LENGTH('dbo.scheduler_eventos', 'tipo_snapshot') IS NULL
        ALTER TABLE dbo.scheduler_eventos ADD tipo_snapshot nvarchar(200) NULL;
END;
GO

IF OBJECT_ID(N'dbo.scheduler_eventos', N'U') IS NOT NULL
BEGIN
    UPDATE se
    SET id_tarea_original = COALESCE(se.id_tarea_original, se.id_tarea),
        nombre_tarea_snapshot = COALESCE(se.nombre_tarea_snapshot, se.nombre_tarea, t.nombre_tarea),
        cliente_snapshot = COALESCE(se.cliente_snapshot, c.nombre_cliente),
        categoria_snapshot = COALESCE(se.categoria_snapshot, ca.nombre_categoria),
        tipo_snapshot = COALESCE(se.tipo_snapshot, ti.nombre_tipo)
    FROM dbo.scheduler_eventos se
    LEFT JOIN dbo.tareas t ON t.id_tarea = se.id_tarea
    LEFT JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
    LEFT JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
    LEFT JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo;
END;
GO

/* Indices para vistas operativas. */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tareas_operativo' AND object_id = OBJECT_ID(N'dbo.tareas'))
    CREATE INDEX IX_tareas_operativo ON dbo.tareas(eliminado_operativo, activo, estado_tarea);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_operativo' AND object_id = OBJECT_ID(N'dbo.scripts'))
    CREATE INDEX IX_scripts_operativo ON dbo.scripts(eliminado_operativo, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_versiones_operativo' AND object_id = OBJECT_ID(N'dbo.scripts_versiones'))
    CREATE INDEX IX_scripts_versiones_operativo ON dbo.scripts_versiones(eliminado_operativo, estado_version, es_activa);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_usuarios_operativo' AND object_id = OBJECT_ID(N'dbo.usuarios'))
    CREATE INDEX IX_usuarios_operativo ON dbo.usuarios(eliminado_operativo, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_clientes_operativo' AND object_id = OBJECT_ID(N'dbo.clientes'))
    CREATE INDEX IX_clientes_operativo ON dbo.clientes(eliminado_operativo, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_categorias_operativo' AND object_id = OBJECT_ID(N'dbo.categorias'))
    CREATE INDEX IX_categorias_operativo ON dbo.categorias(eliminado_operativo, activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tipos_operativo' AND object_id = OBJECT_ID(N'dbo.tipos'))
    CREATE INDEX IX_tipos_operativo ON dbo.tipos(eliminado_operativo, activo);
GO
