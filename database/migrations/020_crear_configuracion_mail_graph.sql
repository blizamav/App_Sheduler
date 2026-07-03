/*
    Fase 15F - Configuracion global Mail Automatico Graph

    Objetivo:
    - Crear tabla especifica para configuracion no sensible de Microsoft Graph.
    - Mantener CLIENT_SECRET, tokens y credenciales fuera de SQL Server.
    - Dejar una configuracion global unica para origen de correo automatico.

    Reglas:
    - No guarda GRAPH_CLIENT_SECRET.
    - No guarda access_token ni refresh_token.
    - No envia correos.
    - No llama a Microsoft Graph.

    Ejecucion manual en SQL Server Management Studio.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.configuracion_mail_graph', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.configuracion_mail_graph (
        id_config_mail int IDENTITY(1,1) NOT NULL,
        clave_configuracion nvarchar(30) NOT NULL CONSTRAINT DF_config_mail_graph_clave DEFAULT N'MAIL_GRAPH',
        activo bit NOT NULL CONSTRAINT DF_config_mail_graph_activo DEFAULT 0,
        tenant_id nvarchar(100) NULL,
        client_id nvarchar(100) NULL,
        graph_scope nvarchar(255) NOT NULL CONSTRAINT DF_config_mail_graph_scope DEFAULT N'https://graph.microsoft.com/.default',
        send_mail_user nvarchar(255) NULL,
        save_to_sent_items bit NOT NULL CONSTRAINT DF_config_mail_graph_sent DEFAULT 1,
        alertas_destinatarios_default nvarchar(max) NULL,
        client_secret_origen nvarchar(20) NOT NULL CONSTRAINT DF_config_mail_graph_secret_origen DEFAULT N'ENV',
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_config_mail_graph_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_actualizacion nvarchar(150) NULL,
        CONSTRAINT PK_configuracion_mail_graph PRIMARY KEY (id_config_mail),
        CONSTRAINT CK_config_mail_graph_clave CHECK (clave_configuracion = N'MAIL_GRAPH'),
        CONSTRAINT CK_config_mail_graph_secret_origen CHECK (client_secret_origen IN (N'ENV')),
        CONSTRAINT CK_config_mail_graph_scope CHECK (
            graph_scope = N'https://graph.microsoft.com/.default'
            OR graph_scope LIKE N'https://graph.microsoft.com/%'
        ),
        CONSTRAINT CK_config_mail_graph_send_mail_user CHECK (
            send_mail_user IS NULL
            OR (send_mail_user LIKE N'%_@_%._%' AND send_mail_user NOT LIKE N'% %')
        )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.configuracion_mail_graph
)
BEGIN
    INSERT INTO dbo.configuracion_mail_graph (
        clave_configuracion,
        activo,
        graph_scope,
        save_to_sent_items,
        alertas_destinatarios_default,
        client_secret_origen,
        usuario_actualizacion
    )
    VALUES (
        N'MAIL_GRAPH',
        0,
        N'https://graph.microsoft.com/.default',
        1,
        NULL,
        N'ENV',
        N'sistema'
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_config_mail_graph_unica_activa'
      AND object_id = OBJECT_ID(N'dbo.configuracion_mail_graph')
)
BEGIN
    CREATE UNIQUE INDEX UX_config_mail_graph_unica_activa
    ON dbo.configuracion_mail_graph(activo)
    WHERE activo = 1;
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_config_mail_graph_clave'
      AND object_id = OBJECT_ID(N'dbo.configuracion_mail_graph')
)
BEGIN
    CREATE UNIQUE INDEX UX_config_mail_graph_clave
    ON dbo.configuracion_mail_graph(clave_configuracion);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_config_mail_graph_actualizacion'
      AND object_id = OBJECT_ID(N'dbo.configuracion_mail_graph')
)
BEGIN
    CREATE INDEX IX_config_mail_graph_actualizacion
    ON dbo.configuracion_mail_graph(fecha_actualizacion DESC, id_config_mail DESC);
END;
GO
