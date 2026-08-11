/* Seed seguro para la unica configuracion global Mail Graph. */

USE [$(DB_NAME)];
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.configuracion_mail_graph
    WHERE clave_configuracion = N'MAIL_GRAPH'
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
    SELECT 1
    FROM dbo.configuracion_sistema
    WHERE clave = N'BOOTSTRAP_SQL'
)
BEGIN
    INSERT INTO dbo.configuracion_sistema (
        clave,
        valor,
        tipo_dato,
        descripcion,
        es_sensible,
        usuario_creacion,
        activo
    )
    VALUES (
        N'BOOTSTRAP_SQL',
        N'19B.0',
        N'TEXTO',
        N'Version del bootstrap limpio aplicado.',
        0,
        N'sistema',
        1
    );
END;
GO
