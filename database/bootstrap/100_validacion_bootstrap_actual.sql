/* Validacion complementaria del bootstrap actual. Solo ejecuta SELECT y THROW. */

USE [$(DB_NAME)];
GO

SET NOCOUNT ON;

DECLARE @errores TABLE (
    categoria nvarchar(50) NOT NULL,
    detalle nvarchar(400) NOT NULL
);

DECLARE @tablas_esperadas TABLE (nombre sysname PRIMARY KEY);
INSERT INTO @tablas_esperadas (nombre)
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

INSERT INTO @errores (categoria, detalle)
SELECT N'TABLA_FALTANTE', e.nombre
FROM @tablas_esperadas e
WHERE OBJECT_ID(N'dbo.' + e.nombre, N'U') IS NULL;

IF (SELECT COUNT(*) FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id WHERE s.name = N'dbo') <> 33
    INSERT INTO @errores VALUES (N'TABLAS', N'La base debe contener exactamente 33 tablas dbo.');

IF (SELECT COUNT(*) FROM sys.columns c INNER JOIN sys.tables t ON t.object_id = c.object_id INNER JOIN sys.schemas s ON s.schema_id = t.schema_id WHERE s.name = N'dbo') <> 456
    INSERT INTO @errores VALUES (N'METADATA', N'La base debe contener exactamente 456 columnas dbo.');

IF (SELECT COUNT(*) FROM sys.foreign_keys WHERE is_ms_shipped = 0) <> 25
    INSERT INTO @errores VALUES (N'METADATA', N'La base debe contener exactamente 25 claves foraneas.');

IF (SELECT COUNT(*) FROM sys.check_constraints WHERE is_ms_shipped = 0) <> 38
    INSERT INTO @errores VALUES (N'METADATA', N'La base debe contener exactamente 38 restricciones CHECK.');

IF (SELECT COUNT(*) FROM sys.default_constraints) <> 117
    INSERT INTO @errores VALUES (N'METADATA', N'La base debe contener exactamente 117 restricciones DEFAULT.');

IF (SELECT COUNT(*) FROM sys.indexes i INNER JOIN sys.tables t ON t.object_id = i.object_id WHERE i.index_id > 0 AND t.is_ms_shipped = 0) <> 119
    INSERT INTO @errores VALUES (N'METADATA', N'La base debe contener exactamente 119 indices, incluyendo PK y UNIQUE.');

DECLARE @columnas_esperadas TABLE (tabla sysname PRIMARY KEY, cantidad int NOT NULL);
INSERT INTO @columnas_esperadas VALUES
    (N'notificaciones_config_tarea', 13),
    (N'notificaciones_destinatarios', 8),
    (N'evidencias_ejecucion', 16),
    (N'notificaciones_envios', 18),
    (N'configuracion_mail_graph', 13);

INSERT INTO @errores (categoria, detalle)
SELECT N'COLUMNAS', CONCAT(e.tabla, N': se esperaban ', e.cantidad, N' columnas.')
FROM @columnas_esperadas e
WHERE (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = OBJECT_ID(N'dbo.' + e.tabla)) <> e.cantidad;

DECLARE @objetos_esperados TABLE (nombre sysname PRIMARY KEY);
INSERT INTO @objetos_esperados (nombre)
VALUES
    (N'PK_notificaciones_config_tarea'), (N'FK_notif_config_tareas'), (N'CK_notif_config_plantilla'),
    (N'UX_notif_config_tarea_activa'), (N'IX_notif_config_tarea_activo'), (N'IX_notif_config_enviar_evidencia'),
    (N'PK_notificaciones_destinatarios'), (N'FK_notif_dest_config'), (N'CK_notif_dest_tipo'),
    (N'CK_notif_dest_canal'), (N'CK_notif_dest_email_basico'), (N'UX_notif_dest_activo'),
    (N'IX_notif_dest_config_tipo_activo'), (N'PK_evidencias_ejecucion'), (N'FK_evidencias_ejecuciones'),
    (N'UX_evidencias_ejecucion'), (N'CK_evidencias_estado'), (N'CK_evidencias_cantidades'),
    (N'IX_evidencias_estado_fecha'), (N'PK_notificaciones_envios'), (N'FK_notif_envios_ejecuciones'),
    (N'FK_notif_envios_evidencias'), (N'FK_notif_envios_origen'), (N'CK_notif_envios_tipo'),
    (N'CK_notif_envios_estado'), (N'CK_notif_envios_intento'), (N'CK_notif_envios_graph_status'),
    (N'IX_notif_envios_ejecucion_fecha'), (N'IX_notif_envios_evidencia_fecha'),
    (N'IX_notif_envios_tipo_estado_fecha'), (N'IX_notif_envios_origen'),
    (N'UX_notif_envio_exitoso_cliente'), (N'PK_configuracion_mail_graph'),
    (N'CK_config_mail_graph_clave'), (N'CK_config_mail_graph_secret_origen'),
    (N'CK_config_mail_graph_scope'), (N'CK_config_mail_graph_send_mail_user'),
    (N'UX_config_mail_graph_unica_activa'), (N'UX_config_mail_graph_clave'),
    (N'IX_config_mail_graph_actualizacion');

INSERT INTO @errores (categoria, detalle)
SELECT N'OBJETO_FALTANTE', e.nombre
FROM @objetos_esperados e
WHERE NOT EXISTS (SELECT 1 FROM sys.objects o WHERE o.name = e.nombre)
  AND NOT EXISTS (SELECT 1 FROM sys.indexes i WHERE i.name = e.nombre);

IF (SELECT COUNT(*) FROM dbo.roles WHERE activo = 1) <> 4
   OR EXISTS (SELECT 1 FROM dbo.roles WHERE codigo_rol NOT IN (N'SUPER_ADMIN', N'ADMIN', N'TI', N'TERCERO'))
    INSERT INTO @errores VALUES (N'ROLES', N'Deben existir solo los cuatro roles base activos.');

IF (SELECT COUNT(*) FROM dbo.permisos WHERE activo = 1) <> 52
    INSERT INTO @errores VALUES (N'PERMISOS', N'Deben existir exactamente 52 permisos base activos.');

IF NOT EXISTS (SELECT 1 FROM dbo.permisos WHERE codigo_permiso = N'FACTORY_RESET_EJECUTAR' AND activo = 1)
    INSERT INTO @errores VALUES (N'PERMISOS', N'Falta el permiso FACTORY_RESET_EJECUTAR.');

IF EXISTS (
    SELECT 1
    FROM dbo.roles_permisos rp
    INNER JOIN dbo.roles r ON r.id_rol = rp.id_rol
    INNER JOIN dbo.permisos p ON p.id_permiso = rp.id_permiso
    WHERE p.codigo_permiso = N'FACTORY_RESET_EJECUTAR'
      AND rp.activo = 1 AND rp.permitido = 1
      AND r.codigo_rol <> N'SUPER_ADMIN'
)
    INSERT INTO @errores VALUES (N'PERMISOS', N'FACTORY_RESET_EJECUTAR solo puede pertenecer a SUPER_ADMIN.');

DECLARE @matriz_roles TABLE (codigo_rol varchar(50) PRIMARY KEY, cantidad int NOT NULL);
INSERT INTO @matriz_roles VALUES (N'SUPER_ADMIN', 52), (N'ADMIN', 49), (N'TI', 34), (N'TERCERO', 7);

INSERT INTO @errores (categoria, detalle)
SELECT N'ROLES_PERMISOS', CONCAT(m.codigo_rol, N': matriz de permisos incompleta.')
FROM @matriz_roles m
WHERE (
    SELECT COUNT(*)
    FROM dbo.roles_permisos rp
    INNER JOIN dbo.roles r ON r.id_rol = rp.id_rol
    WHERE r.codigo_rol = m.codigo_rol AND rp.activo = 1 AND rp.permitido = 1
) <> m.cantidad;

DECLARE @catalogos_esperados TABLE (tabla sysname NOT NULL, codigo varchar(60) NOT NULL, PRIMARY KEY (tabla, codigo));
INSERT INTO @catalogos_esperados VALUES
    (N'cat_estados_tarea', N'ACTIVA'), (N'cat_estados_tarea', N'ELIMINADA'),
    (N'cat_estados_tarea', N'INACTIVA'), (N'cat_estados_tarea', N'SUSPENDIDA'),
    (N'cat_estados_ejecucion', N'CANCELADA'), (N'cat_estados_ejecucion', N'DETENIDA_MANUALMENTE'),
    (N'cat_estados_ejecucion', N'EN_EJECUCION'), (N'cat_estados_ejecucion', N'ERROR'),
    (N'cat_estados_ejecucion', N'EXITOSA'),
    (N'cat_estados_ejecucion', N'PENDIENTE'),
    (N'cat_tipos_programacion', N'DIARIA'), (N'cat_tipos_programacion', N'FECHA_ESPECIFICA'),
    (N'cat_tipos_programacion', N'FECHAS_ESPECIFICAS'),
    (N'cat_tipos_programacion', N'MANUAL'), (N'cat_tipos_programacion', N'MENSUAL'),
    (N'cat_tipos_programacion', N'SEMANAL'),
    (N'cat_niveles_log', N'CRITICAL'), (N'cat_niveles_log', N'DEBUG'),
    (N'cat_niveles_log', N'ERROR'),
    (N'cat_niveles_log', N'INFO'), (N'cat_niveles_log', N'WARNING'),
    (N'cat_tipos_tarea', N'MANUAL'), (N'cat_tipos_tarea', N'PROGRAMADA'),
    (N'cat_estados_version_script', N'ACTIVA'), (N'cat_estados_version_script', N'DISPONIBLE'),
    (N'cat_estados_version_script', N'INACTIVA'), (N'cat_estados_version_script', N'REEMPLAZADA');

INSERT INTO @errores (categoria, detalle)
SELECT N'CATALOGO', CONCAT(c.tabla, N'.', c.codigo, N' no existe activo.')
FROM @catalogos_esperados c
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.cat_estados_tarea x WHERE c.tabla = N'cat_estados_tarea' AND x.codigo = c.codigo AND x.activo = 1
    UNION ALL SELECT 1 FROM dbo.cat_estados_ejecucion x WHERE c.tabla = N'cat_estados_ejecucion' AND x.codigo = c.codigo AND x.activo = 1
    UNION ALL SELECT 1 FROM dbo.cat_tipos_programacion x WHERE c.tabla = N'cat_tipos_programacion' AND x.codigo = c.codigo AND x.activo = 1
    UNION ALL SELECT 1 FROM dbo.cat_niveles_log x WHERE c.tabla = N'cat_niveles_log' AND x.codigo = c.codigo AND x.activo = 1
    UNION ALL SELECT 1 FROM dbo.cat_tipos_tarea x WHERE c.tabla = N'cat_tipos_tarea' AND x.codigo = c.codigo AND x.activo = 1
    UNION ALL SELECT 1 FROM dbo.cat_estados_version_script x WHERE c.tabla = N'cat_estados_version_script' AND x.codigo = c.codigo AND x.activo = 1
);

IF (SELECT COUNT(*) FROM dbo.reglas_feriados_irrenunciables WHERE activo = 1 AND pais = N'CL') <> 5
    INSERT INTO @errores VALUES (N'FERIADOS', N'Deben existir cinco reglas base activas para Chile.');

IF (SELECT COUNT(*) FROM dbo.configuracion_mail_graph WHERE clave_configuracion = N'MAIL_GRAPH') <> 1
    INSERT INTO @errores VALUES (N'MAIL_GRAPH', N'Debe existir exactamente una configuracion MAIL_GRAPH.');

IF (SELECT COUNT(*) FROM dbo.configuracion_sistema WHERE clave = N'BOOTSTRAP_SQL' AND valor = N'19C.0' AND activo = 1) <> 1
    INSERT INTO @errores VALUES (N'BOOTSTRAP', N'No existe la marca de version BOOTSTRAP_SQL 19C.0.');

IF EXISTS (
    SELECT 1 FROM dbo.configuracion_mail_graph
    WHERE activo <> 0 OR tenant_id IS NOT NULL OR client_id IS NOT NULL
       OR send_mail_user IS NOT NULL OR alertas_destinatarios_default IS NOT NULL
       OR client_secret_origen <> N'ENV'
)
    INSERT INTO @errores VALUES (N'MAIL_GRAPH', N'La configuracion inicial no es segura o contiene datos de ambiente.');

IF (SELECT COUNT(*) FROM dbo.configuracion_scheduler WHERE activo = 1 AND scheduler_activo = 0
    AND permitir_ejecucion_automatica = 0 AND intervalo_revision_segundos = 60
    AND max_ejecuciones_concurrentes = 3 AND modo_mantenimiento = 0) <> 1
    INSERT INTO @errores VALUES (N'SCHEDULER', N'La configuracion inicial del scheduler no coincide con los defaults seguros.');

IF EXISTS (
    SELECT 1 FROM (
        SELECT COUNT(*) total FROM dbo.usuarios UNION ALL
        SELECT COUNT(*) FROM dbo.usuarios_roles UNION ALL
        SELECT COUNT(*) FROM dbo.clientes UNION ALL
        SELECT COUNT(*) FROM dbo.categorias UNION ALL
        SELECT COUNT(*) FROM dbo.tipos UNION ALL
        SELECT COUNT(*) FROM dbo.tareas UNION ALL
        SELECT COUNT(*) FROM dbo.programaciones UNION ALL
        SELECT COUNT(*) FROM dbo.scripts UNION ALL
        SELECT COUNT(*) FROM dbo.scripts_versiones UNION ALL
        SELECT COUNT(*) FROM dbo.ejecuciones UNION ALL
        SELECT COUNT(*) FROM dbo.logs_tareas UNION ALL
        SELECT COUNT(*) FROM dbo.logs_sistema UNION ALL
        SELECT COUNT(*) FROM dbo.auditoria_cambios UNION ALL
        SELECT COUNT(*) FROM dbo.scheduler_worker_heartbeat UNION ALL
        SELECT COUNT(*) FROM dbo.scheduler_eventos UNION ALL
        SELECT COUNT(*) FROM dbo.feriados UNION ALL
        SELECT COUNT(*) FROM dbo.notificaciones_config_tarea UNION ALL
        SELECT COUNT(*) FROM dbo.notificaciones_destinatarios UNION ALL
        SELECT COUNT(*) FROM dbo.evidencias_ejecucion UNION ALL
        SELECT COUNT(*) FROM dbo.notificaciones_envios
    ) datos_operativos
    WHERE total <> 0
)
    INSERT INTO @errores VALUES (N'ESTADO_VIRGEN', N'Una o mas tablas operativas contienen datos.');

SELECT categoria, detalle FROM @errores ORDER BY categoria, detalle;

IF EXISTS (SELECT 1 FROM @errores)
BEGIN
    ;THROW 51000, N'Bootstrap actual invalido. Revisar el resultado de validacion.', 1;
END;

SELECT
    N'BOOTSTRAP_ACTUAL' AS validacion,
    N'OK' AS resultado,
    DB_NAME() AS base_validada,
    (SELECT COUNT(*) FROM sys.tables t INNER JOIN sys.schemas s ON s.schema_id = t.schema_id WHERE s.name = N'dbo') AS tablas_dbo;
GO
