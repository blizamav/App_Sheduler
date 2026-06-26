/*
Fase 4.3 - APP Scheduler
Script: 007_agregar_control_ejecucion_y_env_scripts.sql
Objetivo: agregar soporte de rutas .env por version de script y control de detencion manual.
Nota: script propuesto/versionado. Ejecutar manualmente en SSMS solo despues de aprobacion.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.cat_estados_ejecucion AS destino
USING (VALUES
    ('DETENIDA_MANUALMENTE', N'Detenida manualmente', N'Ejecucion detenida por un usuario autorizado.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'migration_007');
GO

IF COL_LENGTH('dbo.scripts_versiones', 'requiere_env') IS NULL
BEGIN
    ALTER TABLE dbo.scripts_versiones
    ADD requiere_env bit NOT NULL
        CONSTRAINT DF_scripts_versiones_requiere_env DEFAULT 0;
END;
GO

IF COL_LENGTH('dbo.scripts_versiones', 'ruta_env_fisica') IS NULL
BEGIN
    ALTER TABLE dbo.scripts_versiones
    ADD ruta_env_fisica nvarchar(500) NULL;
END;
GO

IF COL_LENGTH('dbo.scripts_versiones', 'ruta_env_relativa') IS NULL
BEGIN
    ALTER TABLE dbo.scripts_versiones
    ADD ruta_env_relativa nvarchar(500) NULL;
END;
GO

IF COL_LENGTH('dbo.ejecuciones', 'usuario_detencion') IS NULL
BEGIN
    ALTER TABLE dbo.ejecuciones
    ADD usuario_detencion nvarchar(100) NULL;
END;
GO

IF COL_LENGTH('dbo.ejecuciones', 'fecha_hora_detencion') IS NULL
BEGIN
    ALTER TABLE dbo.ejecuciones
    ADD fecha_hora_detencion datetime2(0) NULL;
END;
GO

IF COL_LENGTH('dbo.ejecuciones', 'motivo_detencion') IS NULL
BEGIN
    ALTER TABLE dbo.ejecuciones
    ADD motivo_detencion nvarchar(500) NULL;
END;
GO

IF COL_LENGTH('dbo.ejecuciones', 'fue_detencion_forzada') IS NULL
BEGIN
    ALTER TABLE dbo.ejecuciones
    ADD fue_detencion_forzada bit NOT NULL
        CONSTRAINT DF_ejecuciones_fue_detencion_forzada DEFAULT 0;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_scripts_versiones_requiere_env'
      AND object_id = OBJECT_ID('dbo.scripts_versiones')
)
BEGIN
    CREATE INDEX IX_scripts_versiones_requiere_env
    ON dbo.scripts_versiones(requiere_env);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_ejecuciones_detencion'
      AND object_id = OBJECT_ID('dbo.ejecuciones')
)
BEGIN
    CREATE INDEX IX_ejecuciones_detencion
    ON dbo.ejecuciones(fecha_hora_detencion, usuario_detencion)
    WHERE fecha_hora_detencion IS NOT NULL;
END;
GO
