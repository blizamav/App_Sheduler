/*
    Fase 12A - Auditoria de acciones humanas

    Objetivo:
    - Completar dbo.auditoria_cambios para registrar acciones humanas criticas.
    - Mantener compatibilidad con la tabla creada en migracion 005.
    - No borrar historial ni registros existentes.

    Ejecucion manual en SQL Server Management Studio.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.auditoria_cambios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.auditoria_cambios (
        id_auditoria bigint IDENTITY(1,1) NOT NULL,
        fecha_evento datetime2(0) NOT NULL CONSTRAINT DF_auditoria_cambios_fecha_evento DEFAULT SYSDATETIME(),
        usuario nvarchar(100) NOT NULL,
        id_usuario int NULL,
        accion nvarchar(100) NOT NULL,
        entidad nvarchar(100) NOT NULL,
        id_entidad nvarchar(100) NULL,
        nombre_entidad nvarchar(255) NULL,
        descripcion nvarchar(max) NULL,
        valores_antes nvarchar(max) NULL,
        valores_despues nvarchar(max) NULL,
        ip_origen nvarchar(100) NULL,
        user_agent nvarchar(max) NULL,
        resultado nvarchar(50) NULL,
        modulo nvarchar(100) NULL,
        ruta nvarchar(255) NULL,
        metodo_http nvarchar(20) NULL,
        activo bit NOT NULL CONSTRAINT DF_auditoria_cambios_activo DEFAULT 1,
        CONSTRAINT PK_auditoria_cambios PRIMARY KEY (id_auditoria)
    );
END
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'fecha_evento') IS NULL
BEGIN
    ALTER TABLE dbo.auditoria_cambios
    ADD fecha_evento datetime2(0) NULL;
END
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'fecha_hora') IS NOT NULL
BEGIN
    EXEC sp_executesql N'
        UPDATE dbo.auditoria_cambios
        SET fecha_evento = COALESCE(fecha_evento, fecha_hora, SYSDATETIME())
        WHERE fecha_evento IS NULL;
    ';
END
ELSE
BEGIN
    UPDATE dbo.auditoria_cambios
    SET fecha_evento = COALESCE(fecha_evento, SYSDATETIME())
    WHERE fecha_evento IS NULL;
END
GO

IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.auditoria_cambios')
      AND name = N'fecha_evento'
      AND is_nullable = 1
)
BEGIN
    ALTER TABLE dbo.auditoria_cambios ALTER COLUMN fecha_evento datetime2(0) NOT NULL;
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.default_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.auditoria_cambios')
      AND name = N'DF_auditoria_cambios_fecha_evento'
)
BEGIN
    ALTER TABLE dbo.auditoria_cambios
    ADD CONSTRAINT DF_auditoria_cambios_fecha_evento DEFAULT SYSDATETIME() FOR fecha_evento;
END
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'id_usuario') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD id_usuario int NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'entidad') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD entidad nvarchar(100) NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'tabla_afectada') IS NOT NULL
BEGIN
    EXEC sp_executesql N'
        UPDATE dbo.auditoria_cambios
        SET entidad = COALESCE(entidad, tabla_afectada, modulo, N''GENERAL'')
        WHERE entidad IS NULL;
    ';
END
ELSE
BEGIN
    UPDATE dbo.auditoria_cambios
    SET entidad = COALESCE(entidad, modulo, N'GENERAL')
    WHERE entidad IS NULL;
END
GO

IF EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.auditoria_cambios')
      AND name = N'entidad'
      AND is_nullable = 1
)
BEGIN
    ALTER TABLE dbo.auditoria_cambios ALTER COLUMN entidad nvarchar(100) NOT NULL;
END
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'id_entidad') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD id_entidad nvarchar(100) NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'id_registro') IS NOT NULL
BEGIN
    EXEC sp_executesql N'
        UPDATE dbo.auditoria_cambios
        SET id_entidad = COALESCE(id_entidad, id_registro)
        WHERE id_entidad IS NULL;
    ';
END
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'nombre_entidad') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD nombre_entidad nvarchar(255) NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'descripcion') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD descripcion nvarchar(max) NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'valores_antes') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD valores_antes nvarchar(max) NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'valor_anterior') IS NOT NULL
BEGIN
    EXEC sp_executesql N'
        UPDATE dbo.auditoria_cambios
        SET valores_antes = COALESCE(valores_antes, valor_anterior)
        WHERE valores_antes IS NULL;
    ';
END
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'valores_despues') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD valores_despues nvarchar(max) NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'valor_nuevo') IS NOT NULL
BEGIN
    EXEC sp_executesql N'
        UPDATE dbo.auditoria_cambios
        SET valores_despues = COALESCE(valores_despues, valor_nuevo)
        WHERE valores_despues IS NULL;
    ';
END
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'ip_origen') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD ip_origen nvarchar(100) NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'ip') IS NOT NULL
BEGIN
    EXEC sp_executesql N'
        UPDATE dbo.auditoria_cambios
        SET ip_origen = COALESCE(ip_origen, CONVERT(nvarchar(100), ip))
        WHERE ip_origen IS NULL;
    ';
END
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'resultado') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD resultado nvarchar(50) NULL;
GO

UPDATE dbo.auditoria_cambios
SET resultado = COALESCE(resultado, N'OK')
WHERE resultado IS NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'ruta') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD ruta nvarchar(255) NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'metodo_http') IS NULL
    ALTER TABLE dbo.auditoria_cambios ADD metodo_http nvarchar(20) NULL;
GO

IF COL_LENGTH('dbo.auditoria_cambios', 'activo') IS NULL
BEGIN
    ALTER TABLE dbo.auditoria_cambios
    ADD activo bit NOT NULL CONSTRAINT DF_auditoria_cambios_activo DEFAULT 1;
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.auditoria_cambios')
      AND name = N'IX_auditoria_cambios_fecha_evento'
)
BEGIN
    CREATE INDEX IX_auditoria_cambios_fecha_evento
    ON dbo.auditoria_cambios(fecha_evento DESC, id_auditoria DESC);
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.auditoria_cambios')
      AND name = N'IX_auditoria_cambios_usuario'
)
BEGIN
    CREATE INDEX IX_auditoria_cambios_usuario
    ON dbo.auditoria_cambios(usuario, fecha_evento DESC);
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.auditoria_cambios')
      AND name = N'IX_auditoria_cambios_entidad'
)
BEGIN
    CREATE INDEX IX_auditoria_cambios_entidad
    ON dbo.auditoria_cambios(entidad, id_entidad, fecha_evento DESC);
END
GO
