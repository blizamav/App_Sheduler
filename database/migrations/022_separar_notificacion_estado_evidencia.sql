/*
    Ajuste contractual post-Hito 10 - Notificacion de exito independiente

    Objetivo:
    - Separar la notificacion estandar EXITOSA de la Evidencia 1.0 opcional.
    - Preservar la intencion historica de enviar al finalizar correctamente.
    - Mantener EVIDENCIA_CLIENTE y ALERTA_INTERNA como tipos legacy validos.

    Ejecucion: manual y autorizada posteriormente sobre APP_SCHEDULER_QA.
    Este script no envia correos ni modifica destinatarios o estados de error.
*/

USE APP_SCHEDULER_QA;
GO

SET XACT_ABORT ON;
GO

IF OBJECT_ID(N'dbo.notificaciones_config_tarea', N'U') IS NULL
    THROW 51000, 'No existe dbo.notificaciones_config_tarea. Ejecutar primero la migracion 019.', 1;

IF OBJECT_ID(N'dbo.notificaciones_envios', N'U') IS NULL
    THROW 51001, 'No existe dbo.notificaciones_envios. Ejecutar primero la migracion 019.', 1;
GO

IF COL_LENGTH(N'dbo.notificaciones_config_tarea', N'notificar_exito_activa') IS NULL
BEGIN
    ALTER TABLE dbo.notificaciones_config_tarea
    ADD notificar_exito_activa bit NOT NULL
        CONSTRAINT DF_notif_config_notificar_exito DEFAULT 0 WITH VALUES;
END;
ELSE IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
      AND name = N'notificar_exito_activa'
      AND (system_type_id <> TYPE_ID(N'bit') OR is_nullable <> 0)
)
    THROW 51002, 'notificar_exito_activa existe con un contrato incompatible.', 1;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
      AND c.name = N'notificar_exito_activa'
)
BEGIN
    ALTER TABLE dbo.notificaciones_config_tarea
    ADD CONSTRAINT DF_notif_config_notificar_exito
        DEFAULT 0 FOR notificar_exito_activa;
END;
ELSE IF EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
      AND c.name = N'notificar_exito_activa'
      AND REPLACE(REPLACE(REPLACE(dc.definition, N'(', N''), N')', N''), N' ', N'') <> N'0'
)
    THROW 51005, 'notificar_exito_activa posee un DEFAULT incompatible.', 1;
GO

/* Preserva la intencion historica: enviar_evidencia implicaba envio exitoso. */
UPDATE dbo.notificaciones_config_tarea
SET notificar_exito_activa = 1,
    actualizado_en = SYSDATETIME()
WHERE enviar_evidencia = 1
  AND notificar_exito_activa = 0;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_notif_config_evidencia_requiere_exito'
      AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
)
BEGIN
    ALTER TABLE dbo.notificaciones_config_tarea WITH CHECK
    ADD CONSTRAINT CK_notif_config_evidencia_requiere_exito
        CHECK (enviar_evidencia = 0 OR notificar_exito_activa = 1);
END;
GO

IF EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_notif_config_evidencia_requiere_exito'
      AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
      AND (definition NOT LIKE N'%enviar_evidencia%'
           OR definition NOT LIKE N'%notificar_exito_activa%')
)
    THROW 51006, 'CK_notif_config_evidencia_requiere_exito tiene una definicion incompatible.', 1;
GO

IF EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_notif_envios_tipo'
      AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_envios')
      AND definition NOT LIKE N'%NOTIFICACION_EXITOSA%'
)
BEGIN
    IF EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name = N'CK_notif_envios_tipo'
          AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_envios')
          AND (definition NOT LIKE N'%EVIDENCIA_CLIENTE%'
               OR definition NOT LIKE N'%ALERTA_INTERNA%')
    )
        THROW 51003, 'CK_notif_envios_tipo tiene una definicion inesperada.', 1;

    ALTER TABLE dbo.notificaciones_envios DROP CONSTRAINT CK_notif_envios_tipo;
END;
GO


IF EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_notif_envio_notificacion_exitosa'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_envios')
      AND (is_unique <> 1 OR filter_definition NOT LIKE N'%NOTIFICACION_EXITOSA%'
           OR filter_definition NOT LIKE N'%ENVIADO%')
)
    THROW 51007, 'UX_notif_envio_notificacion_exitosa tiene una definicion incompatible.', 1;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_notif_envios_tipo'
      AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_envios')
)
BEGIN
    ALTER TABLE dbo.notificaciones_envios WITH CHECK
    ADD CONSTRAINT CK_notif_envios_tipo CHECK (
        tipo_envio IN (N'NOTIFICACION_EXITOSA', N'EVIDENCIA_CLIENTE', N'ALERTA_INTERNA')
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_notif_envio_notificacion_exitosa'
      AND object_id = OBJECT_ID(N'dbo.notificaciones_envios')
)
BEGIN
    CREATE UNIQUE INDEX UX_notif_envio_notificacion_exitosa
    ON dbo.notificaciones_envios(id_ejecucion, tipo_envio)
    WHERE tipo_envio = N'NOTIFICACION_EXITOSA'
      AND estado_envio = N'ENVIADO';
END;
GO

IF EXISTS (
    SELECT 1 FROM dbo.notificaciones_config_tarea
    WHERE enviar_evidencia = 1 AND notificar_exito_activa = 0
)
    THROW 51004, 'Existen configuraciones de evidencia sin notificacion de exito.', 1;

SELECT
    COUNT(*) AS configuraciones,
    SUM(CASE WHEN notificar_exito_activa = 1 THEN 1 ELSE 0 END) AS notifican_exito,
    SUM(CASE WHEN enviar_evidencia = 1 THEN 1 ELSE 0 END) AS incluyen_evidencia
FROM dbo.notificaciones_config_tarea;
GO
