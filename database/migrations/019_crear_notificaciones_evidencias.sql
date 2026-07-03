/*
    Fase 15C - Migracion de notificaciones y evidencias

    Objetivo:
    - Crear tablas minimas para configuracion de evidencia por tarea.
    - Crear destinatarios por configuracion.
    - Registrar trazabilidad minima de evidencia capturada por stdout.
    - Registrar intentos de envio por Graph o alerta interna.

    Reglas:
    - No guarda JSON completo de evidencia.
    - No guarda cuerpo completo del correo.
    - No guarda secretos Graph, tokens, passwords ni cadenas de conexion.
    - No ejecuta envios ni implementa Graph.

    Ejecucion manual en SQL Server Management Studio.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.notificaciones_config_tarea', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.notificaciones_config_tarea (
        id_config_notificacion int IDENTITY(1,1) NOT NULL,
        id_tarea int NOT NULL,
        enviar_evidencia bit NOT NULL CONSTRAINT DF_notif_config_enviar_evidencia DEFAULT 0,
        plantilla_evidencia nvarchar(100) NULL CONSTRAINT DF_notif_config_plantilla DEFAULT N'STDOUT_V1',
        asunto_personalizado nvarchar(255) NULL,
        usar_asunto_sugerido_script bit NOT NULL CONSTRAINT DF_notif_config_usar_asunto_script DEFAULT 1,
        adjuntar_archivos_declarados bit NOT NULL CONSTRAINT DF_notif_config_adjuntar_archivos DEFAULT 1,
        adjuntar_log_tecnico bit NOT NULL CONSTRAINT DF_notif_config_adjuntar_log DEFAULT 0,
        alerta_error_activa bit NOT NULL CONSTRAINT DF_notif_config_alerta_error DEFAULT 1,
        usar_alerta_global bit NOT NULL CONSTRAINT DF_notif_config_usar_alerta_global DEFAULT 1,
        activo bit NOT NULL CONSTRAINT DF_notif_config_activo DEFAULT 1,
        creado_en datetime2(0) NOT NULL CONSTRAINT DF_notif_config_creado_en DEFAULT SYSDATETIME(),
        actualizado_en datetime2(0) NULL,
        CONSTRAINT PK_notificaciones_config_tarea PRIMARY KEY (id_config_notificacion),
        CONSTRAINT FK_notif_config_tareas FOREIGN KEY (id_tarea) REFERENCES dbo.tareas(id_tarea),
        CONSTRAINT CK_notif_config_plantilla CHECK (plantilla_evidencia IS NULL OR plantilla_evidencia IN (N'STDOUT_V1'))
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_notif_config_tarea_activa'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
)
BEGIN
    CREATE UNIQUE INDEX UX_notif_config_tarea_activa
    ON dbo.notificaciones_config_tarea(id_tarea)
    WHERE activo = 1;
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_notif_config_tarea_activo'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
)
BEGIN
    CREATE INDEX IX_notif_config_tarea_activo
    ON dbo.notificaciones_config_tarea(id_tarea, activo);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_notif_config_enviar_evidencia'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
)
BEGIN
    CREATE INDEX IX_notif_config_enviar_evidencia
    ON dbo.notificaciones_config_tarea(enviar_evidencia, activo);
END;
GO

IF OBJECT_ID(N'dbo.notificaciones_destinatarios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.notificaciones_destinatarios (
        id_destinatario int IDENTITY(1,1) NOT NULL,
        id_config_notificacion int NOT NULL,
        tipo_destinatario nvarchar(20) NOT NULL,
        canal nvarchar(10) NOT NULL,
        email nvarchar(255) NOT NULL,
        nombre nvarchar(150) NULL,
        activo bit NOT NULL CONSTRAINT DF_notif_dest_activo DEFAULT 1,
        creado_en datetime2(0) NOT NULL CONSTRAINT DF_notif_dest_creado_en DEFAULT SYSDATETIME(),
        CONSTRAINT PK_notificaciones_destinatarios PRIMARY KEY (id_destinatario),
        CONSTRAINT FK_notif_dest_config FOREIGN KEY (id_config_notificacion) REFERENCES dbo.notificaciones_config_tarea(id_config_notificacion),
        CONSTRAINT CK_notif_dest_tipo CHECK (tipo_destinatario IN (N'EVIDENCIA', N'ALERTA')),
        CONSTRAINT CK_notif_dest_canal CHECK (canal IN (N'TO', N'CC', N'BCC')),
        CONSTRAINT CK_notif_dest_email_basico CHECK (email LIKE N'%_@_%._%')
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_notif_dest_activo'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_destinatarios')
)
BEGIN
    CREATE UNIQUE INDEX UX_notif_dest_activo
    ON dbo.notificaciones_destinatarios(id_config_notificacion, tipo_destinatario, canal, email)
    WHERE activo = 1;
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_notif_dest_config_tipo_activo'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_destinatarios')
)
BEGIN
    CREATE INDEX IX_notif_dest_config_tipo_activo
    ON dbo.notificaciones_destinatarios(id_config_notificacion, tipo_destinatario, activo);
END;
GO

IF OBJECT_ID(N'dbo.evidencias_ejecucion', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.evidencias_ejecucion (
        id_evidencia bigint IDENTITY(1,1) NOT NULL,
        id_ejecucion bigint NOT NULL,
        estado_evidencia nvarchar(40) NOT NULL,
        version_contrato nvarchar(20) NULL,
        tipo_evidencia nvarchar(100) NULL,
        titulo nvarchar(255) NULL,
        asunto_sugerido nvarchar(255) NULL,
        hash_evidencia nvarchar(128) NULL,
        cantidad_campos_resumen int NOT NULL CONSTRAINT DF_evidencias_campos DEFAULT 0,
        cantidad_adjuntos_declarados int NOT NULL CONSTRAINT DF_evidencias_adjuntos DEFAULT 0,
        cantidad_problemas int NOT NULL CONSTRAINT DF_evidencias_problemas DEFAULT 0,
        bloque_detectado bit NOT NULL CONSTRAINT DF_evidencias_bloque_detectado DEFAULT 0,
        delimitador_inicio_detectado bit NOT NULL CONSTRAINT DF_evidencias_delim_inicio DEFAULT 0,
        delimitador_fin_detectado bit NOT NULL CONSTRAINT DF_evidencias_delim_fin DEFAULT 0,
        error_validacion nvarchar(1000) NULL,
        creado_en datetime2(0) NOT NULL CONSTRAINT DF_evidencias_creado_en DEFAULT SYSDATETIME(),
        CONSTRAINT PK_evidencias_ejecucion PRIMARY KEY (id_evidencia),
        CONSTRAINT FK_evidencias_ejecuciones FOREIGN KEY (id_ejecucion) REFERENCES dbo.ejecuciones(id_ejecucion),
        CONSTRAINT UX_evidencias_ejecucion UNIQUE (id_ejecucion),
        CONSTRAINT CK_evidencias_estado CHECK (
            estado_evidencia IN (
                N'NO_REQUERIDA',
                N'SOPORTE_NO_DECLARADO',
                N'DELIMITADORES_NO_DECLARADOS',
                N'NO_EMITIDA',
                N'CAPTURADA',
                N'INVALIDA',
                N'ERROR_DECLARADO',
                N'ADJUNTO_FALTANTE',
                N'VALIDADA'
            )
        ),
        CONSTRAINT CK_evidencias_cantidades CHECK (
            cantidad_campos_resumen >= 0
            AND cantidad_adjuntos_declarados >= 0
            AND cantidad_problemas >= 0
        )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_evidencias_estado_fecha'
      AND object_id = OBJECT_ID(N'dbo.evidencias_ejecucion')
)
BEGIN
    CREATE INDEX IX_evidencias_estado_fecha
    ON dbo.evidencias_ejecucion(estado_evidencia, creado_en DESC);
END;
GO

IF OBJECT_ID(N'dbo.notificaciones_envios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.notificaciones_envios (
        id_envio bigint IDENTITY(1,1) NOT NULL,
        id_ejecucion bigint NOT NULL,
        id_evidencia bigint NULL,
        tipo_envio nvarchar(30) NOT NULL,
        estado_envio nvarchar(30) NOT NULL,
        asunto nvarchar(255) NULL,
        destinatarios_to nvarchar(max) NULL,
        destinatarios_cc nvarchar(max) NULL,
        destinatarios_bcc nvarchar(max) NULL,
        graph_status_code int NULL,
        graph_request_id nvarchar(255) NULL,
        error_controlado nvarchar(2000) NULL,
        intento int NOT NULL CONSTRAINT DF_notif_envios_intento DEFAULT 1,
        es_reintento bit NOT NULL CONSTRAINT DF_notif_envios_es_reintento DEFAULT 0,
        id_envio_origen bigint NULL,
        fecha_intento datetime2(0) NOT NULL CONSTRAINT DF_notif_envios_fecha_intento DEFAULT SYSDATETIME(),
        fecha_envio datetime2(0) NULL,
        creado_en datetime2(0) NOT NULL CONSTRAINT DF_notif_envios_creado_en DEFAULT SYSDATETIME(),
        CONSTRAINT PK_notificaciones_envios PRIMARY KEY (id_envio),
        CONSTRAINT FK_notif_envios_ejecuciones FOREIGN KEY (id_ejecucion) REFERENCES dbo.ejecuciones(id_ejecucion),
        CONSTRAINT FK_notif_envios_evidencias FOREIGN KEY (id_evidencia) REFERENCES dbo.evidencias_ejecucion(id_evidencia),
        CONSTRAINT FK_notif_envios_origen FOREIGN KEY (id_envio_origen) REFERENCES dbo.notificaciones_envios(id_envio),
        CONSTRAINT CK_notif_envios_tipo CHECK (tipo_envio IN (N'EVIDENCIA_CLIENTE', N'ALERTA_INTERNA')),
        CONSTRAINT CK_notif_envios_estado CHECK (estado_envio IN (N'PENDIENTE', N'ENVIADO', N'FALLIDO', N'OMITIDO', N'NO_REQUERIDO')),
        CONSTRAINT CK_notif_envios_intento CHECK (intento >= 1),
        CONSTRAINT CK_notif_envios_graph_status CHECK (graph_status_code IS NULL OR graph_status_code BETWEEN 100 AND 599)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_notif_envios_ejecucion_fecha'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_envios')
)
BEGIN
    CREATE INDEX IX_notif_envios_ejecucion_fecha
    ON dbo.notificaciones_envios(id_ejecucion, fecha_intento DESC);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_notif_envios_evidencia_fecha'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_envios')
)
BEGIN
    CREATE INDEX IX_notif_envios_evidencia_fecha
    ON dbo.notificaciones_envios(id_evidencia, fecha_intento DESC);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_notif_envios_tipo_estado_fecha'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_envios')
)
BEGIN
    CREATE INDEX IX_notif_envios_tipo_estado_fecha
    ON dbo.notificaciones_envios(tipo_envio, estado_envio, fecha_intento DESC);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_notif_envios_origen'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_envios')
)
BEGIN
    CREATE INDEX IX_notif_envios_origen
    ON dbo.notificaciones_envios(id_envio_origen);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_notif_envio_exitoso_cliente'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_envios')
)
BEGIN
    CREATE UNIQUE INDEX UX_notif_envio_exitoso_cliente
    ON dbo.notificaciones_envios(id_ejecucion, tipo_envio)
    WHERE tipo_envio = N'EVIDENCIA_CLIENTE'
      AND estado_envio = N'ENVIADO';
END;
GO
