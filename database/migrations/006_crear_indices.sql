/*
Fase 3B - APP Scheduler
Script: 006_crear_indices.sql
Objetivo: crear indices y alteraciones finales.
Nota: la FK scripts.id_version_activa se agrega aqui por dependencia circular
entre scripts y scripts_versiones.
*/

USE APP_SCHEDULER_QA;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_usuarios_activo' AND object_id = OBJECT_ID(N'dbo.usuarios'))
    CREATE INDEX IX_usuarios_activo ON dbo.usuarios(activo);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_roles_permisos_permiso' AND object_id = OBJECT_ID(N'dbo.roles_permisos'))
    CREATE INDEX IX_roles_permisos_permiso ON dbo.roles_permisos(id_permiso);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_clientes_activo' AND object_id = OBJECT_ID(N'dbo.clientes'))
    CREATE INDEX IX_clientes_activo ON dbo.clientes(activo);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tareas_estado' AND object_id = OBJECT_ID(N'dbo.tareas'))
    CREATE INDEX IX_tareas_estado ON dbo.tareas(estado_tarea, activo);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tareas_cliente_categoria_tipo' AND object_id = OBJECT_ID(N'dbo.tareas'))
    CREATE INDEX IX_tareas_cliente_categoria_tipo ON dbo.tareas(id_cliente, id_categoria, id_tipo);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_tareas_proxima_ejecucion' AND object_id = OBJECT_ID(N'dbo.tareas'))
    CREATE INDEX IX_tareas_proxima_ejecucion ON dbo.tareas(proxima_ejecucion) WHERE activo = 1;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_programaciones_tarea_activo' AND object_id = OBJECT_ID(N'dbo.programaciones'))
    CREATE INDEX IX_programaciones_tarea_activo ON dbo.programaciones(id_tarea, activo);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_version_activa' AND object_id = OBJECT_ID(N'dbo.scripts'))
    CREATE INDEX IX_scripts_version_activa ON dbo.scripts(id_version_activa);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_scripts_versiones_script_activa' AND object_id = OBJECT_ID(N'dbo.scripts_versiones'))
BEGIN
    CREATE UNIQUE INDEX UX_scripts_versiones_script_activa
    ON dbo.scripts_versiones(id_script)
    WHERE es_activa = 1;
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_versiones_script_estado' AND object_id = OBJECT_ID(N'dbo.scripts_versiones'))
    CREATE INDEX IX_scripts_versiones_script_estado ON dbo.scripts_versiones(id_script, estado_version);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_scripts_versiones_hash' AND object_id = OBJECT_ID(N'dbo.scripts_versiones'))
    CREATE INDEX IX_scripts_versiones_hash ON dbo.scripts_versiones(hash_archivo);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ejecuciones_tarea_fecha' AND object_id = OBJECT_ID(N'dbo.ejecuciones'))
    CREATE INDEX IX_ejecuciones_tarea_fecha ON dbo.ejecuciones(id_tarea, fecha_hora_inicio DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ejecuciones_script_version' AND object_id = OBJECT_ID(N'dbo.ejecuciones'))
    CREATE INDEX IX_ejecuciones_script_version ON dbo.ejecuciones(id_script, id_version);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ejecuciones_estado' AND object_id = OBJECT_ID(N'dbo.ejecuciones'))
    CREATE INDEX IX_ejecuciones_estado ON dbo.ejecuciones(estado_ejecucion);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_logs_tareas_ejecucion' AND object_id = OBJECT_ID(N'dbo.logs_tareas'))
    CREATE INDEX IX_logs_tareas_ejecucion ON dbo.logs_tareas(id_ejecucion);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_logs_tareas_tarea_fecha' AND object_id = OBJECT_ID(N'dbo.logs_tareas'))
    CREATE INDEX IX_logs_tareas_tarea_fecha ON dbo.logs_tareas(id_tarea, fecha_creacion DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_logs_sistema_fecha' AND object_id = OBJECT_ID(N'dbo.logs_sistema'))
    CREATE INDEX IX_logs_sistema_fecha ON dbo.logs_sistema(fecha_hora DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_logs_sistema_usuario' AND object_id = OBJECT_ID(N'dbo.logs_sistema'))
    CREATE INDEX IX_logs_sistema_usuario ON dbo.logs_sistema(usuario);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_auditoria_tabla_registro' AND object_id = OBJECT_ID(N'dbo.auditoria_cambios'))
    CREATE INDEX IX_auditoria_tabla_registro ON dbo.auditoria_cambios(tabla_afectada, id_registro);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_auditoria_usuario_fecha' AND object_id = OBJECT_ID(N'dbo.auditoria_cambios'))
    CREATE INDEX IX_auditoria_usuario_fecha ON dbo.auditoria_cambios(usuario, fecha_hora DESC);
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = N'FK_scripts_version_activa'
      AND parent_object_id = OBJECT_ID(N'dbo.scripts')
)
BEGIN
    ALTER TABLE dbo.scripts
    ADD CONSTRAINT FK_scripts_version_activa
    FOREIGN KEY (id_version_activa) REFERENCES dbo.scripts_versiones(id_version);
END;
GO
