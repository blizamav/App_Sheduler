/*
Fase 11D - APP Scheduler
Script: 015_crear_eventos_programador.sql
Objetivo: crear tabla de eventos y omisiones del programador.
Nota: ejecutar manualmente en SSMS. No crea ejecuciones para tareas omitidas.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.scheduler_eventos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.scheduler_eventos (
        id_evento int IDENTITY(1,1) NOT NULL,
        fecha_evento datetime NOT NULL CONSTRAINT DF_scheduler_eventos_fecha DEFAULT GETDATE(),
        nombre_worker varchar(100) NULL,
        id_tarea int NULL,
        nombre_tarea varchar(200) NULL,
        id_programacion int NULL,
        fecha_programada datetime NULL,
        clave_programacion varchar(200) NULL,
        tipo_evento varchar(50) NOT NULL,
        decision varchar(50) NOT NULL,
        motivo varchar(100) NULL,
        detalle varchar(max) NULL,
        estado_scheduler varchar(50) NULL,
        ejecutar_en_feriados bit NULL,
        es_feriado bit NULL,
        nombre_feriado varchar(200) NULL,
        origen varchar(50) NOT NULL CONSTRAINT DF_scheduler_eventos_origen DEFAULT 'SCHEDULER',
        activo bit NOT NULL CONSTRAINT DF_scheduler_eventos_activo DEFAULT 1,
        CONSTRAINT PK_scheduler_eventos PRIMARY KEY (id_evento),
        CONSTRAINT CK_scheduler_eventos_tipo CHECK (tipo_evento IN ('CICLO_INICIADO','CICLO_FINALIZADO','TAREA_EVALUADA','TAREA_EJECUTADA','TAREA_OMITIDA','ERROR_SCHEDULER')),
        CONSTRAINT CK_scheduler_eventos_decision CHECK (decision IN ('EJECUTAR','OMITIR','ERROR','INFO')),
        CONSTRAINT CK_scheduler_eventos_origen CHECK (origen IN ('SCHEDULER'))
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_scheduler_eventos_fecha'
      AND object_id = OBJECT_ID(N'dbo.scheduler_eventos')
)
BEGIN
    CREATE INDEX IX_scheduler_eventos_fecha
    ON dbo.scheduler_eventos(fecha_evento DESC);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_scheduler_eventos_tarea'
      AND object_id = OBJECT_ID(N'dbo.scheduler_eventos')
)
BEGIN
    CREATE INDEX IX_scheduler_eventos_tarea
    ON dbo.scheduler_eventos(id_tarea);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_scheduler_eventos_fecha_programada'
      AND object_id = OBJECT_ID(N'dbo.scheduler_eventos')
)
BEGIN
    CREATE INDEX IX_scheduler_eventos_fecha_programada
    ON dbo.scheduler_eventos(fecha_programada);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_scheduler_eventos_tipo'
      AND object_id = OBJECT_ID(N'dbo.scheduler_eventos')
)
BEGIN
    CREATE INDEX IX_scheduler_eventos_tipo
    ON dbo.scheduler_eventos(tipo_evento);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_scheduler_eventos_decision'
      AND object_id = OBJECT_ID(N'dbo.scheduler_eventos')
)
BEGIN
    CREATE INDEX IX_scheduler_eventos_decision
    ON dbo.scheduler_eventos(decision);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_scheduler_eventos_motivo'
      AND object_id = OBJECT_ID(N'dbo.scheduler_eventos')
)
BEGIN
    CREATE INDEX IX_scheduler_eventos_motivo
    ON dbo.scheduler_eventos(motivo);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_scheduler_eventos_worker'
      AND object_id = OBJECT_ID(N'dbo.scheduler_eventos')
)
BEGIN
    CREATE INDEX IX_scheduler_eventos_worker
    ON dbo.scheduler_eventos(nombre_worker);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_scheduler_eventos_clave'
      AND object_id = OBJECT_ID(N'dbo.scheduler_eventos')
)
BEGIN
    CREATE INDEX IX_scheduler_eventos_clave
    ON dbo.scheduler_eventos(clave_programacion);
END;
GO
