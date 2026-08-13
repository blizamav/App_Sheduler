/*
    Limpieza in-place del modelo APP Scheduler.
    Debe ejecutarse dentro de la transaccion abierta por 000_reset_in_place.sql.
    Solo elimina las 33 tablas conocidas; no elimina objetos desconocidos.
*/

USE [$(DB_NAME)];
GO

DECLARE @tablas_app TABLE (nombre sysname PRIMARY KEY);
INSERT INTO @tablas_app (nombre)
VALUES
    (N'cat_estados_tarea'), (N'cat_estados_ejecucion'), (N'cat_tipos_programacion'),
    (N'cat_niveles_log'), (N'cat_tipos_tarea'), (N'cat_estados_version_script'),
    (N'usuarios'), (N'roles'), (N'permisos'), (N'usuarios_roles'), (N'roles_permisos'),
    (N'clientes'), (N'categorias'), (N'tipos'), (N'tareas'), (N'programaciones'),
    (N'scripts'), (N'scripts_versiones'), (N'configuracion_sistema'), (N'ejecuciones'),
    (N'logs_tareas'), (N'logs_sistema'), (N'auditoria_cambios'),
    (N'configuracion_scheduler'), (N'scheduler_worker_heartbeat'), (N'scheduler_eventos'),
    (N'feriados'), (N'reglas_feriados_irrenunciables'),
    (N'notificaciones_config_tarea'), (N'notificaciones_destinatarios'),
    (N'evidencias_ejecucion'), (N'notificaciones_envios'), (N'configuracion_mail_graph');

IF EXISTS (
    SELECT 1
    FROM sys.tables t
    INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
    WHERE s.name = N'dbo'
      AND NOT EXISTS (SELECT 1 FROM @tablas_app a WHERE a.nombre = t.name)
)
BEGIN
    THROW 51000, N'La base contiene tablas dbo desconocidas; el reset in-place se cancela sin eliminarlas.', 1;
END;

IF EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables tp ON tp.object_id = fk.parent_object_id
    INNER JOIN sys.schemas sp ON sp.schema_id = tp.schema_id
    INNER JOIN sys.tables tr ON tr.object_id = fk.referenced_object_id
    INNER JOIN sys.schemas sr ON sr.schema_id = tr.schema_id
    WHERE (
        sp.name = N'dbo'
        AND EXISTS (SELECT 1 FROM @tablas_app a WHERE a.nombre = tp.name)
        AND NOT (sr.name = N'dbo' AND EXISTS (SELECT 1 FROM @tablas_app a WHERE a.nombre = tr.name))
    ) OR (
        sr.name = N'dbo'
        AND EXISTS (SELECT 1 FROM @tablas_app a WHERE a.nombre = tr.name)
        AND NOT (sp.name = N'dbo' AND EXISTS (SELECT 1 FROM @tablas_app a WHERE a.nombre = tp.name))
    )
)
BEGIN
    THROW 51000, N'Existe una dependencia FK desconocida sobre el modelo APP Scheduler.', 1;
END;

DECLARE @sql nvarchar(max) = N'';
SELECT @sql = @sql
    + N'ALTER TABLE ' + QUOTENAME(sp.name) + N'.' + QUOTENAME(tp.name)
    + N' DROP CONSTRAINT ' + QUOTENAME(fk.name) + N';' + CHAR(10)
FROM sys.foreign_keys fk
INNER JOIN sys.tables tp ON tp.object_id = fk.parent_object_id
INNER JOIN sys.schemas sp ON sp.schema_id = tp.schema_id
INNER JOIN sys.tables tr ON tr.object_id = fk.referenced_object_id
INNER JOIN sys.schemas sr ON sr.schema_id = tr.schema_id
WHERE sp.name = N'dbo'
  AND sr.name = N'dbo'
  AND EXISTS (SELECT 1 FROM @tablas_app a WHERE a.nombre = tp.name)
  AND EXISTS (SELECT 1 FROM @tablas_app a WHERE a.nombre = tr.name);

IF @sql <> N'' EXEC sys.sp_executesql @sql;

DROP TABLE IF EXISTS dbo.notificaciones_envios;
DROP TABLE IF EXISTS dbo.evidencias_ejecucion;
DROP TABLE IF EXISTS dbo.notificaciones_destinatarios;
DROP TABLE IF EXISTS dbo.notificaciones_config_tarea;
DROP TABLE IF EXISTS dbo.logs_tareas;
DROP TABLE IF EXISTS dbo.ejecuciones;
DROP TABLE IF EXISTS dbo.scripts_versiones;
DROP TABLE IF EXISTS dbo.scripts;
DROP TABLE IF EXISTS dbo.programaciones;
DROP TABLE IF EXISTS dbo.tareas;
DROP TABLE IF EXISTS dbo.usuarios_roles;
DROP TABLE IF EXISTS dbo.roles_permisos;
DROP TABLE IF EXISTS dbo.usuarios;
DROP TABLE IF EXISTS dbo.roles;
DROP TABLE IF EXISTS dbo.permisos;
DROP TABLE IF EXISTS dbo.clientes;
DROP TABLE IF EXISTS dbo.categorias;
DROP TABLE IF EXISTS dbo.tipos;
DROP TABLE IF EXISTS dbo.logs_sistema;
DROP TABLE IF EXISTS dbo.auditoria_cambios;
DROP TABLE IF EXISTS dbo.scheduler_eventos;
DROP TABLE IF EXISTS dbo.scheduler_worker_heartbeat;
DROP TABLE IF EXISTS dbo.configuracion_scheduler;
DROP TABLE IF EXISTS dbo.configuracion_mail_graph;
DROP TABLE IF EXISTS dbo.configuracion_sistema;
DROP TABLE IF EXISTS dbo.feriados;
DROP TABLE IF EXISTS dbo.reglas_feriados_irrenunciables;
DROP TABLE IF EXISTS dbo.cat_estados_tarea;
DROP TABLE IF EXISTS dbo.cat_estados_ejecucion;
DROP TABLE IF EXISTS dbo.cat_tipos_programacion;
DROP TABLE IF EXISTS dbo.cat_niveles_log;
DROP TABLE IF EXISTS dbo.cat_tipos_tarea;
DROP TABLE IF EXISTS dbo.cat_estados_version_script;
GO

IF EXISTS (
    SELECT 1
    FROM sys.tables t
    INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
    WHERE s.name = N'dbo'
      AND t.name IN (
          N'cat_estados_tarea', N'cat_estados_ejecucion', N'cat_tipos_programacion',
          N'cat_niveles_log', N'cat_tipos_tarea', N'cat_estados_version_script',
          N'usuarios', N'roles', N'permisos', N'usuarios_roles', N'roles_permisos',
          N'clientes', N'categorias', N'tipos', N'tareas', N'programaciones',
          N'scripts', N'scripts_versiones', N'configuracion_sistema', N'ejecuciones',
          N'logs_tareas', N'logs_sistema', N'auditoria_cambios', N'configuracion_scheduler',
          N'scheduler_worker_heartbeat', N'scheduler_eventos', N'feriados',
          N'reglas_feriados_irrenunciables', N'notificaciones_config_tarea',
          N'notificaciones_destinatarios', N'evidencias_ejecucion',
          N'notificaciones_envios', N'configuracion_mail_graph'
      )
)
BEGIN
    THROW 51000, N'No fue posible retirar completamente el modelo APP Scheduler.', 1;
END;
GO
