/*
Fase 10A - APP Scheduler
Script: 012_crear_calendario_feriados.sql
Objetivo: crear calendario local de feriados usado por el scheduler.
Nota: ejecutar manualmente en SSMS. No conecta API externa.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.feriados', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.feriados (
        id_feriado int IDENTITY(1,1) NOT NULL,
        fecha date NOT NULL,
        nombre varchar(200) NOT NULL,
        tipo varchar(50) NULL,
        pais varchar(10) NOT NULL CONSTRAINT DF_feriados_pais DEFAULT 'CL',
        irrenunciable bit NOT NULL CONSTRAINT DF_feriados_irrenunciable DEFAULT 0,
        activo bit NOT NULL CONSTRAINT DF_feriados_activo DEFAULT 1,
        origen varchar(50) NOT NULL CONSTRAINT DF_feriados_origen DEFAULT 'MANUAL',
        observacion varchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_feriados_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        CONSTRAINT PK_feriados PRIMARY KEY (id_feriado),
        CONSTRAINT CK_feriados_pais CHECK (LEN(LTRIM(RTRIM(pais))) BETWEEN 1 AND 10),
        CONSTRAINT CK_feriados_origen CHECK (origen IN ('MANUAL','API','IMPORTACION'))
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_feriados_fecha_pais_activo'
      AND object_id = OBJECT_ID('dbo.feriados')
)
BEGIN
    CREATE UNIQUE INDEX UX_feriados_fecha_pais_activo
    ON dbo.feriados(fecha, pais)
    WHERE activo = 1;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_feriados_fecha'
      AND object_id = OBJECT_ID('dbo.feriados')
)
BEGIN
    CREATE INDEX IX_feriados_fecha
    ON dbo.feriados(fecha);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_feriados_pais'
      AND object_id = OBJECT_ID('dbo.feriados')
)
BEGIN
    CREATE INDEX IX_feriados_pais
    ON dbo.feriados(pais);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_feriados_activo'
      AND object_id = OBJECT_ID('dbo.feriados')
)
BEGIN
    CREATE INDEX IX_feriados_activo
    ON dbo.feriados(activo);
END;
GO
