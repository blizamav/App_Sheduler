/*
    Parche v1.0.1 - Separacion definitiva de notificaciones y Evidencia 1.0

    Objetivo:
    - Eliminar la dependencia artificial Evidencia -> Notificacion de exito.
    - Crear el grupo EXITO para destinatarios operacionales.
    - Preservar historial sin asumir que un destinatario operacional es cliente.

    Seguridad de migracion:
    - No elimina filas.
    - Copia destinatarios legacy EVIDENCIA a EXITO solo cuando no existe grupo EXITO.
    - Desactiva esos EVIDENCIA ambiguos y apaga enviar_evidencia para exigir una
      configuracion explicita posterior del destinatario cliente.
    - Es idempotente.

    Ejecucion manual posterior en SQL Server. Este archivo no se ejecuta solo.
*/

USE APP_SCHEDULER_QA;
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET QUOTED_IDENTIFIER ON;
SET NUMERIC_ROUNDABORT OFF;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.notificaciones_config_tarea', N'U') IS NULL
        THROW 51000, 'No existe dbo.notificaciones_config_tarea.', 1;

    IF OBJECT_ID(N'dbo.notificaciones_destinatarios', N'U') IS NULL
        THROW 51001, 'No existe dbo.notificaciones_destinatarios.', 1;

    IF COL_LENGTH(N'dbo.notificaciones_config_tarea', N'notificar_exito_activa') IS NULL
        THROW 51002, 'Falta notificar_exito_activa. Ejecutar primero la migracion 022.', 1;

    IF EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name = N'CK_notif_config_evidencia_requiere_exito'
          AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
    )
        ALTER TABLE dbo.notificaciones_config_tarea
        DROP CONSTRAINT CK_notif_config_evidencia_requiere_exito;

    IF EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name = N'CK_notif_dest_tipo'
          AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_destinatarios')
          AND definition NOT LIKE N'%EXITO%'
    )
    BEGIN
        IF EXISTS (
            SELECT 1 FROM sys.check_constraints
            WHERE name = N'CK_notif_dest_tipo'
              AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_destinatarios')
              AND (definition NOT LIKE N'%EVIDENCIA%' OR definition NOT LIKE N'%ALERTA%')
        )
            THROW 51003, 'CK_notif_dest_tipo tiene una definicion inesperada.', 1;

        ALTER TABLE dbo.notificaciones_destinatarios DROP CONSTRAINT CK_notif_dest_tipo;
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name = N'CK_notif_dest_tipo'
          AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_destinatarios')
    )
    BEGIN
        ALTER TABLE dbo.notificaciones_destinatarios WITH CHECK
        ADD CONSTRAINT CK_notif_dest_tipo
        CHECK (tipo_destinatario IN (N'EXITO', N'EVIDENCIA', N'ALERTA'));
    END;

    DECLARE @configuraciones_legacy TABLE (
        id_config_notificacion int NOT NULL PRIMARY KEY
    );

    INSERT INTO @configuraciones_legacy (id_config_notificacion)
    SELECT c.id_config_notificacion
    FROM dbo.notificaciones_config_tarea c
    WHERE c.activo = 1
      AND c.notificar_exito_activa = 1
      AND EXISTS (
          SELECT 1 FROM dbo.notificaciones_destinatarios d
          WHERE d.id_config_notificacion = c.id_config_notificacion
            AND d.tipo_destinatario = N'EVIDENCIA' AND d.activo = 1
      )
      AND NOT EXISTS (
          SELECT 1 FROM dbo.notificaciones_destinatarios d
          WHERE d.id_config_notificacion = c.id_config_notificacion
            AND d.tipo_destinatario = N'EXITO' AND d.activo = 1
      );

    INSERT INTO dbo.notificaciones_destinatarios
        (id_config_notificacion, tipo_destinatario, canal, email, nombre, activo)
    SELECT d.id_config_notificacion, N'EXITO', d.canal, d.email, d.nombre, 1
    FROM dbo.notificaciones_destinatarios d
    INNER JOIN @configuraciones_legacy l
        ON l.id_config_notificacion = d.id_config_notificacion
    WHERE d.tipo_destinatario = N'EVIDENCIA'
      AND d.activo = 1
      AND NOT EXISTS (
          SELECT 1 FROM dbo.notificaciones_destinatarios x
          WHERE x.id_config_notificacion = d.id_config_notificacion
            AND x.tipo_destinatario = N'EXITO'
            AND x.canal = d.canal
            AND x.email = d.email
            AND x.activo = 1
      );

    UPDATE d
    SET d.activo = 0
    FROM dbo.notificaciones_destinatarios d
    INNER JOIN @configuraciones_legacy l
        ON l.id_config_notificacion = d.id_config_notificacion
    WHERE d.tipo_destinatario = N'EVIDENCIA'
      AND d.activo = 1;

    UPDATE c
    SET c.enviar_evidencia = 0,
        c.actualizado_en = SYSDATETIME()
    FROM dbo.notificaciones_config_tarea c
    INNER JOIN @configuraciones_legacy l
        ON l.id_config_notificacion = c.id_config_notificacion
    WHERE c.enviar_evidencia = 1;

    IF EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name = N'CK_notif_config_evidencia_requiere_exito'
          AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_config_tarea')
    )
        THROW 51004, 'No se pudo retirar la dependencia Evidencia -> Exito.', 1;

    IF EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE name = N'CK_notif_dest_tipo'
          AND parent_object_id = OBJECT_ID(N'dbo.notificaciones_destinatarios')
          AND (
              definition NOT LIKE N'%EXITO%'
              OR definition NOT LIKE N'%EVIDENCIA%'
              OR definition NOT LIKE N'%ALERTA%'
              OR is_disabled = 1
              OR is_not_trusted = 1
          )
    )
        THROW 51005, 'El grupo de destinatarios EXITO no quedo habilitado.', 1;

    SELECT
        (SELECT COUNT(*) FROM @configuraciones_legacy) AS configuraciones_migradas,
        (SELECT COUNT(*) FROM dbo.notificaciones_destinatarios
         WHERE tipo_destinatario = N'EXITO' AND activo = 1) AS destinatarios_exito_activos,
        (SELECT COUNT(*) FROM dbo.notificaciones_destinatarios
         WHERE tipo_destinatario = N'EVIDENCIA' AND activo = 1) AS destinatarios_evidencia_activos;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
