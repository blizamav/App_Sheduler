/*
    Diagnostico Fase 15F - configuracion_mail_graph unica

    Objetivo:
    - Revisar si existen multiples filas en dbo.configuracion_mail_graph.
    - Identificar la fila candidata a conservar.
    - Dejar una propuesta segura de normalizacion, SIN ejecutarla automaticamente.

    Reglas:
    - La seccion DIAGNOSTICO es solo lectura.
    - La seccion PROPUESTA contiene UPDATE/DELETE y NO debe ejecutarse sin autorizacion explicita.
    - No guarda ni muestra GRAPH_CLIENT_SECRET.
*/

USE APP_SCHEDULER_QA;
GO

/* ==================================================
   DIAGNOSTICO SOLO LECTURA
   ================================================== */

SELECT
    COUNT(*) AS total_filas,
    SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) AS total_activas,
    MIN(id_config_mail) AS primer_id,
    MAX(id_config_mail) AS ultimo_id
FROM dbo.configuracion_mail_graph;
GO

SELECT
    id_config_mail,
    activo,
    tenant_id,
    client_id,
    graph_scope,
    send_mail_user,
    save_to_sent_items,
    alertas_destinatarios_default,
    client_secret_origen,
    fecha_creacion,
    fecha_actualizacion,
    usuario_actualizacion
FROM dbo.configuracion_mail_graph
ORDER BY id_config_mail DESC;
GO

SELECT TOP 1
    id_config_mail AS id_config_mail_recomendado_conservar,
    activo,
    graph_scope,
    send_mail_user,
    fecha_creacion,
    fecha_actualizacion,
    usuario_actualizacion
FROM dbo.configuracion_mail_graph
ORDER BY
    COALESCE(fecha_actualizacion, fecha_creacion) DESC,
    id_config_mail DESC;
GO

/* ==================================================
   PROPUESTA SEGURA - NO EJECUTAR SIN AUTORIZACION
   ==================================================

   Criterio propuesto:
   1. Conservar la fila mas reciente por fecha_actualizacion/fecha_creacion/id.
   2. Eliminar filas duplicadas restantes solo con aprobacion explicita.
   3. Agregar clave global unica MAIL_GRAPH si la columna no existe.
   4. Crear indice unico para impedir mas de una configuracion global.

BEGIN TRAN;

DECLARE @id_conservar int;

SELECT TOP 1 @id_conservar = id_config_mail
FROM dbo.configuracion_mail_graph
ORDER BY
    COALESCE(fecha_actualizacion, fecha_creacion) DESC,
    id_config_mail DESC;

SELECT @id_conservar AS id_config_mail_a_conservar;

-- Revisar antes de borrar.
SELECT *
FROM dbo.configuracion_mail_graph
WHERE id_config_mail <> @id_conservar
ORDER BY id_config_mail DESC;

-- NO ejecutar sin autorizacion explicita.
DELETE FROM dbo.configuracion_mail_graph
WHERE id_config_mail <> @id_conservar;

IF COL_LENGTH('dbo.configuracion_mail_graph', 'clave_configuracion') IS NULL
BEGIN
    ALTER TABLE dbo.configuracion_mail_graph
    ADD clave_configuracion nvarchar(30) NOT NULL
        CONSTRAINT DF_config_mail_graph_clave DEFAULT N'MAIL_GRAPH';
END;

UPDATE dbo.configuracion_mail_graph
SET clave_configuracion = N'MAIL_GRAPH'
WHERE id_config_mail = @id_conservar;

IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_config_mail_graph_clave'
      AND parent_object_id = OBJECT_ID(N'dbo.configuracion_mail_graph')
)
BEGIN
    ALTER TABLE dbo.configuracion_mail_graph WITH CHECK
    ADD CONSTRAINT CK_config_mail_graph_clave
    CHECK (clave_configuracion = N'MAIL_GRAPH');
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_config_mail_graph_clave'
      AND object_id = OBJECT_ID(N'dbo.configuracion_mail_graph')
)
BEGIN
    CREATE UNIQUE INDEX UX_config_mail_graph_clave
    ON dbo.configuracion_mail_graph(clave_configuracion);
END;

SELECT *
FROM dbo.configuracion_mail_graph;

-- Mantener ROLLBACK mientras se revisa. Cambiar a COMMIT solo con aprobacion.
ROLLBACK;
-- COMMIT;

*/
