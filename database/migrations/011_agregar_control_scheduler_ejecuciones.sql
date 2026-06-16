/*
Fase 9B - APP Scheduler
Script: 011_agregar_control_scheduler_ejecuciones.sql
Objetivo: agregar control anti-duplicados y trazabilidad para ejecuciones automaticas.
Nota: ejecutar manualmente en SSMS. No modifica migraciones anteriores.
*/

USE APP_SCHEDULER_QA;
GO

IF COL_LENGTH('dbo.ejecuciones', 'origen_ejecucion') IS NULL
BEGIN
    ALTER TABLE dbo.ejecuciones
    ADD origen_ejecucion varchar(20) NULL;
END;
GO

IF COL_LENGTH('dbo.ejecuciones', 'fecha_programada') IS NULL
BEGIN
    ALTER TABLE dbo.ejecuciones
    ADD fecha_programada datetime2(0) NULL;
END;
GO

IF COL_LENGTH('dbo.ejecuciones', 'clave_programacion') IS NULL
BEGIN
    ALTER TABLE dbo.ejecuciones
    ADD clave_programacion varchar(200) NULL;
END;
GO

IF COL_LENGTH('dbo.ejecuciones', 'nombre_worker') IS NULL
BEGIN
    ALTER TABLE dbo.ejecuciones
    ADD nombre_worker varchar(100) NULL;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = 'CK_ejecuciones_origen_scheduler'
      AND parent_object_id = OBJECT_ID('dbo.ejecuciones')
)
BEGIN
    ALTER TABLE dbo.ejecuciones
    ADD CONSTRAINT CK_ejecuciones_origen_scheduler
    CHECK (origen_ejecucion IS NULL OR origen_ejecucion IN ('MANUAL','AUTOMATICA'));
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_ejecuciones_clave_programacion_automatica'
      AND object_id = OBJECT_ID('dbo.ejecuciones')
)
BEGIN
    CREATE UNIQUE INDEX UX_ejecuciones_clave_programacion_automatica
    ON dbo.ejecuciones(clave_programacion)
    WHERE origen_ejecucion = 'AUTOMATICA'
      AND clave_programacion IS NOT NULL;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_ejecuciones_origen_estado'
      AND object_id = OBJECT_ID('dbo.ejecuciones')
)
BEGIN
    CREATE INDEX IX_ejecuciones_origen_estado
    ON dbo.ejecuciones(origen_ejecucion, estado_ejecucion, fecha_hora_inicio);
END;
GO
