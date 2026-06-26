/*
Fase 11B - APP Scheduler
Script: 014_crear_scheduler_worker_heartbeat.sql
Objetivo: crear tabla de heartbeat para monitorear el proceso scheduler_worker.py.
Nota: ejecutar manualmente en SSMS. No inicia ni detiene el worker desde la app.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.scheduler_worker_heartbeat', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.scheduler_worker_heartbeat (
        id_worker int IDENTITY(1,1) NOT NULL,
        nombre_worker varchar(100) NOT NULL,
        estado varchar(30) NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_estado DEFAULT 'INICIADO',
        fecha_inicio datetime2(0) NULL,
        fecha_ultimo_heartbeat datetime2(0) NULL,
        fecha_ultimo_ciclo datetime2(0) NULL,
        resultado_ultimo_ciclo varchar(30) NULL,
        ultimo_error varchar(max) NULL,
        ciclos_ejecutados int NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_ciclos DEFAULT 0,
        tareas_evaluadas_ultimo_ciclo int NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_evaluadas DEFAULT 0,
        tareas_ejecutadas_ultimo_ciclo int NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_ejecutadas DEFAULT 0,
        tareas_omitidas_ultimo_ciclo int NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_omitidas DEFAULT 0,
        pid_proceso int NULL,
        host varchar(150) NULL,
        version_app varchar(50) NULL,
        activo bit NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_activo DEFAULT 1,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_scheduler_worker_heartbeat_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        CONSTRAINT PK_scheduler_worker_heartbeat PRIMARY KEY (id_worker),
        CONSTRAINT CK_scheduler_worker_heartbeat_estado CHECK (estado IN ('INICIADO','ACTIVO','EN_CICLO','ESPERANDO','ERROR','DETENIDO')),
        CONSTRAINT CK_scheduler_worker_heartbeat_ciclos CHECK (ciclos_ejecutados >= 0),
        CONSTRAINT CK_scheduler_worker_heartbeat_tareas_evaluadas CHECK (tareas_evaluadas_ultimo_ciclo >= 0),
        CONSTRAINT CK_scheduler_worker_heartbeat_tareas_ejecutadas CHECK (tareas_ejecutadas_ultimo_ciclo >= 0),
        CONSTRAINT CK_scheduler_worker_heartbeat_tareas_omitidas CHECK (tareas_omitidas_ultimo_ciclo >= 0)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_scheduler_worker_heartbeat_nombre_activo'
      AND object_id = OBJECT_ID(N'dbo.scheduler_worker_heartbeat')
)
BEGIN
    CREATE UNIQUE INDEX UX_scheduler_worker_heartbeat_nombre_activo
    ON dbo.scheduler_worker_heartbeat(nombre_worker)
    WHERE activo = 1;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_scheduler_worker_heartbeat_nombre'
      AND object_id = OBJECT_ID(N'dbo.scheduler_worker_heartbeat')
)
BEGIN
    CREATE INDEX IX_scheduler_worker_heartbeat_nombre
    ON dbo.scheduler_worker_heartbeat(nombre_worker);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_scheduler_worker_heartbeat_fecha'
      AND object_id = OBJECT_ID(N'dbo.scheduler_worker_heartbeat')
)
BEGIN
    CREATE INDEX IX_scheduler_worker_heartbeat_fecha
    ON dbo.scheduler_worker_heartbeat(fecha_ultimo_heartbeat);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_scheduler_worker_heartbeat_estado'
      AND object_id = OBJECT_ID(N'dbo.scheduler_worker_heartbeat')
)
BEGIN
    CREATE INDEX IX_scheduler_worker_heartbeat_estado
    ON dbo.scheduler_worker_heartbeat(estado);
END;
GO
