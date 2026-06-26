/*
Fase 6 - APP Scheduler
Script: 008_ajustar_tareas_y_programaciones_base.sql
Objetivo: ajustar tareas y programaciones para programacion base.
Nota: script versionado e idempotente. Ejecutar manualmente en SSMS despues de aprobar Fase 6.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.cat_tipos_programacion AS destino
USING (VALUES
    ('FECHA_ESPECIFICA', N'Fecha especifica', N'Ejecucion en una fecha especifica.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'migration_008');
GO

IF COL_LENGTH('dbo.tareas', 'observacion_tecnica') IS NULL
BEGIN
    ALTER TABLE dbo.tareas
    ADD observacion_tecnica nvarchar(1000) NULL;
END;
GO

IF COL_LENGTH('dbo.programaciones', 'modo_ejecucion_dia') IS NULL
BEGIN
    ALTER TABLE dbo.programaciones
    ADD modo_ejecucion_dia varchar(30) NULL;
END;
GO

IF COL_LENGTH('dbo.programaciones', 'fecha_especifica') IS NULL
BEGIN
    ALTER TABLE dbo.programaciones
    ADD fecha_especifica date NULL;
END;
GO

IF COL_LENGTH('dbo.programaciones', 'ejecutar_en_feriados') IS NULL
BEGIN
    ALTER TABLE dbo.programaciones
    ADD ejecutar_en_feriados bit NOT NULL
        CONSTRAINT DF_programaciones_ejecutar_en_feriados DEFAULT 0;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = 'CK_programaciones_modo_ejecucion_dia'
      AND parent_object_id = OBJECT_ID('dbo.programaciones')
)
BEGIN
    ALTER TABLE dbo.programaciones
    ADD CONSTRAINT CK_programaciones_modo_ejecucion_dia
    CHECK (modo_ejecucion_dia IS NULL OR modo_ejecucion_dia IN ('UNA_VEZ','INTERVALO'));
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_tareas_nombre_contexto'
      AND object_id = OBJECT_ID('dbo.tareas')
)
BEGIN
    CREATE INDEX IX_tareas_nombre_contexto
    ON dbo.tareas(nombre_tarea, id_cliente, id_categoria, id_tipo);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_programaciones_tipo_modo'
      AND object_id = OBJECT_ID('dbo.programaciones')
)
BEGIN
    CREATE INDEX IX_programaciones_tipo_modo
    ON dbo.programaciones(tipo_programacion, modo_ejecucion_dia, activo);
END;
GO
