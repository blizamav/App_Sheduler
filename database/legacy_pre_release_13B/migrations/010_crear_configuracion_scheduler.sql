/*
Fase 9A - APP Scheduler
Script: 010_crear_configuracion_scheduler.sql
Objetivo: crear configuracion operativa del scheduler en base de datos.
Nota: ejecutar manualmente en SSMS. No inicia worker ni ejecuciones automaticas.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.configuracion_scheduler', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.configuracion_scheduler (
        id_configuracion int IDENTITY(1,1) NOT NULL,
        scheduler_activo bit NOT NULL CONSTRAINT DF_configuracion_scheduler_activo_scheduler DEFAULT 0,
        intervalo_revision_segundos int NOT NULL CONSTRAINT DF_configuracion_scheduler_intervalo DEFAULT 60,
        max_ejecuciones_concurrentes int NOT NULL CONSTRAINT DF_configuracion_scheduler_max DEFAULT 3,
        permitir_ejecucion_automatica bit NOT NULL CONSTRAINT DF_configuracion_scheduler_permitir DEFAULT 0,
        modo_mantenimiento bit NOT NULL CONSTRAINT DF_configuracion_scheduler_mantenimiento DEFAULT 0,
        nombre_worker_principal varchar(100) NULL,
        descripcion varchar(500) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_configuracion_scheduler_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_configuracion_scheduler_activo DEFAULT 1,
        CONSTRAINT PK_configuracion_scheduler PRIMARY KEY (id_configuracion),
        CONSTRAINT CK_configuracion_scheduler_intervalo CHECK (intervalo_revision_segundos BETWEEN 10 AND 3600),
        CONSTRAINT CK_configuracion_scheduler_max CHECK (max_ejecuciones_concurrentes BETWEEN 1 AND 20)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_configuracion_scheduler_activa'
      AND object_id = OBJECT_ID(N'dbo.configuracion_scheduler')
)
BEGIN
    CREATE UNIQUE INDEX UX_configuracion_scheduler_activa
    ON dbo.configuracion_scheduler(activo)
    WHERE activo = 1;
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.configuracion_scheduler WHERE activo = 1)
BEGIN
    INSERT INTO dbo.configuracion_scheduler
        (scheduler_activo, intervalo_revision_segundos, max_ejecuciones_concurrentes,
         permitir_ejecucion_automatica, modo_mantenimiento, nombre_worker_principal,
         descripcion, usuario_actualizacion, activo)
    VALUES
        (0, 60, 3, 0, 0, 'worker_default',
         'Configuracion inicial segura. Scheduler apagado por defecto.',
         N'migration_010', 1);
END;
GO
