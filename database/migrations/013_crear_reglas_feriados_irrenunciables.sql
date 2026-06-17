/*
Fase 10B - APP Scheduler
Script: 013_crear_reglas_feriados_irrenunciables.sql
Objetivo: crear reglas locales de feriados irrenunciables y permitir origen API_NAGER.
Nota: ejecutar manualmente en SSMS. No modifica datos existentes ni conecta API externa.
*/

USE APP_SCHEDULER_QA;
GO

IF EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = 'CK_feriados_origen'
      AND parent_object_id = OBJECT_ID('dbo.feriados')
)
BEGIN
    ALTER TABLE dbo.feriados DROP CONSTRAINT CK_feriados_origen;
END;
GO

IF OBJECT_ID(N'dbo.feriados', N'U') IS NOT NULL
BEGIN
    ALTER TABLE dbo.feriados
    ADD CONSTRAINT CK_feriados_origen
    CHECK (origen IN ('MANUAL','API','API_NAGER','IMPORTACION'));
END;
GO

IF OBJECT_ID(N'dbo.reglas_feriados_irrenunciables', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.reglas_feriados_irrenunciables (
        id_regla int IDENTITY(1,1) NOT NULL,
        pais varchar(10) NOT NULL CONSTRAINT DF_reglas_feriados_irrenunciables_pais DEFAULT 'CL',
        mes int NOT NULL,
        dia int NOT NULL,
        nombre_referencia varchar(200) NOT NULL,
        irrenunciable bit NOT NULL CONSTRAINT DF_reglas_feriados_irrenunciables_irrenunciable DEFAULT 1,
        activo bit NOT NULL CONSTRAINT DF_reglas_feriados_irrenunciables_activo DEFAULT 1,
        observacion varchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_reglas_feriados_irrenunciables_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        CONSTRAINT PK_reglas_feriados_irrenunciables PRIMARY KEY (id_regla),
        CONSTRAINT CK_reglas_feriados_irrenunciables_pais CHECK (LEN(LTRIM(RTRIM(pais))) BETWEEN 1 AND 10),
        CONSTRAINT CK_reglas_feriados_irrenunciables_mes CHECK (mes BETWEEN 1 AND 12),
        CONSTRAINT CK_reglas_feriados_irrenunciables_dia CHECK (dia BETWEEN 1 AND 31)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_reglas_feriados_irrenunciables_pais_mes_dia_activo'
      AND object_id = OBJECT_ID('dbo.reglas_feriados_irrenunciables')
)
BEGIN
    CREATE UNIQUE INDEX UX_reglas_feriados_irrenunciables_pais_mes_dia_activo
    ON dbo.reglas_feriados_irrenunciables(pais, mes, dia)
    WHERE activo = 1;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_reglas_feriados_irrenunciables_busqueda'
      AND object_id = OBJECT_ID('dbo.reglas_feriados_irrenunciables')
)
BEGIN
    CREATE INDEX IX_reglas_feriados_irrenunciables_busqueda
    ON dbo.reglas_feriados_irrenunciables(pais, mes, dia, activo);
END;
GO
