/*
    Fase 15F.1 - Consolidacion configuracion Mail Graph QA

    Objetivo:
    - Corregir APP_SCHEDULER_QA despues de que la migracion 020 fue ejecutada
      antes del ajuste de guardado sobre fila unica.
    - Conservar exclusivamente id_config_mail = 3 como configuracion global valida.
    - Eliminar solo filas duplicadas conocidas generadas por bug de formulario:
      id_config_mail IN (1, 2, 4).
    - Agregar clave_configuracion = MAIL_GRAPH e indice unico para impedir duplicacion futura.

    Reglas:
    - No guardar GRAPH_CLIENT_SECRET.
    - No enviar correos.
    - No llamar a Microsoft Graph.
    - No tocar database/release/.
    - Ejecutar manualmente en SQL Server Management Studio.

    Validaciones esperadas antes de ejecutar:
    - Revisar SELECT inicial.
    - Confirmar que id_config_mail = 3 corresponde a la fila correcta.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.configuracion_mail_graph', N'U') IS NULL
BEGIN
    THROW 51000, 'No existe dbo.configuracion_mail_graph. Ejecutar primero la migracion 020.', 1;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.configuracion_mail_graph
    WHERE id_config_mail = 3
)
BEGIN
    THROW 51001, 'No existe id_config_mail = 3. No se puede consolidar automaticamente.', 1;
END;
GO

IF EXISTS (
    SELECT 1
    FROM dbo.configuracion_mail_graph
    WHERE id_config_mail = 3
      AND ISNULL(send_mail_user, N'') <> N'bpm@soex.cl'
)
BEGIN
    THROW 51002, 'La fila id_config_mail = 3 no coincide con el buzon esperado bpm@soex.cl.', 1;
END;
GO

IF COL_LENGTH(N'dbo.configuracion_mail_graph', N'clave_configuracion') IS NULL
BEGIN
    ALTER TABLE dbo.configuracion_mail_graph
    ADD clave_configuracion nvarchar(30) NOT NULL
        CONSTRAINT DF_config_mail_graph_clave DEFAULT N'MAIL_GRAPH';
END;
GO

UPDATE dbo.configuracion_mail_graph
SET clave_configuracion = N'MAIL_GRAPH'
WHERE id_config_mail = 3;
GO

/*
    Limpieza controlada:
    Estas filas fueron generadas por el bug de guardado detectado en Fase 15F.
    No se elimina ninguna otra fila fuera de la lista explicita.
*/
DELETE FROM dbo.configuracion_mail_graph
WHERE id_config_mail IN (1, 2, 4);
GO

IF EXISTS (
    SELECT 1
    FROM dbo.configuracion_mail_graph
    GROUP BY clave_configuracion
    HAVING COUNT(*) > 1
)
BEGIN
    THROW 51003, 'Aun existen multiples filas por clave_configuracion. Revisar manualmente antes de crear indice unico.', 1;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = N'CK_config_mail_graph_clave'
      AND parent_object_id = OBJECT_ID(N'dbo.configuracion_mail_graph')
)
BEGIN
    ALTER TABLE dbo.configuracion_mail_graph WITH CHECK
    ADD CONSTRAINT CK_config_mail_graph_clave
    CHECK (clave_configuracion = N'MAIL_GRAPH');
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_config_mail_graph_clave'
      AND object_id = OBJECT_ID(N'dbo.configuracion_mail_graph')
)
BEGIN
    CREATE UNIQUE INDEX UX_config_mail_graph_clave
    ON dbo.configuracion_mail_graph(clave_configuracion);
END;
GO

SELECT
    id_config_mail,
    clave_configuracion,
    activo,
    send_mail_user,
    alertas_destinatarios_default,
    client_secret_origen,
    usuario_actualizacion,
    fecha_creacion,
    fecha_actualizacion
FROM dbo.configuracion_mail_graph
ORDER BY id_config_mail;
GO
